from fastapi import FastAPI, Query, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import aiosqlite
import json
import re
import time
import jdatetime

app = FastAPI(
    title="سامانه جامع آزمون‌یاب (API اپلیکیشن)",
    description="API اختصاصی برای ارتباط اپلیکیشن فلاتر با دیتابیس و منطق هوشمند آزمون‌ها",
    version="2.0.0"
)

APP_DB = 'recruitment.db' # استفاده از همان دیتابیس مشترک ربات

# ================= مدل‌های داده (Pydantic Models) برای ورودی‌های اپلیکیشن =================
class DegreeItem(BaseModel):
    degree: str
    major: str

class RegisterModel(BaseModel):
    user_id: int # شناسه یکتا برای کاربر در اپلیکیشن (یا شماره موبایل به عنوان شناسه)
    name: str
    phone: str
    b_year: int
    b_month: int
    b_day: int
    is_married: int # 0 یا 1
    children_count: int
    degrees: List[DegreeItem]

# ================= توابع محاسباتی و هوشمند (دقیقاً مشابه ربات) =================
def calculate_exact_age_details(b_year, b_month, b_day):
    today = jdatetime.date.today()
    try: birth = jdatetime.date(int(b_year), int(b_month), int(b_day))
    except: return 0, 0, 0
    years = today.year - birth.year
    months = today.month - birth.month
    days = today.day - birth.day
    if days < 0:
        months -= 1; days += 30 
    if months < 0:
        years -= 1; months += 12
    return years, months, days

def calculate_age_at_exam(b_year, b_month, b_day, exam_date_str):
    try:
        ey, em, ed = map(int, exam_date_str.split('/'))
        age = ey - b_year
        if (em < b_month) or (em == b_month and ed < b_day): age -= 1
        return age
    except: return 0

def normalize_text(text, keep_dash=False):
    if not text: return ""
    text = text.replace("آ", "ا").replace("أ", "ا").replace("إ", "ا")
    text = text.replace("ي", "ی").replace("ك", "ک").replace("گرایش", " ")
    text = text.replace('\u200b', ' ').replace('\u200c', ' ').replace('\u200d', ' ')
    text = text.replace("(", " ").replace(")", " ").replace("،", " ")
    text = re.sub(r'[@#$*&^%_=+`~|\\}{\[\]:;"\'><?,./¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿×÷]', ' ', text)
    if not keep_dash:
        text = text.replace("-", " ")
    return " ".join(text.split()).lower()

def clean_major_name(text):
    if not text: return ""
    forbidden_words = [
        'کارشناسی ارشد', 'دکتری تخصصی', 'فوق لیسانس', 'فوق دیپلم',
        'کارشناسی', 'کاردانی', 'لیسانس', 'ارشد', 'دکتری', 'دیپلم'
    ]
    clean_text = text
    for word in forbidden_words:
        clean_text = clean_text.replace(word, " ")
    return " ".join(clean_text.split())

def check_match_logic(excel_major, user_major):
    cleaned_user_major = clean_major_name(user_major)
    norm_excel = normalize_text(excel_major, keep_dash=True)
    norm_user = normalize_text(cleaned_user_major, keep_dash=False)
    
    if "زبان انگلیسی" in norm_excel and any(w in norm_excel for w in ["همه", "کلیه", "تمامی", "گرایش"]):
        if "زبان انگلیسی" in norm_user and any(w in norm_user for w in ["مترجمی", "اموزش", "ادبیات"]):
            return True

    global_wildcards = ["همه رشته ها", "کلیه رشته ها", "تمامی رشته ها", "همه", "کلیه", "تمام رشته ها"]
    if norm_excel in global_wildcards:
        return True

    is_matched = False
    if "-" in norm_excel:
        parts = norm_excel.split("-")
        base_major = parts[0].strip()
        sub_major = parts[1].strip() if len(parts) > 1 else ""
        wildcards = ["همه", "کلیه", "تمامی", "بدون اولویت", "تمام"]
        is_wild = any(w in sub_major for w in wildcards)
        
        if is_wild:
            if norm_user == base_major or norm_user.startswith(base_major + " "): 
                is_matched = True
        else:
            exact_expected_major = f"{base_major} {sub_major}".strip()
            if norm_user == exact_expected_major: 
                is_matched = True
    else:
        if norm_excel == norm_user: 
            is_matched = True
            
    if is_matched:
        return True
        
    no_space_excel = norm_excel.replace(" ", "")
    no_space_user = norm_user.replace(" ", "")
    
    if "-" in norm_excel: 
        parts = norm_excel.split("-")
        base_major_no_space = parts[0].strip().replace(" ", "")
        sub_major = parts[1].strip() if len(parts) > 1 else ""
        wildcards = ["همه", "کلیه", "تمامی", "بدون اولویت", "تمام"]
        is_wild = any(w in sub_major for w in wildcards)
        
        if is_wild:
            if no_space_user == base_major_no_space or no_space_user.startswith(base_major_no_space): 
                return True
        else:
            sub_major_no_space = sub_major.replace(" ", "")
            exact_expected_major = f"{base_major_no_space}{sub_major_no_space}"
            if no_space_user == exact_expected_major: 
                return True
    else:
        if no_space_excel == no_space_user: 
            return True
            
    return False

