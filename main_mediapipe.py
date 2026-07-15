import cv2
import mediapipe as mp
import time
from database import log_attendance

# 1. ตั้งค่า MediaPipe
mp_face_detection = mp.solutions.face_detection
video_capture = cv2.VideoCapture(0)

# 2. ปรับการเก็บข้อมูล (ใช้ Dictionary เพื่อเก็บเวลาล่าสุดที่สแกนแทนการใช้ Set)
last_scanned = {} 
SCAN_COOLDOWN = 60 # ให้สแกนซ้ำได้ทุก 60 วินาที เพื่อป้องกันบันทึกซ้ำรัวๆ

print("เปิดระบบ MediaPipe เรียบร้อย...")

with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
    try:
        while True:
            ret, frame = video_capture.read()
            if not ret: break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if results.detections:
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
                    
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # --- ส่วนที่เพิ่ม: ระบบเช็คเวลาสแกนซ้ำ ---
                    student_id = "ปวช-001" 
                    current_time = time.time()
                    
                    if student_id not in last_scanned or (current_time - last_scanned[student_id] > SCAN_COOLDOWN):
                        log_attendance(student_id)
                        last_scanned[student_id] = current_time
                        cv2.putText(frame, "SAVED!", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                    cv2.putText(frame, student_id, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow('Face Scanner', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
        # เคลียร์ทรัพยากรทุกครั้งไม่ว่าจะเกิดอะไรขึ้น
        video_capture.release()
        cv2.destroyAllWindows()