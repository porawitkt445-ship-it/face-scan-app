import sqlite3

def force_update_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # ดึงรายชื่อคอลัมน์ที่มีอยู่ในปัจจุบันออกมาเช็ค
    cursor.execute("PRAGMA table_info(students)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # ถ้าไม่มีคอลัมน์ department ให้เพิ่ม
    if 'department' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN department TEXT")
        print("เพิ่มคอลัมน์ 'department' สำเร็จ")
    
    # ถ้าไม่มีคอลัมน์ room ให้เพิ่ม
    if 'room' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN room TEXT")
        print("เพิ่มคอลัมน์ 'room' สำเร็จ")
        
    conn.commit()
    conn.close()
    print("ตรวจสอบและแก้ไขฐานข้อมูลเรียบร้อยแล้ว!")

if __name__ == '__main__':
    force_update_db()