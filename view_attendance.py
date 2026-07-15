import sqlite3

def view_logs():
    # 1. เชื่อมต่อกับไฟล์ฐานข้อมูลดิจิทัลที่สร้างไว้
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # 2. ใช้คำสั่ง SQL ดึงข้อมูลประวัติการบันทึกเวลาทั้งหมด เรียงจากล่าสุดขึ้นก่อน
    cursor.execute("""
        SELECT id, student_id, timestamp 
        FROM attendance_logs 
        ORDER BY timestamp DESC
    """)
    
    rows = cursor.fetchall()
    
    # 3. แสดงผลลัพธ์ออกมาทางหน้าจอ Terminal
    print("\n" + "="*50)
    print(" รายงานประวัติการบันทึกเวลาเรียน (Time Attendance Logs)")
    print("="*50)
    print(f"{'ลำดับ':<6}{'รหัสนักเรียน':<15}{'วัน-เวลาที่สแกนสำเร็จ'}")
    print("-"*50)
    
    if not rows:
        print("ยังไม่มีประวัติการบันทึกเวลาในระบบ")
    else:
        for row in rows:
            print(f"{row[0]:<6}{row[1]:<15}{row[2]}")
            
    print("="*50 + "\n")
    conn.close()

if __name__ == "__main__":
    view_logs()