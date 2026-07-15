import sqlite3

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

# ตารางนักเรียน (ของเดิม)
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class_group TEXT NOT NULL, 
    pdpa_consent INTEGER DEFAULT 1
)
''')

# ตารางประวัติการเข้าเรียน (ของเดิม)
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students (student_id)
)
''')

# 📌 เพิ่มใหม่: ตารางเก็บข้อมูลคุณครู/แอดมิน
cursor.execute('''
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    department TEXT NOT NULL
)
''')

conn.commit()
conn.close()

print("✔️ อัปเดตฐานข้อมูล เพิ่มตารางคุณครูสำเร็จ!")