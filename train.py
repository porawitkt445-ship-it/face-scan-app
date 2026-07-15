import cv2
import os
import numpy as np
import pickle
from PIL import Image

IMAGE_DIR = "img"
# ใช้ Haar Cascade ตัวมาตรฐาน
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

label_ids = {}
y_labels = []
x_train = []
current_id = 0

print("⏳ กำลังเตรียมสอน AI โปรดรอสักครู่...")

if not os.path.exists(IMAGE_DIR):
    print(f"❌ ไม่พบโฟลเดอร์ {IMAGE_DIR}")
    exit()

for file in os.listdir(IMAGE_DIR):
    if file.lower().endswith((".png", ".jpg", ".jpeg")):
        path = os.path.join(IMAGE_DIR, file)
        student_id = os.path.splitext(file)[0]
        
        if student_id not in label_ids.values():
            label_ids[current_id] = student_id
            current_id += 1
        
        id_ = [k for k, v in label_ids.items() if v == student_id][0]
        
        # 1. โหลดรูปและแปลงเป็น Grayscale
        pil_image = Image.open(path).convert("L")
        image_array = np.array(pil_image, "uint8")
        
        # 2. ปรับสมดุลแสง (Histogram Equalization) ช่วยให้ AI เห็นรายละเอียดหน้าชัดขึ้น
        image_array = cv2.equalizeHist(image_array)
        
        # 3. ค้นหาใบหน้า (ปรับ scaleFactor และ minNeighbors ให้เหมาะสม)
        faces = face_cascade.detectMultiScale(image_array, scaleFactor=1.1, minNeighbors=4)
        
        for (x, y, w, h) in faces:
            roi = image_array[y:y+h, x:x+w]
            x_train.append(roi)
            y_labels.append(id_)

if len(x_train) > 0:
    # เริ่มการสอน AI
    recognizer.train(x_train, np.array(y_labels))
    recognizer.save("trainer.yml")
    
    # บันทึก label_ids
    with open("labels.pkl", "wb") as f:
        pickle.dump(label_ids, f)
        
    print(f"✔️ สอน AI เสร็จสิ้น! จำใบหน้าได้ {len(np.unique(y_labels))} คน")
else:
    print("❌ ไม่พบใบหน้าในรูปภาพ! ตรวจสอบว่ารูปในโฟลเดอร์ img มีใบหน้าคนชัดเจนและไม่เอียงจนเกินไป")