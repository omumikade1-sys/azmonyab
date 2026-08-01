import os
import io
import json
import asyncio
import time
import openpyxl
import re
# ================= 🛠 ترفند ۱: پاک کردن تنظیمات مخفی ویندوز =================
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

import nest_asyncio
nest_asyncio.apply()

import sqlite3
import aiosqlite 
import jdatetime
import re
import html
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler, CallbackQueryHandler, TypeHandler
)
from telegram.request import HTTPXRequest
from telegram.error import RetryAfter, Forbidden

# ================= تنظیمات اصلی =================
TOKEN = '8425776110:AAHgpz-q15t5XW8_d0pJMgfxhZYBIYcUkXk'
ADMIN_IDS = [1870990328, 775322201 ,1771649818] # آیدی‌های ادمین‌ها
BOT_USERNAME = 'Azmonyab_bot'
CHANNEL_ID = '@OMUMI_KADE' # آیدی کانال اول برای ادد اجباری
CHANNEL_ID_2 = '@mosahebe6' # آیدی کانال دوم برای ادد اجباری

BACK_BTN = "بازگشت به منو اصلی"
ADMIN_BACK_BTN = "🔙 بازگشت به پنل مدیریت"

(NAME, PHONE, B_YEAR, B_MONTH, B_DAY, MARITAL_STATUS, CHILDREN_COUNT, DEGREE, DEGREE_SUB, MAJOR, ASK_MORE_DEGREES) = range(11)
EXAM_EXCEL_UPLOAD, EXAM_CONFIRM_FINAL = range(11, 13)
ADMIN_BROADCAST_MSG = 13
ADMIN_SET_TUTORIAL_MSG = 14
UPCOMING_NAME, UPCOMING_DESC, UPCOMING_VOICE = range(20, 23)
ADMIN_USER_EXCEL_UPLOAD = 24
ADMIN_UPLOAD_EXAM_PDF = 25
ADMIN_UPLOAD_EXAM_BOOKLET = 26 
ADMIN_SEARCH_DEGREE, ADMIN_SEARCH_MAJOR = range(30, 32)
WAIT_FOR_VIDEO = 15
# ================= دیتابیس =================
def init_db():
    conn = sqlite3.connect('recruitment.db')
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  name TEXT, phone TEXT, 
                  b_year INTEGER, b_month INTEGER, b_day INTEGER, 
                  is_married INTEGER, children_count INTEGER,
                  degree TEXT, major TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_degrees
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  degree TEXT,
                  major TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS exams
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT, exam_date TEXT,
                  reg_start TEXT, reg_end TEXT, 
                  min_age INTEGER, max_age INTEGER,
                  degree_req TEXT, major_req TEXT, description TEXT,
                  analysis_type TEXT DEFAULT NULL,
                  analysis_content TEXT DEFAULT NULL,
                  pdf_file_id TEXT DEFAULT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS upcoming_exams
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT, description TEXT, voice_file_id TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS active_sessions
                 (user_id INTEGER PRIMARY KEY, last_seen INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tutorials
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, content TEXT, caption TEXT)''')
                 
    conn.commit()
    conn.close()

def upgrade_db():
    conn = sqlite3.connect('recruitment.db')
    c = conn.cursor()
    # اضافه کردن امن ستون‌های جدید برای کاربران
    for col in ['edit_count', 'penalty_level', 'lock_until']:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
            
    # اضافه کردن ستون فایل دفترچه به جدول آزمون‌ها
    try:
        c.execute("ALTER TABLE exams ADD COLUMN booklet_file_id TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
        
    # 🟢 اضافه کردن ستون دسته‌بندی برای آموزش‌ها
    try:
        c.execute("ALTER TABLE tutorials ADD COLUMN category TEXT DEFAULT 'general'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

async def check_user_exists(user_id):
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)) as c:
            exists = await c.fetchone()
    return True if exists else False

async def is_member(user_id: int, bot) -> bool:
    try:
        member1 = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        status1 = str(member1.status).lower()
        member2 = await bot.get_chat_member(chat_id=CHANNEL_ID_2, user_id=user_id)
        status2 = str(member2.status).lower()
        
        print(f"🟢 [DEBUG] User {user_id} status in ch1: {status1}, in ch2: {status2}")
        is_mem1 = status1 in ['member', 'administrator', 'creator', 'owner']
        is_mem2 = status2 in ['member', 'administrator', 'creator', 'owner']
        return is_mem1 and is_mem2
    except Exception as e:
        print(f"🔴 [DEBUG] Membership Check Error for {user_id}: {e}")
        return False

async def track_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return
    now_ts = int(time.time())
    try:
        async with aiosqlite.connect('recruitment.db', timeout=5) as conn:
            await conn.execute("INSERT OR REPLACE INTO active_sessions (user_id, last_seen) VALUES (?, ?)", (user.id, now_ts))
            await conn.commit()
    except:
        pass

# ================= توابع محاسباتی و هوشمند =================
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

def get_days_remaining(exam_date_str):
    try:
        y, m, d = map(int, exam_date_str.split('/'))
        return (jdatetime.date(y, m, d) - jdatetime.date.today()).days
    except: return 0

def normalize_text(text, keep_dash=False):
    if not text: return ""
    # یکسان‌سازی انواع الف (آ، أ، إ) به ا ساده
    text = text.replace("آ", "ا").replace("أ", "ا").replace("إ", "ا")
    text = text.replace("ي", "ی").replace("ك", "ک").replace("گرایش", " ")
    text = text.replace('\u200b', ' ').replace('\u200c', ' ').replace('\u200d', ' ')
    text = text.replace("(", " ").replace(")", " ").replace("،", " ")
    
    # حذف تمام کاراکترهای غیرمتعارف و خاص
    text = re.sub(r'[@#$*&^%_=+`~|\\}{\[\]:;"\'><?,./¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿×÷]', ' ', text)
    
    if not keep_dash:
        text = text.replace("-", " ")
    return " ".join(text.split()).lower()

def clean_major_name(text):
    if not text: return ""
    # 🟢 لیست کلمات ممنوعه (به ترتیب از طولانی به کوتاه چیده شده تا تداخل ایجاد نکند)
    forbidden_words = [
        'کارشناسی ارشد', 'دکتری تخصصی', 'فوق لیسانس', 'فوق دیپلم',
        'کارشناسی', 'کاردانی', 'لیسانس', 'ارشد', 'دکتری', 'دیپلم'
    ]
    clean_text = text
    for word in forbidden_words:
        clean_text = clean_text.replace(word, " ")
    # پاک کردن فاصله‌های اضافی ایجاد شده
    return " ".join(clean_text.split())


def check_match_logic(excel_major, user_major):
    # 🟢 ۱. فیلتر کردن کلمات اضافه (مثل لیسانس، ارشد) از رشته کاربر
    cleaned_user_major = clean_major_name(user_major)
    
    norm_excel = normalize_text(excel_major, keep_dash=True)
    norm_user = normalize_text(cleaned_user_major, keep_dash=False)
    
    # 🛑 تبصره اختصاصی برای استثنای رشته‌های زبان انگلیسی
    if "زبان انگلیسی" in norm_excel and any(w in norm_excel for w in ["همه", "کلیه", "تمامی", "گرایش"]):
        if "زبان انگلیسی" in norm_user and any(w in norm_user for w in ["مترجمی", "اموزش", "ادبیات"]):
            return True

    global_wildcards = ["همه رشته ها", "کلیه رشته ها", "تمامی رشته ها", "همه", "کلیه", "تمام رشته ها"]
    if norm_excel in global_wildcards:
        return True

    # ==========================================
    # 🟢 مرحله اول: بررسی دقیق (با حفظ فاصله‌ها)
    # ==========================================
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
        
    # ==========================================
    # 🟢 مرحله دوم: اغماض و بررسی بدون فاصله
    # ==========================================
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
    except Exception as e:
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
    except Exception as e:
        return []

def format_majors_display_v2(req_json):
    try:
        data = json.loads(req_json)
        items = data.get('items', [])
        ordered_majors = []
        
        for item in items:
            for mapping in item.get('mappings', []):
                m = mapping.get('major', '').strip()
                if m and m not in ordered_majors: 
                    ordered_majors.append(m)
                    
        has_more = False
        display_text = ""
        if len(ordered_majors) > 10:
            display_text = "🔹 " + "، ".join(ordered_majors[:10]) + " ..."
            has_more = True
        elif len(ordered_majors) > 0:
            display_text = "🔹 " + "، ".join(ordered_majors)
        else:
            display_text = "🔹 (رشته‌ای ثبت نشده)"
        return display_text, has_more
    except Exception:
        return "خطا در پردازش لیست رشته‌ها", False

# ================= کیبوردها =================
def get_back_kb(placeholder_text="در حال تایپ..."):
    return ReplyKeyboardMarkup([[BACK_BTN]], resize_keyboard=True, selective=True, input_field_placeholder=placeholder_text)

async def get_main_reply_keyboard(user_id):
    is_registered = await check_user_exists(user_id)
    profile_btn = '👤 پروفایل کاربری' if is_registered else '📝 ثبت نام'
    
    keyboard = [
        [profile_btn, '🎬 آموزش کار با ربات'],
        ['🟢 آزمون های در حال ثبت نام'],
        ['🎯 آزمون های مناسب رشته من'],
      ['📅 آزمون های پیش رو'],
        ['🎧 ارتباط با پشتیبانی']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن آزمون (Excel)", callback_data='admin_add_exam'),
         InlineKeyboardButton("🗑 حذف آزمون", callback_data='admin_list_delete_exam')],
        [InlineKeyboardButton("📎 ارسال فایل / دفترچه", callback_data='admin_files_menu'),
         InlineKeyboardButton("➕ افزودن آزمون پیش رو", callback_data='admin_add_upcoming')],
        [InlineKeyboardButton("🗑 حذف آزمون پیش رو", callback_data='admin_list_delete_upcoming'),
         InlineKeyboardButton("✏️ ویرایش کاربران (Excel)", callback_data='admin_edit_users_excel')],
        [InlineKeyboardButton("🟢 کاربران آنلاین", callback_data='admin_online_users'),
         InlineKeyboardButton("📊 آمار و خروجی کاربران", callback_data='admin_stats_menu')],
        [InlineKeyboardButton("📣 ارسال پیام همگانی", callback_data='admin_broadcast_start'),
         InlineKeyboardButton("🎬 مدیریت آموزش ربات", callback_data='admin_tutorial_menu')],
        [InlineKeyboardButton("🔍 جستجوی رشته و مقطع", callback_data='admin_search_start')],
        # 👇 این دکمه جدید را اینجا اضافه کن 👇
        [InlineKeyboardButton("📤 یادآوری ثبت‌نام (به ثبت‌نام نکرده‌ها)", callback_data='admin_remind_unreg')],
        [InlineKeyboardButton("❌ بستن پنل", callback_data='close_panel')]
    ])
def get_admin_back_kb():
    return ReplyKeyboardMarkup([[KeyboardButton(ADMIN_BACK_BTN)]], resize_keyboard=True, one_time_keyboard=True)

# ================= توابع نمایش اطلاعات کاربری و آزمون =================
async def check_user_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT b_year, b_month, b_day, is_married, children_count FROM users WHERE user_id=?", (user_id,)) as c:
            u_data = await c.fetchone()
        async with conn.execute("SELECT degree, major FROM user_degrees WHERE user_id=?", (user_id,)) as c:
            u_degrees = await c.fetchall()
        async with conn.execute("SELECT id, name, exam_date, reg_end, min_age, max_age, major_req FROM exams ORDER BY exam_date DESC") as c:
            exams = await c.fetchall()
            
    if not exams:
        await update.message.reply_text("❌ هنوز هیچ آزمونی در سیستم ثبت نشده است.")
        return

    b_year, b_month, b_day, is_married, children_count = u_data[0], u_data[1], u_data[2], u_data[3], u_data[4]
    bonus = min((1 if is_married else 0) + children_count, 5)
    today = jdatetime.datetime.now().strftime("%Y/%m/%d")
    
    active_msgs = ""
    past_msgs = ""

    for exam in exams:
        exam_id, exam_name, exam_date, reg_end, global_min, global_max, major_req = exam
        
        booklet_link = f"<a href='https://t.me/{BOT_USERNAME}?start=booklet_{exam_id}'>📥 دانلود دفترچه این آزمون</a>"
        
        age_at_exam = calculate_age_at_exam(b_year, b_month, b_day, exam_date)
        
        exam_degree_blocks = []
        try:
            req_data = json.loads(major_req)
            items = req_data.get('items', [])
            has_bonus = req_data.get('has_bonus', True) # 🟢 گرفتن شرط جوانی
        except:
            items = []
            has_bonus = True
            
        # 🟢 اعمال ارفاق سنی فقط در صورت داشتن امتیاز جوانی
        bonus = min((1 if is_married else 0) + children_count, 5) if has_bonus else 0
        eff_age = age_at_exam - bonus
        
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
                    jobs_list_str = "\n".join([f"      ▫️ {j}" for j in set(matched_jobs)])
                    
                    # 🟢 اعمال فیلتر نمایشی برای پنهان کردن کلمات ممنوعه
                    clean_maj = clean_major_name(u_major) 
                    
                    # استفاده از تگ b به جای ستاره
                    block = f"   🎓 با مدرک <b>{u_degree} {clean_maj}</b> در جایگاه های شغلی زیر میتونستین شرکت کنین:\n{jobs_list_str}"
                    exam_degree_blocks.append(block)
            
        if exam_degree_blocks:
            all_blocks_str = "\n\n".join(exam_degree_blocks)
            if reg_end >= today:
                active_msgs += f"🎯 ✨ {exam_name} ✨\n{booklet_link}\n📅 تاریخ برگزاری: {exam_date}\n{all_blocks_str}\n\n" 
            else:
                past_msgs += f"🏛 ✨ {exam_name} ✨\n{booklet_link}\n📅 تاریخ برگزاری: {exam_date}\n{all_blocks_str}\n\n"

    degrees_lines = []
    for idx, md in enumerate(u_degrees):
        # 🟢 اعمال فیلتر نمایشی برای لیست مدارک ثبت شده
        clean_maj = clean_major_name(md[1]) 
        degrees_lines.append(f"▫️ مدرک {idx + 1}: {md[0]} {clean_maj}")
    majors_display = "\n".join(degrees_lines)

    # استفاده از ایموجی به جای ** برای تیترها
    final_msg = f"🔍 ✨ نتیجه جستجوی هوشمند مشاغل برای شما ✨\n\n🎓 🌟 مدارک ثبت‌شده شما:\n{majors_display}\n➖➖➖➖➖➖➖➖\n\n"

    if active_msgs:
        final_msg += f"🟢 🌟 فرصت‌های فعال (مجاز به ثبت‌نام هستید):\n\n{active_msgs}"
    else:
        final_msg += "🔴 🌟 فرصت‌های فعال: در حال حاضر آزمون فعالی برای رشته شما وجود ندارد.\n\n"

    if past_msgs:
        final_msg += f"➖➖➖➖➖➖➖➖\n📚 🌟 تاریخچه آزمون‌های گذشته:\n(آزمون‌هایی که در دوره‌های قبل مدارک شما را پذیرفته‌اند)\n\n{past_msgs}"
        final_msg += "💡 <i>این بخش به شما کمک می‌کند بدانید رشته شما معمولاً در کدام ارگان‌ها تقاضا دارد تا برای دوره‌های بعدی آماده باشید.</i>"

    if active_msgs or past_msgs:
        final_msg += "\n\n📚 <b>اگه منابع این آزمون رو میخوای پیام بده به ادمین :</b>\nایدی ادمین :\n@omumikade_admin"
        
    if not active_msgs and not past_msgs:
        final_msg = (
            f"❌ <b>عدم تطابق با هیچ آزمونی</b>\n\n"
            f"دوست عزیز، متاسفانه در دیتابیس ما (چه آزمون‌های فعال و چه آزمون‌های سال‌های قبل)، رشته شما در دفترچه برای هیچ شغلی تعریف نشده است.\n\n"
            f"✅ اما آزمون یاب الان روشنه و به محض انتشار آزمون جدید فورا به شما اطلاع میدیم!"
        )

    # تغییر پارس مُد به HTML برای رفع قطعی ارور
    await update.message.reply_text(final_msg, parse_mode='HTML', disable_web_page_preview=True)
    

async def show_exam_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, exam_id: int):
    user_id = update.effective_user.id
    RLM = "\u200f"
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT * FROM exams WHERE id=?", (exam_id,)) as c:
            exam = await c.fetchone()
        async with conn.execute("SELECT b_year, b_month, b_day, is_married, children_count FROM users WHERE user_id=?", (user_id,)) as c:
            u = await c.fetchone()
        async with conn.execute("SELECT degree, major FROM user_degrees WHERE user_id=?", (user_id,)) as c:
            u_degrees = await c.fetchall()

    if not exam:
        await context.bot.send_message(user_id, "❌ آزمون مورد نظر یافت نشد.")
        return

    majors_display, has_more = format_majors_display_v2(exam[8])

    status_msg = ""
    if u and u_degrees:
        age_at_exam = calculate_age_at_exam(u[0], u[1], u[2], exam[2])
        base_bonus = min((1 if u[3] else 0) + u[4], 5)
        
        valid_degrees = []
        age_reasons = []
        
        try:
            req_data = json.loads(exam[8])
            items = req_data.get('items', [])
            has_bonus = req_data.get('has_bonus', True)
        except:
            items = []
            has_bonus = True

        # 🟢 اعمال هوشمند امتیاز جوانی برای این آزمون
        bonus = base_bonus if has_bonus else 0
        eff_age = age_at_exam - bonus
        
        is_major_ok_general = False
        
        for ud_deg, ud_maj in u_degrees:
            if check_eligibility(ud_deg, ud_maj, exam[8]):
                is_major_ok_general = True
                u_deg_norm = normalize_text(ud_deg)
                
                # استخراج سن اختصاصی مدرک
                specific_min, specific_max = exam[5], exam[6]
                for item in items:
                    req_deg = normalize_text(item.get('degree', ''))
                    if req_deg == 'همه' or req_deg == u_deg_norm:
                        specific_min = item.get('min_age', exam[5])
                        specific_max = item.get('max_age', exam[6])
                        break
                        
                if specific_min <= eff_age <= specific_max:
                    clean_maj = clean_major_name(ud_maj) # 🟢 اعمال فیلتر نمایشی
                    valid_degrees.append(f"{ud_deg} {clean_maj}")
                else:
                    age_reasons.append(f"سن شما ({eff_age} سال) با شرایط سنی مقطع {ud_deg} مطابقت ندارد (مجاز: {specific_min} تا {specific_max} سال).")
                    
        is_completely_valid = len(valid_degrees) > 0
        
        if is_completely_valid:
            degrees_str = "، ".join(valid_degrees)
            status_msg = f"{RLM}✅ <b>وضعیت شما:</b> با توجه به شرایط شما، <b>مجاز به شرکت در این آزمون هستید (با مدرک: {degrees_str}).</b>\n\n📚 <b>اگه منابع این آزمون رو میخوای پیام بده به ادمین :</b>\nایدی ادمین :\n@omumikade_admin"
        else:
            reasons = []
            if not is_major_ok_general:
                reasons.append("هیچ‌کدام از رشته‌های تحصیلی شما در لیست رشته‌های این آزمون نیست")
            else:
                reasons.extend(age_reasons)
                
            reasons_str = f"\n{RLM}".join([f"🔸 {r}" for r in reasons])
            status_msg = f"{RLM}❌ <b>وضعیت شما:</b> متاسفانه به دلایل زیر <b>مجاز به شرکت نیستید:</b>\n{RLM}{reasons_str}"
    else:
        status_msg = f"{RLM}ℹ️ <b>وضعیت شما:</b> برای بررسی شرایط، ابتدا <b>ثبت‌نام کنید.</b>"

    divider = f"{RLM}➖➖➖➖➖➖➖➖➖➖"
    caption = (
        f"{RLM}📢 <b>{exam[1]}</b>\n"
        f"{divider}\n\n"
        
        f"{RLM}📅 <b>تقویم استخدامی:</b>\n"
        f"{RLM}▫️ برگزاری آزمون: {exam[2]}\n"
        f"{RLM}▫️ مهلت ثبت‌نام: {exam[3]} تا {exam[4]}\n\n"
        
        f"{divider}\n\n"
        
        f"{RLM}👤 <b>شرط اختصاصی:</b>\n"
        f"{RLM}🔹 بازه سنی: {exam[5]} تا {exam[6]} سال\n"
        f"{RLM}🎓 <b>رشته‌های مورد نیاز:</b>\n"
        f"{RLM}<code>{majors_display.replace('🔹 ', '')}</code>\n\n"
        
        f"{status_msg}\n\n"
        
        f"{divider}\n\n"
        
        f"{RLM}📝 <b>توضیحات تکمیلی:</b>\n"
        f"{RLM}{exam[9] if exam[9] else 'توضیحاتی ثبت نشده است.'}\n\n"
        
        f"{RLM}🆔 @{BOT_USERNAME}"
    )

    keyboard = []
    
    # 🟢 دکمه "مشاهده تمام رشته‌ها" حالا همیشه و بدون هیچ شرطی نمایش داده میشه
    keyboard.append([InlineKeyboardButton(f"{RLM}📚 مشاهده تمام رشته‌های مورد نیاز", callback_data=f"show_full_majors_{exam_id}")])

    # دکمه دوم بر اساس اینکه کاربر ثبت نام کرده یا نه نمایش داده میشه
    if u: 
        keyboard.append([InlineKeyboardButton(f"{RLM}💼 مشاهده شغل‌های مجاز من", callback_data=f"show_my_jobs_{exam_id}")])
    else: 
        keyboard.append([InlineKeyboardButton(f"{RLM}🔍 ثبت‌نام و بررسی شرایط", callback_data=f"pre_register_confirm")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try: await update.callback_query.message.reply_text(caption, parse_mode='HTML', reply_markup=reply_markup)
        except: pass
    else:
        await update.message.reply_text(caption, parse_mode='HTML', reply_markup=reply_markup)
        
async def show_full_majors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    
    exam_id = int(query.data.split("_")[3])

    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT name, pdf_file_id FROM exams WHERE id=?", (exam_id,)) as c:
            res = await c.fetchone()

    if not res:
        await query.answer("آزمون یافت نشد.", show_alert=True)
        return

    exam_name = res[0]
    pdf_file_id = res[1]

    if pdf_file_id:
        await context.bot.send_document(
            chat_id=chat_id,
            document=pdf_file_id,
            caption=f"📎 فایل لیست رشته‌های مورد نیاز آزمون: 📋 {exam_name} 📌"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ مدیریت هنوز فایل PDF رشته‌های این آزمون را آپلود نکرده است."
        )

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT name, phone, b_year, b_month, b_day, is_married, children_count FROM users WHERE user_id=?", (user_id,)) as c:
            u = await c.fetchone()
        async with conn.execute("SELECT degree, major FROM user_degrees WHERE user_id=?", (user_id,)) as c:
            u_degrees = await c.fetchall()

    if not u: return

    y, m, d = calculate_exact_age_details(u[2], u[3], u[4])
    is_married = u[5] == 1
    kids = u[6]
    bonus = (1 if is_married else 0) + kids
    if bonus > 5: bonus = 5
    
    marital_display = "متاهل 💍" if u[5] else "مجرد 👤"
    radar_status = "✅ فعال (رایگان و دائمی)"

    bonus_msg = ""
    kids_line = ""
    if is_married:
        if bonus > 0:
            bonus_msg = f"با توجه به امتیاز جوانی جمعیت (شرایط تاهل و {kids} فرزند)  {bonus} سال به سقف سنی شما اضافه میشود\n\n"
        kids_line = f"👶 فرزند: {kids}\n"

    degrees_display = ""
    if len(u_degrees) <= 1:
        deg_text = u_degrees[0][0] if u_degrees else "(ثبت نشده)"
        maj_text = u_degrees[0][1] if u_degrees else "(ثبت نشده)"
        # 🟢 اعمال فیلتر برای نمایش خالص رشته
        clean_maj = clean_major_name(maj_text)
        degrees_display = f"🎓 مدرک: {deg_text}\n📚 رشته: {html.escape(clean_maj)}"
    else:
        num_map = ["اول", "دوم", "سوم", "چهارم", "پنجم", "ششم", "هفتم", "هشتم", "نهم", "دهم"]
        deg_lines = []
        for idx, (deg, maj) in enumerate(u_degrees):
            num_word = num_map[idx] if idx < len(num_map) else str(idx + 1)
            # 🟢 اعمال فیلتر برای نمایش خالص رشته
            clean_maj = clean_major_name(maj)
            deg_lines.append(f"🎓 مدرک {num_word}: {deg} {html.escape(clean_maj)}")
        degrees_display = "\n".join(deg_lines)

    profile_msg = (
        f"👤 پروفایل کاربری شما\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"📛 نام: {html.escape(u[0])}\n"
        f"📱 موبایل: {u[1]}\n\n"
        f"🎂 سن: {y} سال و {m} ماه و {d} روز\n\n"
        f"{bonus_msg}"
        f"💍 وضعیت: {marital_display}\n"
        f"{kids_line}"
        f"\n{degrees_display}\n"
        f"\nآزمون یاب: {radar_status}"
    )
    
    kb = [
        [InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data='edit_profile')]
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(profile_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(profile_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        
async def show_active_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT id, name, reg_end FROM exams") as c:
            exams = await c.fetchall()

    today = jdatetime.datetime.now().strftime("%Y/%m/%d")
    keyboard = []

    for exam in exams:
        exam_id, exam_name, reg_end = exam
        if reg_end >= today:
            keyboard.append([InlineKeyboardButton(f"🎯 {exam_name}", callback_data=f"view_exam_{exam_id}")])

    if keyboard:
        msg = "📅 **آزمون‌های فعال:**\n\n👇 برای مشاهده جزئیات روی آزمون مورد نظر کلیک کنید:"
    else:
        msg = "🔴 در حال حاضر هیچ آزمون فعالی برای ثبت‌نام وجود ندارد."

    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    else:
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def show_upcoming_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT id, name FROM upcoming_exams ORDER BY id DESC") as c:
            exams = await c.fetchall()
    keyboard = []
    for exam in exams:
        keyboard.append([InlineKeyboardButton(exam[1], callback_data=f"view_upcoming_{exam[0]}")])
    
    msg = "📅 **آزمون‌های پیش رو:**\n\n👇 برای مشاهده جزئیات روی آزمون مورد نظر کلیک کنید:"
    if not keyboard:
        msg = "🔴 در حال حاضر هیچ آزمون پیش رویی ثبت نشده است."
        
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    else:
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def show_delete_exam_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT id, name FROM exams ORDER BY id DESC") as c:
            exams = await c.fetchall()

    if not exams:
        await query.answer("❌ هیچ آزمونی برای حذف وجود ندارد.", show_alert=True)
        await query.message.edit_text("🕴 به پنل مدیریت خوش آمدید:", reply_markup=get_admin_panel_keyboard())
        return

    keyboard = []
    for ex in exams:
        keyboard.append([InlineKeyboardButton(f"🗑 {ex[1]}", callback_data=f"do_delete_exam_{ex[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_admin_main')])

    await query.message.edit_text("👇 آزمون مورد نظر برای حذف را انتخاب کنید:\n(این عمل غیرقابل بازگشت است)", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= هندلرهای اصلی یوزر =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 🟢 بخش جدید: بررسی دیپ‌لینک برای دانلود مستقیم دفترچه
    text = update.message.text
    if text and text.startswith('/start booklet_'):
        try:
            exam_id = int(text.split('_')[1])
            async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
                async with conn.execute("SELECT name, booklet_file_id FROM exams WHERE id=?", (exam_id,)) as c:
                    res = await c.fetchone()
            
            if res:
                ex_name, booklet_id = res
                if booklet_id:
                    await update.message.reply_document(document=booklet_id, caption=f"📥 فایل دفترچه کامل آزمون:\n📋 {ex_name}")
                    return ConversationHandler.END
                else:
                    await update.message.reply_text("❌ مدیریت هنوز دفترچه اصلی این آزمون را در سیستم آپلود نکرده است.")
                    return ConversationHandler.END
            else:
                await update.message.reply_text("❌ آزمون یافت نشد.")
                return ConversationHandler.END
        except Exception:
            pass

    user_exists = await check_user_exists(user_id)
    # بقیه کدهای تابع start این پایین سر جاشون بمونن...
    
    keys_to_clear = ['name', 'phone', 'b_year', 'b_month', 'b_day', 'is_editing', 'temp_degrees']
    for key in keys_to_clear: context.user_data.pop(key, None)

    if user_exists:
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT name FROM users WHERE user_id=?", (user_id,)) as c:
                row = await c.fetchone()
                user_name = row[0] if row else "کاربر"
                
        reply_kb = await get_main_reply_keyboard(user_id)
        await update.message.reply_text(f"سلام {user_name} عزیز 👋\nبه منوی اصلی بازگشتید.", reply_markup=reply_kb)
    else:
        welcome_text = (
            "رفیق، خوش اومدی! 👋 من ربات هوش مصنوعی آزمون‌های استخدامی‌ام! 🤖\n\n"
            "✨ **خدمات من:**\n\n"
            "📡 **آزمون‌یاب:**\n"
            "به محض اینکه دفترچه جدیدی منتشر بشه، من قبل از همه بازش می‌کنم، خط به خطش رو با سن و رشته شما تطبیق میدم و فوری بهت میگم واجد شرایط هستی یا نه!\n\n"
            "🟢 **آزمون های فعال:**\n"
            "آگهی‌های مرتبط با رشته و سن شما رو بررسی می‌کنیم و بهتون میگیم دقیقاً در کدوم موقعیت‌های شغلی مجاز به ثبت نام هستین.\n\n"
            "🎯 **آزمون های مناسب رشته من:**\n"
            "با بررسی مشخصات شما، لیست تمام آزمون‌هایی که شما در گذشته شرایط شرکت در آن را داشته اید به شما نمایش داده میشود\n\n"
            "🚀 آماده‌ای؟ همین الان ثبت‌نام کن 👇"
        )
        btns = [
            [InlineKeyboardButton("✅ بله (ثبت‌نام)", callback_data='pre_register_confirm')]
        ]
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(btns))
    return ConversationHandler.END

async def main_menu_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🟢 ۱. محافظت در برابر آپدیت‌های سیستمی، پیام‌های کانال و مواردی که دیتای کاربر ندارند
    if context.user_data is None or update.message is None:
        return

    # 🟢 ۲. بررسی وضعیت ادمین برای دریافت عکس/متن در پیام همگانی
    if context.user_data.get('admin_state') == 'WAITING_FOR_BC_MSG':
        await receive_broadcast_message(update, context)
        return

    # 🟢 ۳. بررسی متن. اگر کاربر عادی چیزی غیر از متن (مثل عکس) فرستاد، واکنشی نشان ندهد
    text = update.message.text
    if not text:
        return
    
    if text == "📢 ارسال پیام همگانی":
        await start_smart_broadcast(update, context)
        return
    
    user_id = update.effective_user.id
    is_registered = await check_user_exists(user_id)
    
    if text in ['🟢 آزمون های در حال ثبت نام', '📅 آزمون های پیش رو', '🎯 آزمون های مناسب رشته من']:
        if not await is_member(user_id, context.bot):
            kb = [
                [InlineKeyboardButton("📢 عضویت در کانال عمومی کده", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton("📢 عضویت در کانال مصاحبه", url=f"https://t.me/{CHANNEL_ID_2.replace('@', '')}")],
                [InlineKeyboardButton("🔄 بررسی مجدد عضویت", callback_data='check_membership_dynamic')]
            ]
            await update.message.reply_text(
                "❌ **دسترسی محدود شد!**\n\nبرای استفاده از خدمات ربات و دریافت اطلاعات آزمون‌ها، باید همواره در کانال های ما عضو بمانید. لطفاً مجدداً جوین شوید:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(kb)
            )
            return

    if text == '🟢 آزمون های در حال ثبت نام':
        await show_active_exams(update, context)

    elif text == '📅 آزمون های پیش رو':
        await show_upcoming_exams(update, context)
        
    elif text == '🎧 ارتباط با پشتیبانی':
        await update.message.reply_text("جهت ارتباط با پشتیبانی به آیدی زیر پیام دهید:\n@omumikade_admin")

    elif text == '👤 پروفایل کاربری':
        if not is_registered: 
            txt = "⛔️ **شما هنوز ثبت‌نام نکرده‌اید!**\n\nبرای دسترسی به پروفایل و ویرایش اطلاعات، ابتدا باید ثبت‌نام خود را تکمیل کنید."
            kb = [[InlineKeyboardButton("✅ ثبت‌نام (رایگان)", callback_data='pre_register_confirm')]]
            await update.message.reply_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        else: 
            await show_profile(update, context)
        
    elif text == '📝 ثبت نام':
        if not await is_member(user_id, context.bot):
            kb = [
                [InlineKeyboardButton("📢 عضویت در کانال عمومی کده", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton("📢 عضویت در کانال مصاحبه", url=f"https://t.me/{CHANNEL_ID_2.replace('@', '')}")],
                [InlineKeyboardButton("✅ عضو شدم (شروع ثبت‌نام)", callback_data='start_register')]
            ]
            await update.message.reply_text(
                "❌ **دسترسی محدود!**\n\nبرای ثبت‌نام، ابتدا باید در کانال های ما عضو شوید. پس از عضویت، دکمه زیر را بزنید.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(kb)
            )
            return

        txt = (
            "دوست عزیز، برای اینکه بررسی کنیم که شما در آزمون های استخدامی واجد شرایط هستید یا خیر، باید سن و مدرک تحصیلی شما رو بدونیم.\n"
            "آیا مایلید اطلاعات تون رو ثبت کنید ؟"
        )
        kb = [[InlineKeyboardButton("بله", callback_data='start_register')]]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        
    elif text == '🎯 آزمون های مناسب رشته من':
        if not is_registered:
            txt = "⛔️ **شما هنوز ثبت‌نام نکرده‌اید!**\n\nبرای بررسی شرایط خود، ابتدا باید سن و مدرک خود را از طریق دکمه ثبت نام ثبت کنید."
            kb = [[InlineKeyboardButton("✅ ثبت‌نام (رایگان)", callback_data='pre_register_confirm')]]
            await update.message.reply_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        else:
            await check_user_jobs(update, context)
            
    elif text == '🎬 آموزش کار با ربات':
        kb = [
            [InlineKeyboardButton("👤 پروفایل کاربری", callback_data='show_tut_profile')],
            [InlineKeyboardButton("🟢 آزمون های در حال ثبت نام", callback_data='show_tut_active')],
            [InlineKeyboardButton("🎯 آزمون های مناسب رشته من", callback_data='show_tut_matched')],
            [InlineKeyboardButton("📅 آزمون های پیش رو", callback_data='show_tut_upcoming')],
            [InlineKeyboardButton("🏠 منو اصلی", callback_data='back_to_main_menu')]
        ]
        await update.message.reply_text("آموزش کدام بخش از ربات را نیاز دارید؟", reply_markup=InlineKeyboardMarkup(kb))
        
# ================= هندلرهای ادمین =================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in ADMIN_IDS:
        context.user_data.clear()
        await update.message.reply_text("🕴 به پنل مدیریت خوش آمدید:", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END
    
async def close_panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.delete()

async def back_to_admin_panel_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("انصراف از انجام عملیات.", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
    return ConversationHandler.END

async def start_exam_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📊 لطفاً فایل اکسل حاوی اطلاعات آزمون را ارسال کنید.\n\n"
        "⚠️ ستون‌ها باید به ترتیب زیر باشند:\n"
        "نام آزمون | عنوان شغلی | مقطع | رشته‌های مجاز",
        reply_markup=get_admin_back_kb()
    )
    return EXAM_EXCEL_UPLOAD

async def receive_exam_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: 
        return await back_to_admin_panel_msg(update, context)
        
    if not update.message.document:
        await update.message.reply_text("❌ لطفاً فایل را به صورت فایل (document) بفرستید.")
        return EXAM_EXCEL_UPLOAD

    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    
    if not update.message.document.file_name.lower().endswith('.xlsx'):
        await update.message.reply_text("❌ برای این روش حتماً باید فایل فرمت .xlsx داشته باشد (اکسل جدید).")
        return EXAM_EXCEL_UPLOAD

    def safe_int(val, default):
        try: 
            if val is None or str(val).strip() == "": return default
            return int(float(str(val).strip()))
        except: return default

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        
        if 'Info' not in wb.sheetnames or 'Jobs' not in wb.sheetnames:
            await update.message.reply_text("❌ فایل اکسل باید دو شیت به نام‌های Info و Jobs داشته باشد.\n(به حروف بزرگ و کوچک دقت کنید)")
            return EXAM_EXCEL_UPLOAD

        ws_info = wb['Info']
        info_rows = list(ws_info.iter_rows(min_row=2, values_only=True))
        
        if not info_rows or not info_rows[0][0]:
            await update.message.reply_text("❌ شیت Info خالی است.")
            return EXAM_EXCEL_UPLOAD
            
        main_row = info_rows[0]
        exam_name = str(main_row[0]).strip() 
        
        # خواندن وضعیت امتیاز جوانی (ستون F / ایندکس 5)
        has_bonus_str = str(main_row[5]).strip() if len(main_row) > 5 and main_row[5] is not None else ""
        has_bonus = True if has_bonus_str == "دارد" else False

        # 🟢 استخراج هوشمند کمترین سن از ستون H و بیشترین از ستون I
        all_mins = []
        all_maxs = []
        for row in info_rows:
            if len(row) > 7 and row[7] is not None and str(row[7]).strip() != "":
                all_mins.append(safe_int(row[7], 18))
            if len(row) > 8 and row[8] is not None and str(row[8]).strip() != "":
                all_maxs.append(safe_int(row[8], 45))
                
        # پیدا کردن مطلقِ کمترین و بیشترین سن در کل مقاطع
        global_min_age = min(all_mins) if all_mins else 18
        global_max_age = max(all_maxs) if all_maxs else 45
        
        exam_data = {
            'e_name': exam_name,
            'e_date': str(main_row[1]).strip(),
            'e_reg_start': str(main_row[2]).strip(),
            'e_reg_end': str(main_row[3]).strip(),
            'e_min': global_min_age,  
            'e_max': global_max_age,  
            # 🟢 تغییر: استخراج توضیحات آزمون از سلول E2 (ایندکس 4)
            'e_desc': str(main_row[4]).strip() if len(main_row) > 4 and main_row[4] is not None else "",
            'items': [] 
        }

        # ذخیره سن اختصاصی هر مقطع
        age_limits = {}
        for row in info_rows:
            if len(row) > 8 and row[6] is not None and str(row[6]).strip() != "": 
                deg_name = str(row[6]).strip()
                age_limits[deg_name] = {
                    'min': safe_int(row[7], global_min_age),
                    'max': safe_int(row[8], global_max_age)
                }

        ws_jobs = wb['Jobs']
        jobs_rows = list(ws_jobs.iter_rows(min_row=2, values_only=True))
        degree_map = {}

        for row in jobs_rows:
            row_exam_name = str(row[0]).strip() if row[0] else ""
            if row_exam_name == exam_name:
                job_title = str(row[1]).strip() if row[1] else "عنوان کلی"
                degree = str(row[2]).strip() if row[2] else "نامشخص"
                
                majors_raw = str(row[3]).strip() if row[3] else ""
                
                majors_list = [m.strip() for m in re.split(r'[,،]', majors_raw) if m.strip()]
                if not degree in degree_map: degree_map[degree] = []
                for maj in majors_list:
                    degree_map[degree].append({'major': maj, 'jobs': job_title})

        final_items = []
        for deg, mappings in degree_map.items():
            limits = age_limits.get(deg.strip(), {'min': exam_data['e_min'], 'max': exam_data['e_max']})
            final_items.append({
                'degree': deg, 
                'min_age': limits['min'], 
                'max_age': limits['max'], 
                'mappings': mappings
            })

        context.user_data.update(exam_data)
        context.user_data['final_req_json'] = json.dumps({"has_bonus": has_bonus, "items": final_items}, ensure_ascii=False)
        
        display_majors, _ = format_majors_display_v2(context.user_data['final_req_json'])
        msg = (
            "🛑 <b>پیش‌نمایش خبر (استخراج شده از اکسل)</b>\n\n"
            f"🏷 نام: {exam_data['e_name']}\n"
            f"📅 تاریخ برگزاری: {exam_data['e_date']}\n"
            f"⏱ مهلت ثبت‌نام: {exam_data['e_reg_start']} الی {exam_data['e_reg_end']}\n"
            f"🎁 امتیاز جوانی جمعیت: {'دارد ✅' if has_bonus else 'ندارد ❌'}\n"
            f"🎓 رشته‌ها:\n{display_majors}\n"
            f"📝 توضیحات: {exam_data.get('e_desc', 'ندارد')}\n\n"
            "آیا اطلاعات مورد تایید است؟"
        )
        kb = [
            [InlineKeyboardButton("📢 تایید و انتشار عمومی", callback_data='confirm_send')],
            [InlineKeyboardButton("🔕 تایید و ثبت بی‌صدا", callback_data='confirm_send_silent')],
            [InlineKeyboardButton("❌ لغو و حذف", callback_data='cancel_send')]
        ]
        
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        return EXAM_CONFIRM_FINAL

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش فایل: {str(e)}")
        return EXAM_EXCEL_UPLOAD

async def finalize_exam_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_send':
        context.user_data.clear()
        await query.message.edit_text("❌ عملیات لغو شد.", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END

    if query.data in ['confirm_send', 'confirm_send_silent']:
        # یک کپی امن از دیتا می‌گیریم تا موقع پاکسازی از بین نرود
        exam_data = dict(context.user_data) 
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            cursor = await conn.cursor()
            
            # ۱. ذخیره آزمون در دیتابیس
            await cursor.execute('''
                INSERT INTO exams (name, exam_date, reg_start, reg_end, min_age, max_age, degree_req, major_req, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                exam_data['e_name'], exam_data['e_date'], 
                exam_data['e_reg_start'], exam_data['e_reg_end'], 
                exam_data['e_min'], exam_data['e_max'],
                "Excel", exam_data['final_req_json'], exam_data.get('e_desc', '')
            ))
            exam_id = cursor.lastrowid
            
            # ۲. استخراج لیست کاربران
            users_with_degrees = []
            unregistered_users = []
            
            if query.data == 'confirm_send':
                # الف) استخراج کاربران ثبت‌نام شده با مدارک
                await cursor.execute('''
                    SELECT u.user_id, u.b_year, u.b_month, u.b_day, u.is_married, u.children_count,
                           ud.degree, ud.major 
                    FROM users u 
                    INNER JOIN user_degrees ud ON u.user_id = ud.user_id
                ''')
                users_with_degrees = await cursor.fetchall()
                
                # ب) استخراج کاربرانی که فقط استارت زده‌اند (در اکتیو سشن هستند اما در جدول یوزر نیستند)
                await cursor.execute('''
                    SELECT user_id FROM active_sessions WHERE user_id NOT IN (SELECT user_id FROM users)
                ''')
                unregistered_users = await cursor.fetchall()
                
            await conn.commit()

        if query.data == 'confirm_send':
            await query.message.edit_text("✅ آزمون با موفقیت ثبت شد.\nدر حال پردازش و ارسال پیام به تمامی کاربران... ⏳")
            full_date = exam_data['e_date']
            # ۳. فراخوانی تابع برودکست با پارامترهای جدید
            asyncio.create_task(broadcast_exam_safe(context, users_with_degrees, unregistered_users, exam_data, full_date, exam_id))
            
        elif query.data == 'confirm_send_silent':
            # ثبت بدون ارسال پیام برای کاربران
            await query.message.edit_text("✅🔕 آزمون با موفقیت و به‌صورت بی‌صدا در دیتابیس آپدیت شد (هیچ پیامی برای کاربران نرفت).", reply_markup=get_admin_panel_keyboard())

        context.user_data.clear()
        return ConversationHandler.END

