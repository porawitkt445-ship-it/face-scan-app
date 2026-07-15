from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
import sqlite3, cv2, os, numpy as np, base64, pickle, time
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = 'super_secret_key' 

UPLOAD_FOLDER = 'img'
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

# ตัวแปรระดับ Global สำหรับจัดการการสลับกล้องอัตโนมัติ
LAST_MOBILE_SEEN = 0.0
MOBILE_TIMEOUT = 4.0

# ฟังก์ชันจัดการฐานข้อมูล
def init_db():
    conn = sqlite3.connect("attendance.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS students (student_id TEXT PRIMARY KEY, name TEXT, department TEXT, room TEXT, class_group TEXT, pdpa_consent INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS attendance_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
init_db()

def connect_db(): return sqlite3.connect("attendance.db")

# ระบบ AI
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
is_ai_ready = False
labels = {}

def load_ai_model():
    global is_ai_ready, labels
    if os.path.exists("trainer.yml") and os.path.exists("labels.pkl"):
        recognizer.read("trainer.yml")
        with open("labels.pkl", "rb") as f: labels = pickle.load(f)
        is_ai_ready = True
load_ai_model()

def train_ai_auto():
    label_ids, y_labels, x_train, current_id = {}, [], [], 0
    for file in os.listdir(UPLOAD_FOLDER):
        if file.lower().endswith((".jpg", ".png")):
            student_id = os.path.splitext(file)[0]
            if student_id not in label_ids.values(): 
                label_ids[current_id] = student_id
                current_id += 1
            id_ = [k for k, v in label_ids.items() if v == student_id][0]
            img = Image.open(os.path.join(UPLOAD_FOLDER, file)).convert("L")
            faces = face_cascade.detectMultiScale(np.array(img, "uint8"), 1.1, 4)
            for (x, y, w, h) in faces: 
                x_train.append(np.array(img, "uint8")[y:y+h, x:x+w])
                y_labels.append(id_)
    if x_train:
        recognizer.train(x_train, np.array(y_labels))
        recognizer.save("trainer.yml")
        with open("labels.pkl", "wb") as f: pickle.dump(label_ids, f)

# ระบบป้องกันการสแกนซ้ำ (Anti-Spam Cooldown)
scanned_students = {}
SCAN_COOLDOWN = 300 

def log_attendance(student_id):
    current_time = time.time()
    if student_id in scanned_students:
        if current_time - scanned_students[student_id] < SCAN_COOLDOWN:
            return 
            
    try:
        conn = connect_db()
        cur = conn.execute("SELECT COUNT(*) FROM attendance_logs WHERE student_id = ? AND date(timestamp) = date('now', 'localtime')", (student_id,))
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO attendance_logs (student_id) VALUES (?)", (student_id,))
            conn.commit()
            scanned_students[student_id] = current_time
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# ระบบประมวลผลกล้อง
def generate_frames():
    global LAST_MOBILE_SEEN
    camera = None
    try:
        while True:
            is_mobile_active = (time.time() - LAST_MOBILE_SEEN) < MOBILE_TIMEOUT
            if is_mobile_active:
                if camera is not None and camera.isOpened():
                    camera.release()
                    camera = None
                blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank_frame, "KT Network Mobile Active...", (90, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
                _, buffer = cv2.imencode('.jpg', blank_frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.5)
                continue
            if camera is None or not camera.isOpened():
                camera = cv2.VideoCapture(0)
            success, frame = camera.read()
            if not success: continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5)
            for (x, y, w, h) in faces:
                student_id = "Unknown"
                if is_ai_ready:
                    id_, conf = recognizer.predict(gray[y:y+h, x:x+w])
                    if conf < 100: student_id = labels.get(id_, "Unknown")
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, student_id, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                if student_id != "Unknown": log_attendance(student_id)
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally: 
        if camera is not None and camera.isOpened(): camera.release()

# ระบบรับภาพจากกล้องมือถือ
@app.route('/api/process-frame', methods=['POST'])
def process_frame():
    global LAST_MOBILE_SEEN
    try:
        LAST_MOBILE_SEEN = time.time()
        data = request.json
        header, encoded = data['image'].split(",", 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        student_id = "Unknown"
        if is_ai_ready and len(faces) > 0:
            for (x, y, w, h) in faces:
                id_, conf = recognizer.predict(gray[y:y+h, x:x+w])
                if conf < 100: 
                    student_id = labels.get(id_, "Unknown")
                    if student_id != "Unknown":
                        log_attendance(student_id)
                        break
        return jsonify({"student_id": student_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/')
def home(): return redirect(url_for('login_page'))
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST': session['department'] = request.form.get('department', 'ไม่ระบุ'); return redirect(url_for('index'))
    return render_template('login.html')
@app.route('/dashboard')
def index(): return render_template('index.html', department=session.get('department', 'ไม่ระบุ'))
@app.route('/register')
def register_page(): return render_template('register.html')
@app.route('/report')
def report_page(): return render_template('report.html')
@app.route('/scan')
def scan_page(): return render_template('scan.html')
@app.route('/scan_mobile')
def scan_mobile_page(): return render_template('scan_mobile.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    conn = connect_db()
    conn.execute("REPLACE INTO students VALUES (?, ?, ?, ?, ?, 1)", (data['student_id'], data['name'], data['department'], data['room'], data['class_group']))
    conn.commit(); conn.close()
    with open(f"img/{data['student_id']}.jpg", "wb") as f: f.write(base64.b64decode(data['image'].split(",")[1]))
    train_ai_auto(); load_ai_model()
    return jsonify({"status": "success"})

# ✅ แก้ไขตรงนี้: เพิ่ม id และปรับ Format วันเดือนปี
@app.route('/api/attendance-logs')
def get_logs():
    conn = connect_db()
    rows = conn.execute("""
        SELECT l.id, l.student_id, s.name, s.department, s.room, strftime('%d/%m/%Y %H:%M', l.timestamp, 'localtime') 
        FROM attendance_logs l 
        LEFT JOIN students s ON l.student_id = s.student_id 
        ORDER BY l.timestamp DESC
    """).fetchall()
    conn.close()
    return jsonify([{"id": r[0], "student_id": r[1], "name": r[2], "department": r[3], "room": r[4], "timestamp": r[5]} for r in rows])

@app.route('/api/absent-students')
def get_absent_students():
    conn = connect_db()
    rows = conn.execute("SELECT student_id, name, department, room FROM students WHERE student_id NOT IN (SELECT student_id FROM attendance_logs WHERE date(timestamp) = date('now', 'localtime'))").fetchall()
    conn.close()
    # ใส่ id: null กลับไปให้หน้า report ไม่ Error เวลาอ่านข้อมูล
    return jsonify([{"id": None, "student_id": r[0], "name": r[1], "department": r[2], "room": r[3]} for r in rows])

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/delete-student/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = sqlite3.connect("attendance.db")
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM attendance_logs WHERE student_id = ?", (student_id,))
        conn.commit(); conn.close()
        img_path = os.path.join(UPLOAD_FOLDER, f"{student_id}.jpg")
        if os.path.exists(img_path): os.remove(img_path)
        if student_id in scanned_students: del scanned_students[student_id]
        train_ai_auto(); load_ai_model()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 500
    
# ✅ เพิ่ม Route สำหรับลบประวัติโดยใช้ ID
@app.route('/api/delete-log/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    try:
        conn = connect_db()
        conn.execute("DELETE FROM attendance_logs WHERE id = ?", (log_id,))
        conn.commit(); conn.close()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 500

@app.route('/register_teacher')
def register_teacher_page():
    return render_template('register_teacher.html')

@app.route('/api/register_teacher', methods=['POST'])
def register_teacher():
    data = request.json
    try:
        conn = connect_db()
        conn.execute('''CREATE TABLE IF NOT EXISTS teachers 
                        (username TEXT PRIMARY KEY, password TEXT, department TEXT)''')
        conn.execute("INSERT INTO teachers VALUES (?, ?, ?)", 
                     (data['username'], data['password'], data['department']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "ลงทะเบียนครูสำเร็จ!"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username นี้มีผู้ใช้งานแล้ว"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)