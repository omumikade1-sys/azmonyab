import sqlite3
import pandas as pd

# خواندن فایل اکسل
df = pd.read_excel('questions.xlsx')
correct_map = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', 'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd'}

conn = sqlite3.connect('recruitment.db')
cursor = conn.cursor()

# ساخت جدول سوالات در دیتابیس (اگر وجود نداشته باشد)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL,
        day_number INTEGER DEFAULT 1
    )
''')

# وارد کردن سوالات
for index, row in df.iterrows():
    day_num = (index // 5) + 1  # هر ۵ سوال برای یک روز
    raw_correct = str(row['پاسخ صحیح']).split('.')[0].strip().lower()
    correct_opt = correct_map.get(raw_correct, raw_correct)
    
    cursor.execute('''
        INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option, day_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(row['متن سوال']),
        str(row['گزینه 1']),
        str(row['گزینه 2']),
        str(row['گزینه 3']),
        str(row['گزینه 4']),
        correct_opt,
        day_num
    ))

conn.commit()
conn.close()
print("✅ تمام سوالات اکسل با موفقیت وارد دیتابیس شدند!")