async def broadcast_exam_safe(context, users_with_degrees, unregistered_users, exam_data, full_date, exam_id):
    days_left = get_days_remaining(full_date)
    
    # استخراج شرط جوانی جمعیت این آزمون از جیسون
    has_bonus = True
    try:
        req_data = json.loads(exam_data['final_req_json'])
        has_bonus = req_data.get('has_bonus', True)
    except: 
        pass
    
    # -------------------------------------------------------------
    # بخش اول: پردازش و ارسال به کاربران ثبت‌نام شده (چه مجاز، چه غیرمجاز)
    # -------------------------------------------------------------
    user_profiles = {}
    # جمع‌آوری مدارک هر کاربر در یک دیکشنری تا فقط یک پیام به هر نفر برود
    for row in users_with_degrees:
        u_id, b_year, b_month, b_day, is_married, children_count, deg, maj = row
        if u_id not in user_profiles:
            user_profiles[u_id] = {
                'b_year': b_year, 'b_month': b_month, 'b_day': b_day,
                'is_married': is_married, 'children_count': children_count,
                'degrees': []
            }
        user_profiles[u_id]['degrees'].append((deg, maj))
        
    count_registered = 0
    for u_id, profile in user_profiles.items():
        try:
            age = calculate_age_at_exam(profile['b_year'], profile['b_month'], profile['b_day'], full_date)
            base_bonus = min((1 if profile['is_married'] else 0) + profile['children_count'], 5)
            bonus = base_bonus if has_bonus else 0 
            eff_age = age - bonus
            
            valid_degrees = []
            age_reasons = []
            is_major_ok_general = False
            
            for deg, maj in profile['degrees']:
                if check_eligibility(deg, maj, exam_data['final_req_json']):
                    is_major_ok_general = True
                    u_deg_norm = normalize_text(deg)
                    
                    specific_min, specific_max = exam_data['e_min'], exam_data['e_max']
                    try:
                        req_data = json.loads(exam_data['final_req_json'])
                        for item in req_data.get('items', []):
                            if normalize_text(item.get('degree', '')) in ['همه', u_deg_norm]:
                                specific_min = item.get('min_age', exam_data['e_min'])
                                specific_max = item.get('max_age', exam_data['e_max'])
                                break
                    except: 
                        pass
                    
                    if specific_min <= eff_age <= specific_max:
                        valid_degrees.append(f"{deg} {maj}")
                    else:
                        age_reasons.append(f"سن شما ({eff_age} سال) با شرایط سنی مقطع {deg} مطابقت ندارد (مجاز: {specific_min} تا {specific_max} سال).")

            is_completely_valid = len(valid_degrees) > 0
            
            # تولید متن مناسب با توجه به وضعیت مجاز بودن یا نبودن
            if is_completely_valid:
                degrees_str = "، ".join(valid_degrees)
                status_text = f"✅ <b>وضعیت شما:</b> با توجه به شرایط شما، <b>مجاز به شرکت در این آزمون هستید (با مدرک: {degrees_str}).</b>\n\n📚 <b>اگه منابع این آزمون رو میخوای پیام بده به ادمین :</b>\nایدی ادمین :\n@omumikade_admin"
            else:
                reasons = []
                if not is_major_ok_general:
                    reasons.append("هیچ‌کدام از رشته‌های تحصیلی شما در لیست رشته‌های این آزمون نیست")
                else:
                    reasons.extend(age_reasons)
                    
                reasons_str = f"\n🔸 ".join(reasons)
                status_text = f"❌ <b>وضعیت شما:</b> متاسفانه به دلایل زیر <b>مجاز به شرکت نیستید:</b>\n🔸 {reasons_str}"

            # ساخت متن نهایی خبر
            msg = (
                f"🔔 <b>خبر جدید: {exam_data['e_name']}</b>\n\n"
                f"{status_text}\n\n"
                f"📅 تاریخ: {full_date}\n"
                f"⏳ فرصت: {days_left} روز"
            )
            
            btn = [[InlineKeyboardButton("📄 مشاهده توضیحات آگهی", callback_data=f"view_exam_{exam_id}")]]
            
            await context.bot.send_message(u_id, msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
            count_registered += 1
            await asyncio.sleep(0.1)
            
        except RetryAfter as e: 
            await asyncio.sleep(e.retry_after + 1)
        except Forbidden: 
            pass 
        except Exception as e: 
            pass

    # -------------------------------------------------------------
    # بخش دوم: ارسال به کاربرانی که فقط استارت زده‌اند (بدون ثبت‌نام)
    # -------------------------------------------------------------
    count_unregistered = 0
    if unregistered_users:
        unreg_msg = (
            f"🔔 <b>آزمون استخدامی جدید منتشر شد!</b>\n\n"
            f"✨ <b>{exam_data['e_name']}</b>\n"
            f"⏳ فرصت ثبت‌نام: {days_left} روز\n\n"
            f"❓ <b>آیا رشته و سن شما برای این آزمون مجاز است؟</b>\n"
            f"شما هنوز اطلاعات خود را در ربات ثبت نکرده‌اید! همین الان از طریق دکمه زیر ثبت‌نام کنید تا شرایط شما رو با دفترچه این آزمون تطبیق بدم و بهتون بگم واجد شرایط هستید یا نه."
        )
        unreg_btn = [[InlineKeyboardButton("✅ ثبت‌نام و بررسی شرایط من", callback_data='pre_register_confirm')]]
        
        for row in unregistered_users:
            u_id = row[0]
            try:
                await context.bot.send_message(u_id, unreg_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(unreg_btn))
                count_unregistered += 1
                await asyncio.sleep(0.1)
            except RetryAfter as e: 
                await asyncio.sleep(e.retry_after + 1)
            except Forbidden: 
                pass 
            except Exception as e: 
                pass

    # گزارش نهایی به ادمین اصلی
    await context.bot.send_message(
        ADMIN_IDS[0], 
        f"✅ ارسال خبر تمام شد.\n👥 تعداد پیام‌های ارسالی به افراد ثبت‌نام شده (مجاز و غیرمجاز): {count_registered}\n👻 تعداد پیام‌های ارسالی به افراد ثبت‌نام نکرده: {count_unregistered}"
    )
    
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    # 🟢 هدایت ادمین به منوی هوشمند جدیدی که اضافه کردیم
    await start_smart_broadcast(update, context)
    
    # 🟢 پایان دادن به وضعیت قدیمی دیتابیس برای جلوگیری از تداخل
    return ConversationHandler.END

async def receive_broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN:
        return await back_to_admin_panel_msg(update, context)
        
    msg_text = update.message.text
    admin_id = update.effective_user.id
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT user_id FROM users") as c:
            users = await c.fetchall()
            
    await update.message.reply_text("⏳ در حال ارسال پیام به کاربران... (لطفا صبور باشید)", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
    
    asyncio.create_task(broadcast_message_task(context, users, msg_text, admin_id))
    return ConversationHandler.END
    
async def broadcast_message_task(context, users, text, admin_id):
    count = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=text, parse_mode='Markdown')
            count += 1
            await asyncio.sleep(0.2)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except Exception:
            pass
            
    await context.bot.send_message(chat_id=admin_id, text=f"✅ پیام همگانی با موفقیت به {count} نفر ارسال شد.")

# ================= پروسه آموزش ربات =================
async def start_set_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # استخراج نام دسته‌بندی که ادمین انتخاب کرده
    category = query.data.replace('admin_set_', '') 
    context.user_data['target_tut_category'] = category
    
    await query.message.reply_text(
        "🎬 لطفاً یک محتوای آموزش (متن، عکس یا ویدیو) برای این بخش بفرستید.\n⚠️ توجه: این محتوا جایگزین آموزش قبلی این بخش خواهد شد.\n\n(برای اتمام و بازگشت، دکمه بازگشت را بزنید)", 
        reply_markup=get_admin_back_kb()
    )
    return ADMIN_SET_TUTORIAL_MSG

async def receive_tutorial_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN:
        return await back_to_admin_panel_msg(update, context)
        
    msg_type = 'text'
    content = update.message.text or ''
    caption = ''

    if update.message.photo:
        msg_type = 'photo'
        content = update.message.photo[-1].file_id
        caption = update.message.caption or ''
    elif update.message.video:
        msg_type = 'video'
        content = update.message.video.file_id
        caption = update.message.caption or ''
    
    category = context.user_data.get('target_tut_category', 'general')
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        # حذف ویدیوی قبلی این دسته تا فقط یک ویدیو برای هر دکمه داشته باشیم
        await conn.execute("DELETE FROM tutorials WHERE category=?", (category,))
        await conn.execute("INSERT INTO tutorials (type, content, caption, category) VALUES (?, ?, ?, ?)", (msg_type, content, caption, category))
        await conn.commit()

    await update.message.reply_text("✅ محتوای آموزش با موفقیت ثبت و جایگزین شد!", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
    return ConversationHandler.END

# ================= پروسه افزودن آزمون پیش رو =================
async def start_add_upcoming_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📊 لطفا نام آزمون پیش رو را وارد کنید:", reply_markup=get_admin_back_kb())
    return UPCOMING_NAME

async def receive_upcoming_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: return await back_to_admin_panel_msg(update, context)
    context.user_data['up_name'] = update.message.text
    await update.message.reply_text("📝 لطفا متن توضیحات آزمون را وارد کنید:", reply_markup=get_admin_back_kb())
    return UPCOMING_DESC

async def receive_upcoming_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: return await back_to_admin_panel_msg(update, context)
    context.user_data['up_desc'] = update.message.text
    await update.message.reply_text("🎙 لطفا فایل ویس (Voice) مربوط به این آزمون را ارسال کنید:", reply_markup=get_admin_back_kb())
    return UPCOMING_VOICE

async def receive_upcoming_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: return await back_to_admin_panel_msg(update, context)
    if not update.message.voice:
        await update.message.reply_text("❌ لطفا حتما یک فایل ویس ارسال کنید.")
        return UPCOMING_VOICE
    
    voice_id = update.message.voice.file_id
    name = context.user_data.get('up_name')
    desc = context.user_data.get('up_desc')
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        await conn.execute("INSERT INTO upcoming_exams (name, description, voice_file_id) VALUES (?, ?, ?)", (name, desc, voice_id))
        await conn.commit()
        
    await update.message.reply_text("✅ آزمون پیش رو با موفقیت ثبت شد.", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
    return ConversationHandler.END

# ================= پروسه ویرایش کاربران از طریق اکسل =================
async def start_user_excel_edit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "✏️ لطفا فایل اکسل ویرایش شده کاربران را ارسال کنید.\n\n"
        "⚠️ توجه: ساختار ستون‌ها دقیقا باید مشابه فایل خروجی سیستم باشد (ستون اول حاوی آیدی عددی کاربران باشد).",
        reply_markup=get_admin_back_kb()
    )
    return ADMIN_USER_EXCEL_UPLOAD

async def receive_user_edit_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: 
        return await back_to_admin_panel_msg(update, context)
        
    if not update.message.document:
        await update.message.reply_text("❌ لطفاً فایل را به صورت فایل (document) بفرستید.")
        return ADMIN_USER_EXCEL_UPLOAD

    if not update.message.document.file_name.lower().endswith('.xlsx'):
        await update.message.reply_text("❌ فرمت فایل حتماً باید .xlsx باشد.")
        return ADMIN_USER_EXCEL_UPLOAD

    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        
        count = 0
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            for row in rows:
                if not row or row[0] is None: continue
                user_id = int(row[0])
                name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
                phone = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
                b_year = int(row[3]) if len(row) > 3 and row[3] is not None else None
                b_month = int(row[4]) if len(row) > 4 and row[4] is not None else None
                b_day = int(row[5]) if len(row) > 5 and row[5] is not None else None
                is_married = int(row[6]) if len(row) > 6 and row[6] is not None else 0
                children_count = int(row[7]) if len(row) > 7 and row[7] is not None else 0
                
                # 🟢 ۱. استخراج داینامیک تمام مدارک و رشته‌ها از ستون‌های ۸ به بعد اکسل
                user_all_degrees = []
                idx = 8
                while idx < len(row):
                    deg_val = str(row[idx]).strip() if row[idx] is not None else ""
                    maj_val = str(row[idx+1]).strip() if idx+1 < len(row) and row[idx+1] is not None else ""
                    
                    if deg_val or maj_val:
                        user_all_degrees.append((deg_val, normalize_text(maj_val)))
                    idx += 2
                
                # پیدا کردن آخرین مدرک برای حفظ سازگاری در جدول اصلی
                last_deg = user_all_degrees[-1][0] if user_all_degrees else ""
                last_maj = user_all_degrees[-1][1] if user_all_degrees else ""
                
                # ۲. بروزرسانی اطلاعات اصلی کاربر
                await conn.execute('''INSERT OR REPLACE INTO users 
                    (user_id, name, phone, b_year, b_month, b_day, is_married, children_count, degree, major) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (user_id, name, phone, b_year, b_month, b_day, is_married, children_count, last_deg, last_maj))
                
                # 🟢 ۳. پاک کردن مدارک قبلی این کاربر و جایگذاری تمام مدارک جدید استخراج شده از اکسل
                await conn.execute("DELETE FROM user_degrees WHERE user_id=?", (user_id,))
                for deg, maj in user_all_degrees:
                    await conn.execute("INSERT INTO user_degrees (user_id, degree, major) VALUES (?, ?, ?)", (user_id, deg, maj))
                
                count += 1
            await conn.commit()
        
        await update.message.reply_text(f"✅ اطلاعات {count} کاربر با موفقیت بروزرسانی شد.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش فایل: {str(e)}")
        return ADMIN_USER_EXCEL_UPLOAD

# ================= پروسه ثبت نام و قفل جوین اجباری =================
async def start_edit_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    is_editing = False
    skip_video = False # 🟢 اضافه شده: متغیری برای اسکیپ کردن ویدیو
    
    if query:
        await query.answer()
        try: await query.message.delete()
        except: pass
        is_editing = (query.data == 'edit_profile')
        context.user_data['is_editing'] = is_editing
        
        # 🟢 اضافه شده: تشخیص اینکه آیا کاربر از پیام یادآوری آمده است یا خیر
        skip_video = (query.data == 'start_register_skip_video')

    if not await is_member(user_id, context.bot):
        kb = [
            [InlineKeyboardButton("📢 عضویت در کانال عمومی کده", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
            [InlineKeyboardButton("📢 عضویت در کانال مصاحبه", url=f"https://t.me/{CHANNEL_ID_2.replace('@', '')}")],
            [InlineKeyboardButton("✅ عضو شدم (ادامه)", callback_data='start_register')]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ **دسترسی محدود!**\n\nبرای ثبت‌نام، ویرایش اطلاعات و استفاده از آزمون‌یاب، ابتدا باید در کانال های ما عضو شوید. پس از عضویت، دکمه زیر را بزنید.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ConversationHandler.END

    # 🟢 بررسی محدودیت ویرایش در صورتی که کاربر قصد ویرایش دارد
    if is_editing:
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT lock_until FROM users WHERE user_id=?", (user_id,)) as c:
                row = await c.fetchone()
                if row:
                    lock_until = row[0] or 0
                    now = int(time.time())
                    if now < lock_until and user_id not in ADMIN_IDS:
                        diff = lock_until - now
                        if diff < 86400:
                            time_str = "فردا"
                        elif diff < 86400 * 8:
                            time_str = "یک هفته دیگر"
                        else:
                            time_str = "یک ماه دیگر"
                        
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"❌ **محدودیت ویرایش!**\n\nشما بیش از حد مجاز اطلاعات خود را ویرایش کرده‌اید. برای جلوگیری از سوءاستفاده، امکان ویرایش مجدد برای شما تا **{time_str}** مسدود شده است.",
                            parse_mode='Markdown'
                        )
                        return ConversationHandler.END

    # پاک کردن مدارک موقت قبلی
    context.user_data['temp_degrees'] = []

    # 🟢 تغییر کوچک اینجاست: اگر کاربر در حال ویرایش است "یا باید ویدیو اسکیپ شود"، مرحله آموزش را رد می‌کنیم
    if is_editing or skip_video:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✍️ لطفا **نام و نام خانوادگی** خود را وارد کنید:",
            parse_mode='Markdown',
            reply_markup=get_back_kb()
        )
        return NAME

    # --- استخراج ویدیوی آموزش ابتدایی برای ثبت نام اولیه ---
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT type, content, caption FROM tutorials WHERE category='tut_initial' LIMIT 1") as c:
            tutorial = await c.fetchone()

    if tutorial:
        t_type, content, caption = tutorial
        base_caption = caption if caption else ""
        
        # متن جذاب‌تر با تاکید و تغییر دقیق اسم دکمه
        video_caption = f"{base_caption}\n\nاین کلیپ آموزش ثبت نام در رباته 👆\n \n ببین رفیق \n برای اینکه در ربات بدون اشتباه ثبت نام کنی\n **حتما حتما** ‼️ کلیپ رو تا آخر ببین\nوقتی کلیپ رو دیدی رو دکمه ویدئو رو کامل دیدم کلیک کن 👇"
        kb = [[InlineKeyboardButton("ویدئو رو کامل دیدم", callback_data='video_watched')]]
        
        if t_type == 'photo':
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=content, caption=video_caption, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        elif t_type == 'video':
            await context.bot.send_video(chat_id=update.effective_chat.id, video=content, caption=video_caption, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{content}\n\n{video_caption}", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        
        context.user_data['video_start'] = time.time()
        return WAIT_FOR_VIDEO
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✍️ لطفا **نام و نام خانوادگی** خود را وارد کنید:",
            parse_mode='Markdown',
            reply_markup=get_back_kb()
        )
        return NAME
    
async def check_video_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # 🟢 تغییر سوم: شرط قفل زمانی کلاً برداشته شد
    await query.answer()
    try: await query.message.delete()
    except: pass
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✍️ لطفا **نام و نام خانوادگی** خود را وارد کنید:",
        parse_mode='Markdown',
        reply_markup=get_back_kb()
    )
    return NAME
    
async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_BTN or update.message.text == '❌ انصراف': return await cancel(update, context)
    context.user_data['name'] = normalize_text(update.message.text)
    
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("📱 ارسال شماره موبایل", request_contact=True)],
        [KeyboardButton(BACK_BTN)]
    ], one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text("شماره موبایل خود را وارد کنید یا از طریق دکمه زیر ارسال کنید:", reply_markup=kb)
    return PHONE
    
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_BTN: return await cancel(update, context)

    phone = None
    if update.message.contact:
        phone = update.message.contact.phone_number
    elif update.message.text:
        text = update.message.text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
        clean_text = text.replace(' ', '').replace('-', '').strip()
        if clean_text.startswith('+98'): clean_text = '0' + clean_text[3:]
        elif clean_text.startswith('98'): clean_text = '0' + clean_text[2:]

        if re.match(r'^09\d{9}$', clean_text): phone = clean_text
        else:
            await update.message.reply_text("❌ فرمت شماره اشتباه است. لطفاً صحیح وارد کنید یا از دکمه استفاده کنید.", reply_markup=get_back_kb())
            return PHONE
    else:
        await update.message.reply_text("❌ لطفا شماره موبایل خود را ارسال کنید.", reply_markup=get_back_kb())
        return PHONE
    
    if phone.startswith('+98'): phone = '0' + phone[3:]
    elif phone.startswith('98'): phone = '0' + phone[2:]
    
    context.user_data['phone'] = phone
    await update.message.reply_text("🗓 سال تولدتون رو وارد کنید \nمثال : 1375", reply_markup=get_back_kb())
    return B_YEAR
    
async def receive_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_BTN: return await cancel(update, context)
    try:
        year = int(update.message.text)
        if year < 1300 or year > 1404:
             await update.message.reply_text("❌ سال تولد نامعتبر است. لطفاً سال صحیح (مثلاً 1375) وارد کنید.", reply_markup=get_back_kb())
             return B_YEAR
        context.user_data['b_year'] = year
        await update.message.reply_text("🗓 ماه تولدتون رو از بین ( 1 تا 12 ) وارد کنید \nمثال : 5", reply_markup=get_back_kb())
        return B_MONTH
    except ValueError:
         await update.message.reply_text("❌ لطفاً سال را به عدد وارد کنید.", reply_markup=get_back_kb())
         return B_YEAR

async def receive_month(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    if update.message.text == BACK_BTN: return await cancel(update, context)
    try:
        month = int(update.message.text)
        if month < 1 or month > 12:
            await update.message.reply_text("❌ ماه وارد شده اشتباه است. عددی بین 1 تا 12 وارد کنید.", reply_markup=get_back_kb())
            return B_MONTH
        context.user_data['b_month'] = month
        await update.message.reply_text("🗓 روز تولدتون رو از بین ( 1 تا 31 ) وارد کنید \nمثال : 10", reply_markup=get_back_kb())
        return B_DAY
    except ValueError:
        await update.message.reply_text("❌ لطفاً ماه را به عدد وارد کنید.", reply_markup=get_back_kb())
        return B_MONTH

async def receive_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_BTN: return await cancel(update, context)
    try:
        day = int(update.message.text)
        if day < 1 or day > 31:
             await update.message.reply_text("❌ روز وارد شده اشتباه است. عددی بین 1 تا 31 وارد کنید.", reply_markup=get_back_kb())
             return B_DAY
        context.user_data['b_day'] = day
        
        await update.message.reply_text("✅ تاریخ تولد ثبت شد.", reply_markup=get_back_kb())
        await update.message.reply_text("وضعیت تاهل؟", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("مجرد 👤", callback_data='single')], [InlineKeyboardButton("متاهل 💍", callback_data='married')]]))
        return MARITAL_STATUS
    except ValueError:
        await update.message.reply_text("❌ لطفاً روز را به عدد وارد کنید.", reply_markup=get_back_kb())
        return B_DAY
    
async def receive_marital_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data == 'single': 
        context.user_data['is_married'] = 0; context.user_data['children_count'] = 0
        return await ask_degree_inline(update, context)
    else: 
        context.user_data['is_married'] = 1
        btns = [InlineKeyboardButton(str(i), callback_data=f'k_{i}') for i in range(4)]
        btns.append(InlineKeyboardButton("4+", callback_data='k_4'))
        await query.message.edit_text("تعداد فرزندان؟", reply_markup=InlineKeyboardMarkup([btns]))
        return CHILDREN_COUNT

async def receive_children_inline(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    context.user_data['children_count'] = int(update.callback_query.data.split('_')[1])
    return await ask_degree_inline(update, context)

async def ask_degree_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("دیپلم", callback_data='deg_diploma'), InlineKeyboardButton("کاردانی", callback_data='deg_associate')],
        [InlineKeyboardButton("کارشناسی", callback_data='deg_bachelor'), InlineKeyboardButton("ارشد", callback_data='deg_master')],
        [InlineKeyboardButton("دکتری", callback_data='deg_phd_base'), InlineKeyboardButton("دانشنامه تخصصی", callback_data='deg_specialty')],
        [InlineKeyboardButton("حوزوی", callback_data='deg_seminary_base'), InlineKeyboardButton("حافظ قرآن", callback_data='deg_quran')]
    ]
    
    # شمارش مدارک برای شخصی‌سازی جذاب متن دکمه مقطع
    temp_degrees = context.user_data.get('temp_degrees', [])
    txt = "مدرک تحصیلی:" if not temp_degrees else f"مدرک تحصیلی {len(temp_degrees) + 1} خود را انتخاب کنید:"
    
    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    return DEGREE

async def receive_degree_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    direct_maps = {
        'deg_diploma': 'دیپلم', 'deg_associate': 'کاردانی',
        'deg_bachelor': 'کارشناسی', 'deg_master': 'ارشد',
        'deg_specialty': 'دانشنامه تخصصی'
    }

    if data in direct_maps:
        context.user_data['current_degree_name'] = direct_maps[data]
        await query.message.delete()
        
        if data == 'deg_diploma':
            msg = (
                "📚 نام رشته تحصیلی دیپلم خود را وارد کنید:\n\n"
                "❌ غلط: دیپلم ریاضی فیزیک\n"
                "✅ صحیح: ریاضی فیزیک\n\n"
                "❌ غلط: رشته تجربی هستم\n"
                "✅ صحیح: علوم تجربی\n\n"
                "❌ غلط: من رشتم حسابداریه\n"
                "✅ صحیح: حسابداری"
            )
        else:
            msg = (
                "📚 نام رشته تحصیلی خود را وارد کنید:\n\n"
                "❌ غلط: کارشناسی حقوق\n"
                "✅ صحیح: حقوق\n\n"
                "❌ غلط: مدیریت بازرگانی گرایش بازار\n"
                "✅ صحیح: مدیریت بازرگانی بازار\n\n"
                "❌ غلط: omran\n"
                "✅ صحیح: عمران\n\n"
                "❌ غلط: من رشتم معارفعه\n"
                "✅ صحیح: معارف"
            )
        
        await query.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_back_kb())
        return MAJOR

    elif data == 'deg_phd_base':
        kb = [
            [InlineKeyboardButton("دکتری", callback_data='deg_sub_phd')],
            [InlineKeyboardButton("دکتری تخصصی", callback_data='deg_sub_phd_spec')]
        ]
        await query.message.edit_text("نوع دکتری را مشخص کنید:", reply_markup=InlineKeyboardMarkup(kb))
        return DEGREE_SUB

    elif data == 'deg_seminary_base':
        kb = [
            [InlineKeyboardButton("سطح 1", callback_data='deg_sub_sem_1'), InlineKeyboardButton("سطح 2", callback_data='deg_sub_sem_2')],
            [InlineKeyboardButton("سطح 3", callback_data='deg_sub_sem_3'), InlineKeyboardButton("سطح 4", callback_data='deg_sub_sem_4')]
        ]
        await query.message.edit_text("کدام سطح حوزوی هستید؟", reply_markup=InlineKeyboardMarkup(kb))
        return DEGREE_SUB
        
    elif data == 'deg_quran':
        kb = [
            [InlineKeyboardButton("درجه 1", callback_data='deg_sub_quran_1'), InlineKeyboardButton("درجه 2", callback_data='deg_sub_quran_2')],
            [InlineKeyboardButton("درجه 3", callback_data='deg_sub_quran_3'), InlineKeyboardButton("درجه 4", callback_data='deg_sub_quran_4')],
            [InlineKeyboardButton("درجه 5", callback_data='deg_sub_quran_5')]
        ]
        await query.message.edit_text("لطفاً درجه حفظ خود را مشخص کنید:", reply_markup=InlineKeyboardMarkup(kb))
        return DEGREE_SUB

async def receive_degree_sub_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # مپینگ برای دکتری که نیاز به پرسیدن رشته دارد
    phd_maps = {
        'deg_sub_phd': 'دکتری',
        'deg_sub_phd_spec': 'دکتری تخصصی'
    }
    
    # مپینگ اتوماتیک برای حوزوی و حافظ قرآن که مستقیماً مقطع و رشته را تنظیم می‌کند
    auto_major_maps = {
        'deg_sub_sem_1': ('حوزوی', 'سطح 1'),
        'deg_sub_sem_2': ('حوزوی', 'سطح 2'),
        'deg_sub_sem_3': ('حوزوی', 'سطح 3'),
        'deg_sub_sem_4': ('حوزوی', 'سطح 4'),
        'deg_sub_quran_1': ('حافظ قرآن', 'درجه 1'),
        'deg_sub_quran_2': ('حافظ قرآن', 'درجه 2'),
        'deg_sub_quran_3': ('حافظ قرآن', 'درجه 3'),
        'deg_sub_quran_4': ('حافظ قرآن', 'درجه 4'),
        'deg_sub_quran_5': ('حافظ قرآن', 'درجه 5')
    }

    if data in phd_maps:
        context.user_data['current_degree_name'] = phd_maps[data]
        await query.message.delete()
        msg = (
            "📚 نام رشته تحصیلی خود را وارد کنید:\n\n"
            "❌ غلط: کارشناسی حقوق\n"
            "✅ صحیح: حقوق\n\n"
            "❌ غلط: مدیریت بازرگانی گرایش بازار\n"
            "✅ صحیح: مدیریت بازرگانی بازار\n\n"
            "❌ غلط: omran\n"
            "✅ صحیح: عمران\n\n"
            "❌ غلط: من رشتم معارفعه\n"
            "✅ صحیح: معارف"
        )
        await query.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_back_kb())
        return MAJOR
        
    elif data in auto_major_maps:
        degree_name, major_name = auto_major_maps[data]
        
        if 'temp_degrees' not in context.user_data:
            context.user_data['temp_degrees'] = []
            
        # ثبت مستقیم بدون گرفتن تایپ از کاربر
        context.user_data['temp_degrees'].append({'degree': degree_name, 'major': major_name})
        await query.message.delete()
        
        kb = [
            [InlineKeyboardButton("➕ بله، دارم", callback_data='has_more_degree_yes')],
            [InlineKeyboardButton("❌ خیر، همین مدارک کافیه", callback_data='has_more_degree_no')]
        ]
        await query.message.reply_text(
            "❓ آیا مدرک تحصیلی دیگری دارید که بخواهید ثبتش کنید؟ 🎓➕\n\n"
            "💡 *ثبت چند مدرک به شما کمک میکند شانس قبولی خود را در انواع موقعیت‌های شغلی فعال ارزیابی کنید.*",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ASK_MORE_DEGREES

async def receive_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_BTN: return await cancel(update, context)
    
    raw_text = update.message.text
    
    # 🟢 فراخوانی تابع پاکسازی برای حذف کلماتی مثل لیسانس، ارشد و...
    cleaned_text = clean_major_name(raw_text)
    
    # جلوگیری از خالی موندن رشته (اگه کاربر فقط نوشته بود "لیسانس")
    if not cleaned_text.strip():
        cleaned_text = raw_text

    # دریافت مقطع از متغیر دقیق سیستم
    degree_name = context.user_data.get('current_degree_name', 'نامشخص')
    
    if 'temp_degrees' not in context.user_data:
        context.user_data['temp_degrees'] = []
        
    # ثبت همون یک مدرک با اسم تمیز شده و بدون کلمات اضافه
    is_duplicate = any(d['degree'] == degree_name and d['major'] == cleaned_text for d in context.user_data['temp_degrees'])
    if not is_duplicate:
        context.user_data['temp_degrees'].append({'degree': degree_name, 'major': cleaned_text})
            
    # استفاده از دکمه‌ها
    kb = [
        [InlineKeyboardButton("➕ بله، دارم", callback_data='has_more_degree_yes')],
        [InlineKeyboardButton("❌ خیر، همین مدارک کافیه", callback_data='has_more_degree_no')]
    ]
    
    await update.message.reply_text(
        "❓ آیا مدرک تحصیلی دیگری دارید که بخواهید ثبتش کنید؟ 🎓➕\n\n"
        "💡 ثبت چند مدرک به شما کمک میکند شانس قبولی خود را در انواع موقعیت‌های شغلی فعال ارزیابی کنید.",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ASK_MORE_DEGREES

async def receive_more_degrees_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'has_more_degree_yes':
        try:
            await query.message.delete()
        except:
            pass
        
        # 🟢 اصلاح اصلی: به جای ادیت کردن پیامِ پاک شده، وضعیت را روی DEGREE تنظیم میکنیم
        # و تابع ask_degree_inline با آبجکت کوئری، پیام جدید می‌فرستد.
        context.user_data['current_query'] = query
        
        kb = [
            [InlineKeyboardButton("دیپلم", callback_data='deg_diploma'), InlineKeyboardButton("کاردانی", callback_data='deg_associate')],
            [InlineKeyboardButton("کارشناسی", callback_data='deg_bachelor'), InlineKeyboardButton("ارشد", callback_data='deg_master')],
            [InlineKeyboardButton("دکتری", callback_data='deg_phd_base'), InlineKeyboardButton("دانشنامه تخصصی", callback_data='deg_specialty')],
            [InlineKeyboardButton("حوزوی", callback_data='deg_seminary_base'), InlineKeyboardButton("حافظ قرآن", callback_data='deg_quran')]
        ]
        temp_degrees = context.user_data.get('temp_degrees', [])
        txt = f"🎓 مدرک تحصیلی {len(temp_degrees) + 1} خود را انتخاب کنید:"
        
        # فرستادن پیام جدید به جای ادیت پیام حذف شده
        await context.bot.send_message(chat_id=update.effective_chat.id, text=txt, reply_markup=InlineKeyboardMarkup(kb))
        return DEGREE
        
    elif query.data == 'has_more_degree_no':
        try:
            await query.message.delete()
        except:
            pass
        user_id = update.effective_user.id
        ud = context.user_data
        temp_degrees = ud.get('temp_degrees', [])
        
        last_deg = temp_degrees[-1]['degree'] if temp_degrees else ""
        last_maj = temp_degrees[-1]['major'] if temp_degrees else ""
        is_editing = context.user_data.get('is_editing', False)
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            if is_editing:
                # 🟢 مدیریت لاجیک جریمه‌ها (فقط هنگام ویرایش اعمال می‌شود)
                async with conn.execute("SELECT edit_count, penalty_level FROM users WHERE user_id=?", (user_id,)) as c:
                    row = await c.fetchone()
                    e_count = row[0] if row and row[0] else 0
                    p_level = row[1] if row and row[1] else 0
                
                e_count += 1
                lock_until = 0
                now = int(time.time())

                if p_level == 0 and e_count >= 3:
                    lock_until = now + (24 * 3600)  # قفل تا فردا
                    p_level = 1
                    e_count = 0
                elif p_level == 1 and e_count >= 1:
                    lock_until = now + (7 * 24 * 3600) # قفل یک هفته‌ای
                    p_level = 2
                    e_count = 0
                elif p_level >= 2 and e_count >= 1:
                    lock_until = now + (30 * 24 * 3600) # قفل یک ماهه
                    p_level = 3
                    e_count = 0

                await conn.execute('''UPDATE users SET 
                                      name=?, phone=?, b_year=?, b_month=?, b_day=?, is_married=?, children_count=?, degree=?, major=?,
                                      edit_count=?, penalty_level=?, lock_until=?
                                      WHERE user_id=?''', 
                                   (ud['name'], ud['phone'], ud['b_year'], ud['b_month'], ud['b_day'], ud.get('is_married', 0), ud.get('children_count', 0), last_deg, last_maj, e_count, p_level, lock_until, user_id))
            else:
                # ثبت نام بار اول (بدون شمارش ویرایش)
                await conn.execute('''INSERT OR REPLACE INTO users (user_id, name, phone, b_year, b_month, b_day, is_married, children_count, degree, major) 
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                   (user_id, ud['name'], ud['phone'], ud['b_year'], ud['b_month'], ud['b_day'], ud.get('is_married', 0), ud.get('children_count', 0), last_deg, last_maj))
            
            # ذخیره مدارک جانبی
            await conn.execute("DELETE FROM user_degrees WHERE user_id=?", (user_id,))
            for deg_item in temp_degrees:
                await conn.execute("INSERT INTO user_degrees (user_id, degree, major) VALUES (?, ?, ?)", (user_id, deg_item['degree'], deg_item['major']))
            await conn.commit()
        
        reply_kb = await get_main_reply_keyboard(user_id)
        
        if is_editing:
            chat_id = update.effective_chat.id
            await context.bot.send_message(chat_id=chat_id, text="✅ اطلاعات پروفایل شما با موفقیت ویرایش شد.", reply_markup=reply_kb, parse_mode='Markdown')
        else:
            success_text = (
                "🎉 **تبریک! ثبت‌نام شما در \"آزمون یاب\" با موفقیت تکمیل شد.**\n\n"
                "⚠️ نکته مهم اول ⚠️\n\n"
                "قبل از اینکه با ربات کار کنی اول دکمه آموزش کار با ربات رو بزن و آموزش ها رو با دقت ببین \n\n"
                "⚠️نکته مهم دوم ⚠️\n\n"
                "ما تمام دفترچه‌های استخدامی رو دقیقاً با همون املایی که برای **«رشته تحصیلی‌ت»** وارد کردی تطبیق می‌دیم.\n\n"
                "❌ **اگر رشته‌ات رو با غلط املایی نوشته باشی،** یا کلمات اضافه توش باشه، سیستم نمی‌تونه شغل‌های مرتبط با مدرکت رو پیدا کنه و ممکنه بهترین فرصت‌های استخدامی رو از دست بدی!\n\n"
                "👇 **پس همین الان یه کار کوچیک انجام بده:**\n"
                "از منوی پایین، دکمه **«👤 پروفایل کاربری»** رو لمس کن و یه نگاه به رشته‌ای که ثبت کردی بنداز. اگه حتی یه حرفش هم اشتباهه یا با مدرکت هم‌خوانی دقیق نداره، از همونجا ویرایشش کن تا خیالمون راحت باشه "
            )
            chat_id = update.effective_chat.id
            await context.bot.send_message(chat_id=chat_id, text=success_text, reply_markup=reply_kb, parse_mode='Markdown')
            
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reply_kb = await get_main_reply_keyboard(user_id)
    await update.message.reply_text("لغو شد.", reply_markup=reply_kb)
    return ConversationHandler.END

# ================= هندلرهای Inline (دکمه‌های شیشه‌ای) =================
async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    query_data = query.data
    if query_data.startswith("bc_"):
        if query_data == "bc_confirm_send":
            await finalize_smart_broadcast(update, context)
        else:
            await handle_broadcast_callback(update, context)
        return
    
    user_id = update.effective_user.id
    await query.answer()
    data = query.data
    
    # 🟢 بازگشت سریع به منوی اصلی از طریق دکمه شیشه‌ای (کد جدید)
    if data == 'back_to_main_menu':
        try:
            await query.message.delete()
        except:
            pass
            
        reply_kb = await get_main_reply_keyboard(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text="🏠 به منوی اصلی بازگشتید.",
            reply_markup=reply_kb
        )
        return
    
    # بقیه کدهای قبلی شما دقیقاً از اینجا به بعد ادامه پیدا می‌کنه...
    if data.startswith('view_exam_') or data.startswith('view_upcoming_') or data.startswith('show_my_jobs_') or data.startswith('show_full_majors_'):
        if not await is_member(user_id, context.bot):
            kb = [
                [InlineKeyboardButton("📢 عضویت در کانال عمومی کده", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton("📢 عضویت در کانال مصاحبه", url=f"https://t.me/{CHANNEL_ID_2.replace('@', '')}")],
                [InlineKeyboardButton("🔄 بررسی مجدد عضویت", callback_data='check_membership_dynamic')]
            ]
            
            # 🟢 متن تله (FOMO) برای کاربرانی که لفت داده‌اند
            fomo_text = (
                "⛔️ **توجه توجه!**\n\n"
                "دوست عزیز، سیستم هوشمند ما یک فرصت شغلی عالی مختصِ رشته و سنِ شما پیدا کرده است. "
                "اما از آنجایی که شما از کانال‌های اسپانسر ما خارج شده‌اید (لفت دادید)، دسترسی شما به مشاهده دفترچه‌ها و موقعیت‌های شغلی مسدود شده است!\n\n"
                "👇 برای از دست ندادن این فرصت طلایی، همین الان مجدداً در کانال‌های زیر عضو شوید و سپس دکمه بررسی را بزنید:"
            )
            
            await query.message.reply_text(
                fomo_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(kb)
            )
            return
            
    if data == 'admin_files_menu':
        kb = [
            [InlineKeyboardButton("📄 ارسال فایل رشته‌ها", callback_data='admin_select_exam_for_pdf')],
            [InlineKeyboardButton("📚 ارسال دفترچه اصلی آزمون", callback_data='admin_select_exam_for_booklet')],
            [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data='back_to_admin_main')]
        ]
        await query.message.edit_text("👇 لطفاً نوع فایلی که قصد آپلود آن را دارید انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
        return
    
    if data == 'check_membership_dynamic':
        if await is_member(user_id, context.bot):
            await query.message.edit_text("✅ عضویت شما تایید شد! اکنون می‌توانید از خدمات ربات استفاده کنید.")
        else:
            await query.answer("❌ شما هنوز عضو کانال‌های ما نشده‌اید!", show_alert=True)
        return
        
    if data == 'pre_register_confirm':
        if not await is_member(user_id, context.bot):
            kb = [
                [InlineKeyboardButton("📢 عضویت در کانال عمومی کده", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton("📢 عضویت در کانال مصاحبه", url=f"https://t.me/{CHANNEL_ID_2.replace('@', '')}")],
                [InlineKeyboardButton("✅ عضو شدم (شروع ثبت‌نام)", callback_data='start_direct_registration')]
            ]
            await query.message.edit_text(
                "❌ **دسترسی محدود!**\n\nبرای ثبت‌نام، ابتدا باید در کانال های ما عضو شوید. پس از عضویت، دکمه زیر را بزنید.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(kb)
            )
            return

        txt = (
            "دوست عزیز، برای اینکه بررسی کنیم که شما در آزمون های استخدامی واجد شرایط هستید یا خیر، باید سن و مدرک تحصیلی شما رو بدونیم.\n"
            "آیا مایلید اطلاعات تون رو ثبت کنید ؟"
        )
        kb = [
            [InlineKeyboardButton("بله", callback_data='start_direct_registration')]
        ]
        await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    # 🟢 وقتی کاربر عادی روی دکمه‌های آموزش کلیک میکنه
    if data.startswith('show_tut_'):
        category = data # مقدارش میشه مثلا show_tut_profile
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT type, content, caption FROM tutorials WHERE category=?", (category,)) as c:
                tutorial = await c.fetchone()
        
        if not tutorial:
            await query.answer("❌ هنوز آموزشی برای این بخش ثبت نشده است.", show_alert=True)
            return
            
        t_type, content, caption = tutorial
        if t_type == 'photo':
            await context.bot.send_photo(chat_id=user_id, photo=content, caption=caption)
        elif t_type == 'video':
            await context.bot.send_video(chat_id=user_id, video=content, caption=caption)
        else:
            await context.bot.send_message(chat_id=user_id, text=content)
        return

    # 🟢 وقتی ادمین وارد مدیریت آموزش میشه
    elif data == 'admin_tutorial_menu':
        kb = [
            [InlineKeyboardButton("👤 پروفایل کاربری", callback_data='admin_set_show_tut_profile')],
            [InlineKeyboardButton("🟢 آزمون های در حال ثبت نام", callback_data='admin_set_show_tut_active')],
            [InlineKeyboardButton("🎯 آزمون های مناسب رشته من", callback_data='admin_set_show_tut_matched')],
            [InlineKeyboardButton("📅 آزمون های پیش رو", callback_data='admin_set_show_tut_upcoming')],
            [InlineKeyboardButton("🎬 کلیپ آموزش ابتدایی ربات", callback_data='admin_set_tut_initial')],
            [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data='back_to_admin_main')]
        ]
        await query.message.edit_text("بخش مدیریت آموزش کار با ربات:\nجهت ثبت یا تغییر آموزش، بخش مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
        
    elif data == 'admin_clear_tutorial':
        async with aiosqlite.connect('recruitment.db') as conn:
            await conn.execute("DELETE FROM tutorials")
            await conn.commit()
        await query.answer("✅ تمام آموزش‌های قبلی پاک شد.", show_alert=True)
        kb = [
            [InlineKeyboardButton("➕ افزودن محتوای جدید به آموزش", callback_data='admin_add_tutorial')],
            [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data='back_to_admin_main')]
        ]
        await query.message.edit_text("آموزش‌ها پاک شدند. محتوای جدید را اضافه کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith('view_upcoming_'):
        upcoming_id = int(data.split('_')[2])
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT name, description, voice_file_id FROM upcoming_exams WHERE id=?", (upcoming_id,)) as c:
                res = await c.fetchone()
        if res:
            name, desc, voice_id = res
            caption = f"📢 **{name}**\n\n{desc}"
            if voice_id:
                await context.bot.send_voice(chat_id=user_id, voice=voice_id, caption=caption, parse_mode='Markdown')
            else:
                await context.bot.send_message(chat_id=user_id, text=caption, parse_mode='Markdown')

    elif data == 'admin_list_delete_upcoming':
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT id, name FROM upcoming_exams ORDER BY id DESC") as c:
                exams = await c.fetchall()
        if not exams:
            await query.answer("❌ هیچ آزمون پیش رویی برای حذف وجود ندارد.", show_alert=True)
            return
        keyboard = []
        for ex in exams:
            keyboard.append([InlineKeyboardButton(f"🗑 {ex[1]}", callback_data=f"do_del_up_{ex[0]}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_admin_main')])
        await query.message.edit_text("👇 آزمون پیش رو مورد نظر برای حذف را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('do_del_up_'):
        ex_id = int(data.split('_')[3])
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            await conn.execute("DELETE FROM upcoming_exams WHERE id=?", (ex_id,))
            await conn.commit()
        await query.answer("✅ آزمون پیش رو با موفقیت حذف شد.", show_alert=True)
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT id, name FROM upcoming_exams ORDER BY id DESC") as c:
                exams = await c.fetchall()
        keyboard = []
        for ex in exams:
            keyboard.append([InlineKeyboardButton(f"🗑 {ex[1]}", callback_data=f"do_del_up_{ex[0]}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_admin_main')])
        if exams:
            await query.message.edit_text("👇 آزمون پیش رو مورد نظر برای حذف را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.edit_text("🕴 به پنل مدیریت خوش آمدید:", reply_markup=get_admin_panel_keyboard())

    elif data == 'active_exams':
        await show_active_exams(update, context)

    elif data.startswith('view_exam_'):
        exam_id = int(data.split('_')[2])
        await show_exam_detail(update, context, exam_id)
        
    elif data.startswith("show_full_majors_"):
        await show_full_majors(update, context)

    elif data == 'admin_list_delete_exam':
        await show_delete_exam_list(update, context)

    elif data.startswith('do_delete_exam_'):
        ex_id = int(data.split('_')[3])
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            await conn.execute("DELETE FROM exams WHERE id=?", (ex_id,))
            await conn.commit()
            
        await query.answer("✅ آزمون با موفقیت حذف شد.", show_alert=True)
        await show_delete_exam_list(update, context)
    
    elif data == 'admin_remind_unreg':
        # 1. گرفتن کلیپ آموزش ثبت نام از دیتابیس
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT type, content, caption FROM tutorials WHERE category='tut_initial' LIMIT 1") as c:
                tutorial = await c.fetchone()
            
            # 2. پیدا کردن کاربرانی که فقط استارت زده‌اند و در جدول users نیستند
            async with conn.execute("SELECT user_id FROM active_sessions WHERE user_id NOT IN (SELECT user_id FROM users)") as c:
                unreg_users = await c.fetchall()

        if not tutorial:
            await query.answer("❌ اول باید کلیپ آموزش ابتدایی ربات رو از بخش (مدیریت آموزش ربات) تنظیم کنی!", show_alert=True)
            return

        if not unreg_users:
            await query.answer("❌ در حال حاضر کاربری که ثبت‌نام نکرده باشد، یافت نشد!", show_alert=True)
            return

        await query.message.edit_text(f"⏳ در حال ارسال آموزش به {len(unreg_users)} کاربر ثبت‌نام نکرده... (این فرآیند در پس‌زمینه انجام می‌شود)")
        
        # 3. اجرای تسک ارسال همگانی
        asyncio.create_task(blast_tutorial_task(context, unreg_users, tutorial))
        return    
    
    elif data == 'admin_stats_menu':
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            # گرفتن آمار کل ثبت‌نام شده‌ها
            async with conn.execute("SELECT COUNT(*) FROM users") as c:
                row = await c.fetchone()
                total_users = row[0] if row else 0
            
            # گرفتن آمار کاربرانی که استارت زدند اما ثبت‌نام نکردند
            async with conn.execute("SELECT COUNT(*) FROM active_sessions WHERE user_id NOT IN (SELECT user_id FROM users)") as c:
                row_unreg = await c.fetchone()
                unregistered_users = row_unreg[0] if row_unreg else 0
                
            # گرفتن ۵ رشته پرطرفدار
            async with conn.execute("SELECT major, COUNT(*) as cnt FROM users GROUP BY major ORDER BY cnt DESC LIMIT 5") as c:
                top_majors = await c.fetchall()
        
        # ساخت متن پیام با ایموجی 
        msg = f"📊 آمار جامع کاربران ربات\n\n"
        msg += f"👥 کل کاربران ثبت‌نام شده: {total_users} نفر\n"
        msg += f"👻 کاربران استارت‌زده (بدون ثبت‌نام): {unregistered_users} نفر\n\n"
        
        if top_majors:
            msg += "📌 ۵ رشته پرطرفدار در سیستم:\n"
            for m, cnt in top_majors:
                msg += f"▫️ {m}: {cnt} نفر\n"
                
        kb = [
            [InlineKeyboardButton("📥 دریافت فایل اکسل کاربران", callback_data='admin_download_excel')],
            [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data='back_to_admin_main')]
        ]
        # دقت کنید که parse_mode='Markdown' حذف شده تا کاراکترهای خاص مزاحمتی ایجاد نکنند
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    elif data == 'admin_download_excel':
        await query.answer("در حال آماده‌سازی فایل... (لطفا کمی صبر کنید)", show_alert=False)
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            # ۱. ابتدا اطلاعات پایه و فردی تمام کاربران را می‌گیریم
            async with conn.execute("SELECT user_id, name, phone, b_year, b_month, b_day, is_married, children_count FROM users ORDER BY user_id ASC") as c:
                all_users = await c.fetchall()
            
            # ۲. تمام مدارک ثبت شده را هم می‌گیریم
            async with conn.execute("SELECT user_id, degree, major FROM user_degrees ORDER BY id ASC") as c:
                all_degrees = await c.fetchall()
        
        # دسته‌بندی مدارک براساس آیدی کاربر در یک دیکشنری پایتونی
        user_degrees_map = {}
        for u_id, deg, maj in all_degrees:
            if u_id not in user_degrees_map:
                user_degrees_map[u_id] = []
            user_degrees_map[u_id].append((deg, maj))
            
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Users Data"
        
        # ساخت هدر پایه اکسل
        headers = ['آیدی عددی', 'نام و نام خانوادگی', 'شماره موبایل', 'سال تولد', 'ماه تولد', 'روز تولد', 'وضعیت تاهل (1=متاهل)', 'تعداد فرزند']
        
        # پیدا کردن بیشترین تعداد مدرکی که یک کاربر ثبت کرده برای داینامیک کردن ستون‌های هدر
        max_degrees_count = max([len(degs) for degs in user_degrees_map.values()]) if user_degrees_map else 1
        if max_degrees_count == 0:
            max_degrees_count = 1
            
        # اضافه کردن ستون‌های مدارک به هدر (مدرک ۱، رشته ۱، مدرک ۲، رشته ۲ و...)
        for i in range(1, max_degrees_count + 1):
            headers.append(f"مدرک تحصیلی {i}")
            headers.append(f"رشته تحصیلی {i}")
            
        ws.append(headers)
        
        # چیدن اطلاعات؛ هر کاربر دقیقاً در یک سطر
        for u in all_users:
            u_id = u[0]
            row_data = list(u) # تبدیل تیوپل اطلاعات پایه کاربر به لیست برای اضافه کردن ستون‌ها
            
            # دریافت مدارک اختصاصی این کاربر
            u_degs = user_degrees_map.get(u_id, [])
            
            # اضافه کردن مدارک در ستون‌های جلویی همان سطر
            for deg, maj in u_degs:
                row_data.append(deg)
                row_data.append(maj)
                
            # پر کردن ستون‌های خالی باقی‌مانده با مقدار خالی جهت به هم نخوردن ساختار جدول اکسل
            missing_cols = (max_degrees_count * 2) - (len(u_degs) * 2)
            for _ in range(missing_cols):
                row_data.append("")
                
            ws.append(row_data)
            
        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        
        await context.bot.send_document(
            chat_id=user_id,
            document=file_stream,
            filename=f"users_export_{jdatetime.datetime.now().strftime('%Y-%m-%d')}.xlsx",
            caption="📂 خروجی کامل اطلاعات کاربران ربات\n\n⚠️ هر کاربر در یک ردیف قرار دارد و مدارک بیشتر در ستون‌های بعدی همان ردیف درج شده‌اند."
        )
        
    elif data == 'admin_online_users':
        threshold = int(time.time()) - 240
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT COUNT(*) FROM active_sessions WHERE last_seen >= ?", (threshold,)) as c:
                row = await c.fetchone()
                count = row[0] if row else 0
        
        msg = f"🟢 **آمار لحظه‌ای کاربران:**\n\nتعداد کاربرانی که در ۴ دقیقه گذشته با ربات کار کرده‌اند: **{count} نفر**"
        kb = [[InlineKeyboardButton("🔙 بازگشت به پنل", callback_data='back_to_admin_main')]]
        await query.message.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))

    elif data == 'back_to_admin_main':
        await query.message.edit_text("🕴 به پنل مدیریت خوش آمدید:", reply_markup=get_admin_panel_keyboard())

    elif data.startswith("show_my_jobs_"):
        exam_id = int(data.split("_")[3])
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            async with conn.execute("SELECT b_year, b_month, b_day, is_married, children_count FROM users WHERE user_id=?", (user_id,)) as c:
                u_data = await c.fetchone()
            async with conn.execute("SELECT degree, major FROM user_degrees WHERE user_id=?", (user_id,)) as c:
                u_degrees = await c.fetchall()
            async with conn.execute("SELECT name, exam_date, min_age, max_age, major_req FROM exams WHERE id=?", (exam_id,)) as c:
                exam_data = await c.fetchone()
        
        if not u_data or not exam_data or not u_degrees:
            await query.answer("❌ اطلاعات یافت نشد.", show_alert=True)
            return

        exam_date = exam_data[1]
        global_min = exam_data[2]
        global_max = exam_data[3]
        major_req = exam_data[4]
        
        # 🟢 ۱. اول فایل جیسون رو می‌خونیم تا بفهمیم امتیاز جوانی دارد یا نه
        try:
            req_data = json.loads(major_req)
            items = req_data.get('items', [])
            has_bonus = req_data.get('has_bonus', True)
        except:
            items = []
            has_bonus = True

        # 🟢 ۲. محاسبه سن و اعمال هوشمندانه امتیاز جوانی
        age_at_exam = calculate_age_at_exam(u_data[0], u_data[1], u_data[2], exam_date)
        base_bonus = min((1 if u_data[3] else 0) + u_data[4], 5)
        
        bonus = base_bonus if has_bonus else 0 # اگر نداشت، صفر سال کم میشه
        eff_age = age_at_exam - bonus
        
        degree_blocks = []
        is_major_ok_general = False

        for u_deg, u_maj in u_degrees:
            matched_jobs = get_matched_jobs_for_user(u_deg, u_maj, major_req)
            if matched_jobs:
                is_major_ok_general = True
                u_deg_norm = normalize_text(u_deg)
                
                # 🟢 بررسی سن اختصاصی
                specific_min, specific_max = global_min, global_max
                for item in items:
                    req_deg = normalize_text(item.get('degree', ''))
                    if req_deg == 'همه' or req_deg == u_deg_norm:
                        specific_min = item.get('min_age', global_min)
                        specific_max = item.get('max_age', global_max)
                        break
                        
                if specific_min <= eff_age <= specific_max:
                    jobs_list_str = "\n".join([f"🔸 {j}" for j in set(matched_jobs)])
                    clean_maj = clean_major_name(u_maj) # 🟢 اعمال فیلتر نمایشی
                    block = f"🎓 با مدرک <b>{u_deg} {clean_maj}</b> در جایگاه‌های زیر مجازید:\n{jobs_list_str}"
                    degree_blocks.append(block)
        
        if degree_blocks:
            all_blocks_str = "\n\n➖➖➖➖➖➖➖➖\n\n".join(degree_blocks)
            msg = (
                f"✅ <b>تایید شرایط شما در این آزمون</b>\n\n"
                f"🎂 وضعیت سنی: مجاز\n\n"
                f"{all_blocks_str}\n\n"
                f"📚 <b>اگه منابع این آزمون رو میخوای پیام بده به ادمین :</b>\n"
                f"ایدی ادمین :\n@omumikade_admin"
            )
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='HTML')
        else:
            if not is_major_ok_general:
                msg = "❌ <b>عدم تطابق رشته یا مدرک</b>\n\nدوست عزیز، هیچ‌یک از مدارک یا رشته‌های ثبت‌شده شما در دفترچه این آزمون برای هیچ شغلی تعریف نشده است."
            else:
                msg = f"⛔️ <b>عدم احراز شرایط سنی</b>\n\nرشته شما مجاز است اما سن محاسبه شده شما ({eff_age} سال) با سقف سنی مدرک شما تطابق ندارد."
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='HTML')
async def start_upload_pdf_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT id, name FROM exams ORDER BY id DESC LIMIT 10") as c:
            exams = await c.fetchall()
            
    if not exams:
        await query.message.edit_text("❌ ابتدا باید حداقل یک آزمون از طریق فایل اکسل ثبت کنید.", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END
        
    keyboard = []
    for ex in exams:
        keyboard.append([InlineKeyboardButton(f"📄 {ex[1]}", callback_data=f"pdf_target_{ex[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_admin_main')])
    
    await query.message.edit_text("👇 انتخاب کنید فایل PDF رشته‌ها متعلق به کدام آزمون است:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_UPLOAD_EXAM_PDF

async def receive_exam_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query and query.data.startswith("pdf_target_"):
        await query.answer()
        exam_id = int(query.data.split("_")[2])
        context.user_data['target_pdf_exam_id'] = exam_id
        await query.message.reply_text("📥 عالیه! حالا لطفاً فایل PDF مربوط به رشته‌های این آزمون را ارسال کنید:", reply_markup=get_admin_back_kb())
        return ADMIN_UPLOAD_EXAM_PDF
        
    if update.message and update.message.text == ADMIN_BACK_BTN:
        return await back_to_admin_panel_msg(update, context)
        
    if update.message and update.message.document:
        doc = update.message.document
        if not doc.file_name.lower().endswith('.pdf'):
            await update.message.reply_text("❌ خطای فرمت! لطفاً فایل با فرمت .pdf ارسال کنید.")
            return ADMIN_UPLOAD_EXAM_PDF
            
        exam_id = context.user_data.get('target_pdf_exam_id')
        pdf_id = doc.file_id
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            await conn.execute("UPDATE exams SET pdf_file_id = ? WHERE id = ?", (pdf_id, exam_id))
            await conn.commit()
            
        await update.message.reply_text("✅ فایل PDF رشته‌های آزمون با موفقیت به آزمون متصل شد.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END
        
    await update.message.reply_text("❌ لطفاً فایل PDF را ارسال کنید.")
    return ADMIN_UPLOAD_EXAM_PDF

async def start_upload_booklet_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT id, name FROM exams ORDER BY id DESC LIMIT 10") as c:
            exams = await c.fetchall()
            
    if not exams:
        await query.message.edit_text("❌ هیچ آزمونی ثبت نشده است.", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END
        
    keyboard = []
    for ex in exams:
        keyboard.append([InlineKeyboardButton(f"📚 {ex[1]}", callback_data=f"booklet_target_{ex[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_admin_main')])
    
    await query.message.edit_text("👇 انتخاب کنید فایل دفترچه متعلق به کدام آزمون است:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_UPLOAD_EXAM_BOOKLET

async def receive_exam_booklet_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query and query.data.startswith("booklet_target_"):
        await query.answer()
        exam_id = int(query.data.split("_")[2])
        context.user_data['target_booklet_exam_id'] = exam_id
        await query.message.reply_text("📥 عالیه! حالا لطفاً فایل PDF دفترچه اصلی این آزمون را ارسال کنید:", reply_markup=get_admin_back_kb())
        return ADMIN_UPLOAD_EXAM_BOOKLET
        
    if update.message and update.message.text == ADMIN_BACK_BTN:
        return await back_to_admin_panel_msg(update, context)
        
    if update.message and update.message.document:
        doc = update.message.document
        if not doc.file_name.lower().endswith('.pdf'):
            await update.message.reply_text("❌ خطای فرمت! لطفاً فایل با فرمت .pdf ارسال کنید.")
            return ADMIN_UPLOAD_EXAM_BOOKLET
            
        exam_id = context.user_data.get('target_booklet_exam_id')
        pdf_id = doc.file_id
        
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            await conn.execute("UPDATE exams SET booklet_file_id = ? WHERE id = ?", (pdf_id, exam_id))
            await conn.commit()
            
        await update.message.reply_text("✅ فایل دفترچه اصلی آزمون با موفقیت آپلود و متصل شد.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END
        
    await update.message.reply_text("❌ لطفاً فایل PDF را ارسال کنید.")
    return ADMIN_UPLOAD_EXAM_BOOKLET

async def admin_start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🔍 لطفا مقطع تحصیلی مورد نظر را وارد کنید (مثلاً: کارشناسی، ارشد، دیپلم):",
        reply_markup=get_admin_back_kb()
    )
    return ADMIN_SEARCH_DEGREE

async def admin_receive_search_degree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: return await back_to_admin_panel_msg(update, context)
    context.user_data['search_deg'] = normalize_text(update.message.text)
    
    await update.message.reply_text(
        "📚 حالا رشته تحصیلی مورد نظر را وارد کنید (مثلاً: حسابداری، علوم تربیتی):",
        reply_markup=get_admin_back_kb()
    )
    return ADMIN_SEARCH_MAJOR

async def admin_receive_search_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_BACK_BTN: return await back_to_admin_panel_msg(update, context)
    
    search_maj = normalize_text(update.message.text)
    search_deg = context.user_data.get('search_deg')
    
    await update.message.reply_text("⏳ در حال جستجو در دیتابیس آزمون‌ها...", reply_markup=ReplyKeyboardRemove())
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        async with conn.execute("SELECT name, exam_date, reg_end, major_req FROM exams ORDER BY exam_date DESC") as c:
            exams = await c.fetchall()
            
    if not exams:
        await update.message.reply_text("❌ هنوز هیچ آزمونی در سیستم ثبت نشده است.")
        await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
        return ConversationHandler.END

    today = jdatetime.datetime.now().strftime("%Y/%m/%d")
    active_msgs = ""
    past_msgs = ""
    
    for exam in exams:
        exam_name, exam_date, reg_end, major_req = exam
        
        # استفاده از همون تابع هوشمندی که قبلاً نوشتی
        matched_jobs = get_matched_jobs_for_user(search_deg, search_maj, major_req)
        
        if matched_jobs:
            jobs_list_str = "\n".join([f"      ▫️ {j}" for j in set(matched_jobs)])
            block = f"   🎓 در جایگاه های شغلی زیر مجاز است:\n{jobs_list_str}"
            
            if reg_end >= today:
                active_msgs += f"🎯 **{exam_name}**\n📅 تاریخ برگزاری: {exam_date}\n{block}\n\n"
            else:
                past_msgs += f"🏛 **{exam_name}**\n📅 تاریخ برگزاری: {exam_date}\n{block}\n\n"
                
    final_msg = f"🔍 **نتیجه جستجو برای ادمین:** {search_deg} {search_maj}\n➖➖➖➖➖➖➖➖\n\n"
    
    if active_msgs:
        final_msg += f"🟢 **آزمون‌های فعال:**\n\n{active_msgs}"
    if past_msgs:
        final_msg += f"➖➖➖➖➖➖➖➖\n📚 **آزمون‌های گذشته:**\n\n{past_msgs}"
        
    if not active_msgs and not past_msgs:
        final_msg += "❌ متاسفانه هیچ آزمونی (فعال یا گذشته) برای این مقطع و رشته یافت نشد."
        
    await update.message.reply_text(final_msg, parse_mode='Markdown')
    await update.message.reply_text("🕴 به پنل مدیریت بازگشتید:", reply_markup=get_admin_panel_keyboard())
    return ConversationHandler.END

# الف) منوی اولیه انتخاب مخاطبان هدف
async def start_smart_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 همه کاربران (ثبت‌نام شده و نشده)", callback_data="bc_tg_all")],
        [InlineKeyboardButton("✅ فقط کاربران ثبت‌نام شده", callback_data="bc_tg_reg")],
        [InlineKeyboardButton("❌ فقط کاربران ثبت‌نام نکرده", callback_data="bc_tg_unreg")],
        [InlineKeyboardButton("🎯 واجدین شرایط یک آزمون خاص", callback_data="bc_tg_exam")],
        [InlineKeyboardButton("❌ لغو عملیات", callback_data="bc_tg_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg_text = "📢 <b>به بخش ارسال پیام همگانی هوشمند خوش آمدید.</b>\n\nلطفاً گروه مخاطبین هدف خود را انتخاب کنید:"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(msg_text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(msg_text, parse_mode='HTML', reply_markup=reply_markup)

# ب) پردازش کلیک روی منوهای هدف‌گیری
async def handle_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    
    if data == "bc_tg_cancel":
        context.user_data.clear()
        await query.message.edit_text("❌ عملیات ارسال همگانی لغو شد.")
        return

    if data in ["bc_tg_all", "bc_tg_reg", "bc_tg_unreg"]:
        context.user_data['bc_target'] = data
        context.user_data['admin_state'] = 'WAITING_FOR_BC_MSG'
        await query.message.edit_text("📥 لطفاً پیام خود را ارسال کنید.\n*(این پیام می‌تواند متن خالی، بنر عکس‌دار، فیلم یا فایل به همراه کپشن باشد)*")
        return
        
    if data == "bc_tg_exam":
        context.user_data['bc_target'] = 'bc_tg_exam'
        # واکشی آخرین آزمون‌های ثبت شده برای انتخاب آزمون هدف
        async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT id, name FROM exams ORDER BY id DESC LIMIT 10")
            exams = await cursor.fetchall()
        
        if not exams:
            await query.message.edit_text("❌ هیچ آزمونی در دیتابیس جهت فیلتر یافت نشد.")
            return
            
        keyboard = []
        for e_id, e_name in exams:
            keyboard.append([InlineKeyboardButton(f"📝 {e_name}", callback_data=f"bc_ex_{e_id}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="bc_tg_back")])
        
        await query.message.edit_text("🎯 آزمون مورد نظر را انتخاب کنید تا پیام فقط به واجدین شرایط آن آزمون ارسال شود:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
        
    if data.startswith("bc_ex_"):
        exam_id = int(data.split("_")[2])
        context.user_data['bc_exam_id'] = exam_id
        context.user_data['admin_state'] = 'WAITING_FOR_BC_MSG'
        await query.message.edit_text("📥 لطفاً پیام خود را ارسال کنید.\n*(پیام شما به صورت هوشمند فقط برای واجدین شرایط این آزمون فیلتر و ارسال خواهد شد)*")
        return
        
    if data == "bc_tg_back":
        await start_smart_broadcast(update, context)
        return

# ج) دریافت محتوای پیام از ادمین و شبیه‌سازی پیش‌نمایش (تست زنده قبل از ارسال نهایی)
async def receive_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['bc_msg_id'] = update.message.message_id
    context.user_data['bc_chat_id'] = update.message.chat_id
    context.user_data['admin_state'] = 'WAITING_FOR_BC_CONFIRM'
    
    # تغییر کوچک: به جای edit_text از send_message استفاده می‌کنیم تا ارور "Message is not modified" پیش نیاید
    await update.message.reply_text("🔍 <b>پیش‌نمایش زنده پیام شما:</b>", parse_mode='HTML')
    
    # کپی کردن پیام ادمین برای خودش
    await context.bot.copy_message(
        chat_id=update.message.chat_id,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 تایید و ارسال همگانی هوشمند", callback_data="bc_confirm_send")],
        [InlineKeyboardButton("❌ لغو و انصراف", callback_data="bc_tg_cancel")]
    ]
    # استفاده از reply_markup برای دکمه‌های تایید
    await update.message.reply_text("👀 اگر قالب و ظاهر پیام بالا مورد تایید است، دکمه تایید را بزنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    
# د) استخراج دیتابیس و پردازش فیلترها به همراه ارسال پس‌زمینه (Async Task)
async def finalize_smart_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target = context.user_data.get('bc_target')
    msg_id = context.user_data.get('bc_msg_id')
    from_chat_id = context.user_data.get('bc_chat_id')
    
    if not target or not msg_id:
        await query.message.edit_text("❌ خطا در بازیابی اطلاعات پیام.")
        return
        
    await query.message.edit_text("⏳ در حال استخراج لیست کاربران هدف... فرآیند ارسال تا لحظاتی دیگر در پس‌زمینه آغاز می‌شود.")
    
    user_ids = []
    
    async with aiosqlite.connect('recruitment.db', timeout=30) as conn:
        cursor = await conn.cursor()
        
        if target == "bc_tg_all":
            await cursor.execute("SELECT user_id FROM active_sessions")
            user_ids = [r[0] for r in await cursor.fetchall()]
            
        elif target == "bc_tg_reg":
            await cursor.execute("SELECT DISTINCT user_id FROM users")
            user_ids = [r[0] for r in await cursor.fetchall()]
            
        elif target == "bc_tg_unreg":
            await cursor.execute("SELECT user_id FROM active_sessions WHERE user_id NOT IN (SELECT user_id FROM users)")
            user_ids = [r[0] for r in await cursor.fetchall()]
            
        elif target == "bc_tg_exam":
            exam_id = context.user_data.get('bc_exam_id')
            await cursor.execute("SELECT name, exam_date, min_age, max_age, major_req FROM exams WHERE id = ?", (exam_id,))
            exam_row = await cursor.fetchone()
            
            if exam_row:
                e_name, full_date, e_min, e_max, final_req_json = exam_row
                await cursor.execute('''
                    SELECT u.user_id, u.b_year, u.b_month, u.b_day, u.is_married, u.children_count, ud.degree, ud.major 
                    FROM users u INNER JOIN user_degrees ud ON u.user_id = ud.user_id
                ''')
                users_with_degrees = await cursor.fetchall()
                
                # اعمال دقیق منطق تطبیق ربات شما بدون کوچک‌ترین تغییر
                has_bonus = True
                try:
                    req_data = json.loads(final_req_json)
                    has_bonus = req_data.get('has_bonus', True)
                except: pass
                
                user_profiles = {}
                for row in users_with_degrees:
                    u_id, b_year, b_month, b_day, is_married, children_count, deg, maj = row
                    if u_id not in user_profiles:
                        user_profiles[u_id] = {'b_year': b_year, 'b_month': b_month, 'b_day': b_day, 'is_married': is_married, 'children_count': children_count, 'degrees': []}
                    user_profiles[u_id]['degrees'].append((deg, maj))
                    
                for u_id, profile in user_profiles.items():
                    age = calculate_age_at_exam(profile['b_year'], profile['b_month'], profile['b_day'], full_date)
                    bonus = (min((1 if profile['is_married'] else 0) + profile['children_count'], 5)) if has_bonus else 0
                    eff_age = age - bonus
                    
                    is_completely_valid = False
                    for deg, maj in profile['degrees']:
                        if check_eligibility(deg, maj, final_req_json):
                            u_deg_norm = normalize_text(deg)
                            specific_min, specific_max = e_min, e_max
                            try:
                                req_data = json.loads(final_req_json)
                                for item in req_data.get('items', []):
                                    if normalize_text(item.get('degree', '')) in ['همه', u_deg_norm]:
                                        specific_min = item.get('min_age', e_min)
                                        specific_max = item.get('max_age', e_max)
                                        break
                            except: pass
                            
                            if specific_min <= eff_age <= specific_max:
                                is_completely_valid = True
                                break
                    
                    if is_completely_valid:
                        user_ids.append(u_id)

    user_ids = list(set(user_ids))
    if not user_ids:
        await query.message.reply_text("❌ هیچ کاربری واجد این شرایط یافت نشد.")
        context.user_data.clear()
        return
        
    # اجرای تسک در پس‌زمینه بدون بلاک شدن ربات
    asyncio.create_task(execute_blast_task(context, user_ids, from_chat_id, msg_id))
    context.user_data.clear()

# ه) تسک ناهمگام برای ارسال پیام و مدیریت Anti-Flood تلگرام
async def execute_blast_task(context, user_ids, from_chat_id, msg_id):
    count_success = 0
    for u_id in user_ids:
        try:
            await context.bot.copy_message(chat_id=u_id, from_chat_id=from_chat_id, message_id=msg_id)
            count_success += 1
            await asyncio.sleep(0.05)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                await context.bot.copy_message(chat_id=u_id, from_chat_id=from_chat_id, message_id=msg_id)
                count_success += 1
            except: pass
        except: pass
            
    try:
        await context.bot.send_message(ADMIN_IDS[0], f"📢 <b>گزارش ارسال همگانی هوشمند:</b>\n\n✅ پیام شما با موفقیت به {count_success} کاربر از کل {len(user_ids)} کاربر هدف ارسال شد.", parse_mode='HTML')
    except: pass

async def blast_tutorial_task(context, users, tutorial):
    t_type, content, caption = tutorial
    
    # متنی که زیر کلیپ قرار می‌گیرد تا کاربر را ترغیب کند
    text = (
        "رفیق، دیدم ربات رو استارت زدی اما هنوز ثبت‌نامت رو کامل نکردی! 😅\n\n"
        "اینطوری من نمیتونم آزمون های مناسب رشته ت رو برات بفرستم، "
        "پس همین الان کلیپ آموزش ثبت نام رو ببین بعدش روی دکمه زیر کلیک کن 👇"
    )
    
    # دکمه شیشه‌ای ثبت‌نام که به سیستم فعلی رباتت متصل است
    kb = [[InlineKeyboardButton("✅ شروع ثبت‌نام", callback_data='start_register_skip_video')]]
    reply_markup = InlineKeyboardMarkup(kb)

    count_success = 0
    for u in users:
        user_id = u[0]
        try:
            if t_type == 'photo':
                await context.bot.send_photo(chat_id=user_id, photo=content, caption=text, reply_markup=reply_markup)
            elif t_type == 'video':
                await context.bot.send_video(chat_id=user_id, video=content, caption=text, reply_markup=reply_markup)
            else:
                await context.bot.send_message(chat_id=user_id, text=f"{content}\n\n{text}", reply_markup=reply_markup)
            
            count_success += 1
            await asyncio.sleep(0.05) # جلوگیری از بلاک شدن توسط تلگرام
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except Exception:
            pass

    # ارسال گزارش نهایی به ادمین
    try:
        await context.bot.send_message(
            ADMIN_IDS[0],
            f"✅ **عملیات موفق:**\nکلیپ آموزش و دعوت به ثبت‌نام به {count_success} کاربر که ثبت‌نام نکرده بودند، ارسال شد.",
            parse_mode='Markdown'
        )
    except:
        pass

# ================= اجرای ربات =================
if __name__ == '__main__':
    init_db()
    upgrade_db() 
    
    req = HTTPXRequest(
        connection_pool_size=100, 
        pool_timeout=30.0, 
        read_timeout=30.0, 
        write_timeout=30.0, 
        connect_timeout=30.0, 
        httpx_kwargs={"trust_env": False}
    )
    app = ApplicationBuilder().token(TOKEN).request(req).get_updates_request(req).build()

    app.add_handler(TypeHandler(Update, track_user_activity), group=-1)

    app.add_handler(CommandHandler('admin', admin_command))
    
    admin_search_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_start_search, pattern='^admin_search_start$')],
        states={
            ADMIN_SEARCH_DEGREE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_search_degree)],
            ADMIN_SEARCH_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_search_major)]
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('admin', admin_command), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    
    booklet_upload_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_upload_booklet_flow, pattern='^admin_select_exam_for_booklet$')],
        states={ADMIN_UPLOAD_EXAM_BOOKLET: [CallbackQueryHandler(receive_exam_booklet_file, pattern='^booklet_target_'), MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), receive_exam_booklet_file)]},
        fallbacks=[CommandHandler('start', start), CommandHandler('admin', admin_command), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    app.add_handler(booklet_upload_handler)
    app.add_handler(admin_search_handler)
    
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # هندلر اضافه کردن آزمون (اکسل)
    # ---------------------------------------------------------
    # هندلر اضافه کردن آزمون (اکسل)
    exam_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_exam_flow, pattern='^admin_add_exam$')], # 🟢 مشکل اینجا بود که اصلاح شد
        states={
            EXAM_EXCEL_UPLOAD: [MessageHandler(filters.Document.ALL | filters.TEXT, receive_exam_excel)],
            EXAM_CONFIRM_FINAL: [CallbackQueryHandler(finalize_exam_send, pattern='^(confirm_send|confirm_send_silent|cancel_send)$')]
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('admin', admin_command), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    # ---------------------------------------------------------
    # ---------------------------------------------------------
        
    app.add_handler(exam_handler)
    
    broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern='^admin_broadcast_start$')],
        states={
            ADMIN_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast_msg)]
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    app.add_handler(broadcast_handler)

    tutorial_handler = ConversationHandler(
        # 🟢 این خط تغییر کرده است:
        entry_points=[CallbackQueryHandler(start_set_tutorial, pattern='^admin_set_')],
        states={
            ADMIN_SET_TUTORIAL_MSG: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, receive_tutorial_msg)]
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    app.add_handler(tutorial_handler)

    upcoming_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_upcoming_flow, pattern='^admin_add_upcoming$')],
        states={
            UPCOMING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_upcoming_name)],
            UPCOMING_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_upcoming_desc)],
            UPCOMING_VOICE: [MessageHandler(filters.VOICE, receive_upcoming_voice)]
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    app.add_handler(upcoming_handler)

    user_excel_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_user_excel_edit_flow, pattern='^admin_edit_users_excel$')],
        states={
            ADMIN_USER_EXCEL_UPLOAD: [MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), receive_user_edit_excel)]
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('admin', admin_command), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    app.add_handler(user_excel_edit_handler)

    app.add_handler(CallbackQueryHandler(close_panel_cb, pattern='^close_panel$'))
    
    pdf_upload_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_upload_pdf_flow, pattern='^admin_select_exam_for_pdf$')],
        states={ADMIN_UPLOAD_EXAM_PDF: [CallbackQueryHandler(receive_exam_pdf_file, pattern='^pdf_target_'), MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), receive_exam_pdf_file)]},
        fallbacks=[CommandHandler('start', start), CommandHandler('admin', admin_command), MessageHandler(filters.Regex(f'^{ADMIN_BACK_BTN}$'), back_to_admin_panel_msg)],
        allow_reentry=True
    )
    app.add_handler(pdf_upload_handler)

    reg_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_edit_process, pattern='^start_register$'),
            CallbackQueryHandler(start_edit_process, pattern='^edit_profile$'),
            CallbackQueryHandler(start_edit_process, pattern='^start_direct_registration$'),
            CallbackQueryHandler(start_edit_process, pattern='^start_register_skip_video$')
        ],
        states={
            WAIT_FOR_VIDEO: [
                CallbackQueryHandler(check_video_lock, pattern='^video_watched$')
            ],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, receive_phone)],
            # بقیه وضعیت‌ها همون‌طور که خودت نوشتی سر جاشون بمونن...
            B_YEAR: [MessageHandler(filters.TEXT, receive_year)],
            B_MONTH: [MessageHandler(filters.TEXT, receive_month)],
            B_DAY: [MessageHandler(filters.TEXT, receive_day)],
            MARITAL_STATUS: [
                CallbackQueryHandler(receive_marital_inline),
                MessageHandler(filters.Regex(f'^{BACK_BTN}$'), cancel)
            ],
            CHILDREN_COUNT: [
                CallbackQueryHandler(receive_children_inline),
                MessageHandler(filters.Regex(f'^{BACK_BTN}$'), cancel)
            ],
            DEGREE: [
                CallbackQueryHandler(receive_degree_inline),
                MessageHandler(filters.Regex(f'^{BACK_BTN}$'), cancel)
            ],
            DEGREE_SUB: [
                CallbackQueryHandler(receive_degree_sub_inline),
                MessageHandler(filters.Regex(f'^{BACK_BTN}$'), cancel)
            ],
            MAJOR: [MessageHandler(filters.TEXT, receive_major)],
            ASK_MORE_DEGREES: [
                CallbackQueryHandler(receive_more_degrees_choice),
                MessageHandler(filters.Regex(f'^{BACK_BTN}$'), cancel)
            ]
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('cancel', cancel), MessageHandler(filters.Regex(f'^{BACK_BTN}$'), cancel)],
        allow_reentry=True,
        persistent=False
    )

    app.add_handler(reg_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, main_menu_text_handler))
    app.add_handler(CallbackQueryHandler(inline_handler))

    print("✅ System Optimized for Production: Async SQLite & WAL Mode Enabled!")
    print("🚀 Logic & Registration updated flawlessly with Multi-Degree Support!")
    
    try: 
        app.run_polling(close_loop=False)
    except RuntimeError as e:
        if "Cannot close a running event loop" not in str(e): 
            raise e