def check_eligibility(user_degree, user_major, exam_req_json):
    try:
        data = json.loads(exam_req_json)
        items = data.get('items', [])
        user_deg_norm = normalize_text(user_degree)
        
        for item in items:
            req_deg = normalize_text(item['degree'])
            if req_deg == 'همه' or req_deg == user_deg_norm:
                for mapping in item.get('mappings', []):
                    if check_match_logic(mapping['major'], user_major):
                        return True
        return False
    except:
        return False

def get_matched_jobs_for_user(user_degree, user_major, exam_req_json):
    try:
        data = json.loads(exam_req_json)
        items = data.get('items', [])
        found_jobs = []
        user_deg_norm = normalize_text(user_degree)
        
        for item in items:
            req_deg = normalize_text(item['degree'])
            if req_deg == 'همه' or req_deg == user_deg_norm:
                for mapping in item.get('mappings', []):
                    if check_match_logic(mapping['major'], user_major):
                        raw_jobs = mapping['jobs']
                        if raw_jobs:
                            found_jobs.append(raw_jobs)
        return list(set(found_jobs))
    except:
        return []

# ================= اندپوینت‌های API =================

@app.get("/", summary="وضعیت سرور", tags=["عمومی"])
def read_root():
    return {"status": "API Server is running successfully!"}

