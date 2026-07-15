import sqlite3

def fix_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    # ดึงโครงสร้างตารางมาเช็ค
    cursor.execute("PRAGMA table_info(students)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # เพิ่มคอลัมน์ที่ขาดไป
    if 'department' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN department TEXT")
    if 'room' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN room TEXT")
        
    conn.commit()
    conn.close()
    print("Database updated successfully!")

if __name__ == '__main__':
    fix_db()