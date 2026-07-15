import sqlite3
from datetime import datetime

# 1. ฟังก์ชันเชื่อมต่อฐานข้อมูล
def connect_db():
    conn = sqlite3.connect("attendance.db")
    return conn

# 2. ฟังก์ชันสร้างตารางเก็บข้อมูล (รันครั้งแรกครั้งเดียว)
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    
    # ตารางเก็บประวัตินักเรียนและการยอมรับ PDPA
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        pdpa_consent INTEGER DEFAULT 1
    )
    """)
    
    # ตารางบันทึกเวลาเข้าเรียน (Time Attendance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (student_id)
    )
    """)
    
    conn.commit()
    conn.close()
    print("สร้างตารางฐานข้อมูลสําเร็จ!")

# 3. ฟังก์ชันบันทึกเวลาเมื่อสแกนหน้าผ่าน
def log_attendance(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    # ดึงเวลาปัจจุบันแบบเรียลไทม์
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT INTO attendance_logs (student_id, timestamp) 
    VALUES (?, ?)
    """, (student_id, current_time))
    
    conn.commit()
    conn.close()
    print(f"บันทึกเวลาสำเร็จสำหรับรหัส: {student_id} ณ เวลา {current_time}")

# ส่วนนี้คือจุดสำคัญที่จะทำงานเมื่อเราพิมพ์คำสั่งสั่งรันไฟล์นี้ตรงๆ
if __name__ == "__main__":
    create_tables()