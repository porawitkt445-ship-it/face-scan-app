import cv2
import os
import sqlite3
import numpy as np
from PIL import Image, ImageDraw, ImageFont
# นำเข้าฟังก์ชันจาก database.py
from database import log_attendance, create_tables, connect_db

# สั่งให้เช็คและสร้างฐานข้อมูลและตารางโดยอัตโนมัติทันทีที่เปิดโปรแกรม
create_tables()

# โหลดไฟล์ XML สำหรับตรวจจับใบหน้า (Haar Cascades)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# ฟังก์ชันระบบลงทะเบียน (กรอกข้อมูล + ถ่ายหน้าตรง)
def register_user():
    print("\n" + "="*40)
    print(" 📥 ระบบลงทะเบียนนักเรียน ปวช.1")
    print("="*40)
    
    # กรอกข้อมูลทาง Terminal
    student_id = input("กรอกรหัสนักเรียน : ").strip()
    name = input("กรอกชื่อ-นามสกุล: ").strip()
    
    if not student_id or not name:
        print("❌ ข้อผิดพลาด: กรุณากรอกข้อมูลให้ครบถ้วน")
        return

    print("\n[การคุ้มครองข้อมูลส่วนบุคคล (PDPA)]")
    print("โครงการนี้จะจัดเก็บข้อมูลใบหน้าและข้อมูลส่วนบุคคลเพื่อบันทึกเวลาเรียนเท่านั้น")
    consent = input("คุณยินยอมให้ระบบจัดเก็บข้อมูลใบหน้าหรือไม่? (y/n): ").strip().lower()
    
    if consent != 'y':
        print("❌ ปฏิเสธการลงทะเบียน: ผู้ใช้งานต้องให้ความยินยอมตามกฎหมาย PDPA")
        return

    # บันทึกข้อมูลประวัตินักเรียนเข้าฐานข้อมูล SQLite
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (student_id, name, pdpa_consent) 
            VALUES (?, ?, 1)
        """, (student_id, name))
        conn.commit()
        print("✔️ บันทึกข้อมูลสมาชิกลงฐานข้อมูลสำเร็จ")
    except sqlite3.IntegrityError:
        print("⚠️ รหัสนักเรียนนี้เคยลงทะเบียนไว้แล้ว จะทำการเปิดกล้องอัปเดตถ่ายรูปใหม่")
    finally:
        conn.close()

    # เปิดกล้องถ่ายภาพใบหน้า
    print("\nกำลังเปิดกล้อง... กรุณามองที่กล้องและกดปุ่ม 's' เพื่อถ่ายภาพหน้าตรง")
    cam = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cam.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        
        display_frame = frame.copy()
        for (x, y, w, h) in faces:
            # วาดกรอบสี่เหลี่ยมแนะนำตำแหน่งใบหน้า (สีน้ำเงิน)
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
        cv2.imshow("Register - Press 's' to Save Picture", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        # กด 's' เพื่อล็อกบันทึกภาพใบหน้า
        if key == ord('s'):
            if len(faces) > 0:
                img_name = f"{student_id}.jpg"
                cv2.imwrite(img_name, frame)
                print(f"✔️ บันทึกภาพใบหน้าสำเร็จและจัดเก็บเป็นไฟล์: {img_name}")
                break
            else:
                print("⚠️ ไม่พบใบหน้าในกล้อง กรุณาจัดตำแหน่งหน้าให้อยู่ในกรอบแล้วกด 's' ใหม่")
        elif key == ord('q'):
            print("❌ ยกเลิกการลงทะเบียนถ่ายภาพ")
            break
            
    cam.release()
    cv2.destroyAllWindows()


# ฟังก์ชันระบบเปิดกล้องสแกนบันทึกเวลา (แสดงภาษาไทย + ดึงชื่อจริง)
def scan_attendance():
    # โหลดฟอนต์ภาษาไทยมาตรฐานของระบบ Windows เพื่อใช้แสดงชื่อภาษาไทยบนหน้าต่างกล้อง
    try:
        font_path = "C:\\Windows\\Fonts\\tahoma.ttf"
        font = ImageFont.truetype(font_path, 20)
    except:
        font = ImageFont.load_default()

    video_capture = cv2.VideoCapture(0)
    logged_students = set()
    print("\nเปิดระบบสแกนใบหน้าสำเร็จ... กด 'q' เพื่อปิดหน้าต่างกล้อง")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, 1.1, 5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            color = (0, 255, 0) # สีเขียวแสดงผลสำเร็จและปลอดภัย
            
            # ดึงรหัสจำลองที่ตรงระบบในตัวอย่างการพัฒนาช่วงแรก
            student_id = "PWC-001" 
            student_name = "Unknown Student"
            
            # วิ่งไปค้นหาข้อมูลชื่อจริงของรหัสนี้จากคลังข้อมูล SQLite
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            result = cursor.fetchone()
            if result:
                student_name = result[0]
            conn.close()
            
            # 1. วาดกรอบสี่เหลี่ยมรอบใบหน้าด้วย OpenCV
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # 2. แปลงภาพ OpenCV (BGR) เป็นภาพ PIL Image เพื่อพิมพ์ภาษาไทย
            img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)
            
            # กำหนดคำภาษาไทยแจ้งรายละเอียดชื่อรหัสและสถานะการเช็คชื่อ
            display_text = f"{student_id} - {student_name} (เช็คชื่อแล้ว)"
            
            # วาดข้อความลงบนตำแหน่งหัวของกรอบสแกน
            draw.text((x, y - 30), display_text, font=font, fill=(0, 255, 0))
            
            # แปลงภาพกลับมาเป็น OpenCV format เพื่อแสดงผลผ่านหน้าต่างหลัก
            frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            # ส่งค่าบันทึกเวลาลงฐานข้อมูล SQLite แบบปัจจุบันทันด่วน
            if student_id not in logged_students:
                log_attendance(student_id)
                logged_students.add(student_id)

        # แสดงผลหน้าจอกล้องสแกน
        cv2.imshow('Time Attendance Face Scanner', frame)

        # กดปุ่ม 'q' บนแป้นพิมพ์เพื่อปิดหน้าต่างกล้องและกลับสู่เมนูหลัก
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


# เมนูหลักควบคุมและบริหารโครงการแอปพลิเคชัน
if __name__ == "__main__":
    while True:
        print("\n" + "=== เมนูระบบบันทึกเวลาเข้าใช้งาน ===")
        print("1. ลงทะเบียนนักเรียนใหม่ (กรอกข้อมูล + ถ่ายรูปใบหน้า)")
        print("2. เปิดระบบกล้องสแกนใบหน้าบันทึกเวลา")
        print("3. ออกจากโปรแกรม")
        choice = input("เลือกเมนู (1/2/3): ").strip()
        
        if choice == '1':
            register_user()
        elif choice == '2':
            scan_attendance()
        elif choice == '3':
            print("ปิดโปรแกรมระบบบันทึกเวลา...")
            break
        else:
            print("กรุณาเลือกเมนูให้ถูกต้อง (1, 2 หรือ 3)")