@post_reg_endpoint := app.post("/register", summary="ثبت‌نام یا ویرایش اطلاعات کاربر (چند مدرکی)", tags=["کاربران"])
async def register_user(data: RegisterModel):
    async with aiosqlite.connect(APP_DB, timeout=30) as conn:
        # بررسی قفل ویرایش
        async with conn.execute("SELECT lock_until, edit_count, penalty_level FROM users WHERE user_id=?", (data.user_id,)) as c:
            row = await c.fetchone()
            
        is_editing = row is not None
        lock_until = row[0] if row else 0
        e_count = row[1] if row else 0
        p_level = row[2] if row else 0
        
        now = int(time.time())
        if is_editing and now < lock_until:
            diff = lock_until - now
            time_str = "فردا" if diff < 86400 else ("یک هفته دیگر" if diff < 86400 * 8 else "یک ماه دیگر")
            raise HTTPException(status_code=400, detail=f"امکان ویرایش اطلاعات تا {time_str} مسدود شده است.")

        if is_editing:
            e_count += 1
            if p_level == 0 and e_count >= 3:
                lock_until = now + (24 * 3600); p_level = 1; e_count = 0
            elif p_level == 1 and e_count >= 1:
                lock_until = now + (7 * 24 * 3600); p_level = 2; e_count = 0
            elif p_level >= 2 and e_count >= 1:
                lock_until = now + (30 * 24 * 3600); p_level = 3; e_count = 0

        last_deg = data.degrees[-1].degree if data.degrees else ""
        last_maj = normalize_text(data.degrees[-1].major) if data.degrees else ""

        # ذخیره جدول اصلی کاربران
        await conn.execute('''INSERT OR REPLACE INTO users 
            (user_id, name, phone, b_year, b_month, b_day, is_married, children_count, degree, major, edit_count, penalty_level, lock_until) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (data.user_id, normalize_text(data.name), data.phone, data.b_year, data.b_month, data.b_day, 
             data.is_married, data.children_count, last_deg, last_maj, e_count, p_level, lock_until))

        # ذخیره مدارک جانبی در جدول user_degrees
        await conn.execute("DELETE FROM user_degrees WHERE user_id=?", (data.user_id,))
        for deg_item in data.degrees:
            await conn.execute("INSERT INTO user_degrees (user_id, degree, major) VALUES (?, ?, ?)", 
                               (data.user_id, deg_item.degree, normalize_text(deg_item.major)))
        
        # ثبت در اکتیو سشن جهت آمار کاربران آنلاین
        await conn.execute("INSERT OR REPLACE INTO active_sessions (user_id, last_seen) VALUES (?, ?)", (data.user_id, now))
        await conn.commit()

    return {"status": "success", "message": "اطلاعات کاربر با موفقیت ثبت شد."}

@app.get("/profile/{user_id}", summary="دریافت اطلاعات پروفایل و مدارک کاربر", tags=["کاربران"])
async def get_profile(user_id: int):
    async with aiosqlite.connect(APP_DB, timeout=30) as conn:
        async with conn.execute("SELECT name, phone, b_year, b_month, b_day, is_married, children_count FROM users WHERE user_id=?", (user_id,)) as c:
            u = await c.fetchone()
        async with conn.execute("SELECT degree, major FROM user_degrees WHERE user_id=?", (user_id,)) as c:
            u_degrees = await c.fetchall()

    if not u:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد. لطفاً ثبت‌نام کنید.")

    y, m, d = calculate_exact_age_details(u[2], u[3], u[4])
    return {
        "name": u[0],
        "phone": u[1],
        "age_years": y,
        "age_months": m,
        "age_days": d,
        "is_married": bool(u[5]),
        "children_count": u[6],
        "degrees": [{"degree": d[0], "major": d[1]} for d in u_degrees]
    }

@app.get("/exams/active", summary="لیست آزمون‌های فعال و در حال ثبت‌نام", tags=["آزمون‌ها"])
async def get_active_exams():
    today = jdatetime.datetime.now().strftime("%Y/%m/%d")
    async with aiosqlite.connect(APP_DB, timeout=30) as conn:
        async with conn.execute("SELECT id, name, exam_date, reg_start, reg_end, description FROM exams") as c:
            exams = await c.fetchall()

    active_list = []
    for ex in exams:
        if ex[4] >= today: # اگر تاریخ پایان ثبت‌نام نگذشته باشد
            active_list.append({
                "id": ex[0],
                "name": ex[1],
                "exam_date": ex[2],
                "reg_start": ex[3],
                "reg_end": ex[4],
                "description": ex[5]
            })
    return active_list

@app.get("/exams/upcoming", summary="لیست آزمون‌های پیش رو", tags=["آزمون‌ها"])
async def get_upcoming_exams():
    async with aiosqlite.connect(APP_DB, timeout=30) as conn:
        async with conn.execute("SELECT id, name, description FROM upcoming_exams ORDER BY id DESC") as c:
            exams = await c.fetchall()
            
    return [{"id": ex[0], "name": ex[1], "description": ex[2]} for ex in exams]

@app.get("/user/matched-jobs/{user_id}", summary="جستجوی هوشمند مشاغل مجاز برای کاربر", tags=["تطبیق هوشمند"])
async def get_user_matched_jobs(user_id: int):
    async with aiosqlite.connect(APP_DB, timeout=30) as conn:
        async with conn.execute("SELECT b_year, b_month, b_day, is_married, children_count FROM users WHERE user_id=?", (user_id,)) as c:
            u_data = await c.fetchone()
        async with conn.execute("SELECT degree, major FROM user_degrees WHERE user_id=?", (user_id,)) as c:
            u_degrees = await c.fetchall()
        async with conn.execute("SELECT id, name, exam_date, reg_end, min_age, max_age, major_req FROM exams ORDER BY exam_date DESC") as c:
            exams = await c.fetchall()

    if not u_data or not u_degrees:
        raise HTTPException(status_code=404, detail="پروفایل کاربر یا مدارک تحصیلی یافت نشد.")

    b_year, b_month, b_day, is_married, children_count = u_data
    base_bonus = min((1 if is_married else 0) + children_count, 5)
    today = jdatetime.datetime.now().strftime("%Y/%m/%d")

    active_results = []
    past_results = []

    for exam in exams:
        exam_id, exam_name, exam_date, reg_end, global_min, global_max, major_req = exam
        age_at_exam = calculate_age_at_exam(b_year, b_month, b_day, exam_date)
        
        try:
            req_data = json.loads(major_req)
            items = req_data.get('items', [])
            has_bonus = req_data.get('has_bonus', True)
        except:
            items = []
            has_bonus = True

        bonus = base_bonus if has_bonus else 0
        eff_age = age_at_exam - bonus

        exam_degree_blocks = []
        for u_degree, u_major in u_degrees:
            u_deg_norm = normalize_text(u_degree)
            specific_min, specific_max = global_min, global_max
            for item in items:
                req_deg = normalize_text(item.get('degree', ''))
                if req_deg == 'همه' or req_deg == u_deg_norm:
                    specific_min = item.get('min_age', global_min)
                    specific_max = item.get('max_age', global_max)
                    break
            
            if specific_min <= eff_age <= specific_max:
                matched_jobs = get_matched_jobs_for_user(u_degree, u_major, major_req)
                if matched_jobs:
                    exam_degree_blocks.append({
                        "degree": u_degree,
                        "major": clean_major_name(u_major),
                        "jobs": list(set(matched_jobs))
                    })

        if exam_degree_blocks:
            exam_info = {
                "exam_id": exam_id,
                "exam_name": exam_name,
                "exam_date": exam_date,
                "matched_degrees": exam_degree_blocks
            }
            if reg_end >= today:
                active_results.append(exam_info)
            else:
                past_results.append(exam_info)

    return {
        "active_exams": active_results,
        "past_exams": past_results
    }