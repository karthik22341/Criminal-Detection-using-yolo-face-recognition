from ultralytics import YOLO
import threading
import cv2
import face_compare
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import sqlite3
import numpy as np
import uuid

path = ''

conn = sqlite3.connect(path + 'database.sqlite')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS criminals (id INTEGER PRIMARY KEY, encoding TEXT, name VARCHAR2(255), image_path TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, criminal_id INTEGER, camera_id INTEGER, timestamp TEXT, image TEXT, FOREIGN KEY(criminal_id) REFERENCES criminals(id) ON DELETE CASCADE)')
c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name VARCHAR2(255), email VARCHAR2(255), password TEXT, token VARCHAR2(100) NULL, role VARCHAR2(10))')
users = c.execute('SELECT * FROM users WHERE role = "admin"').fetchall()
if len(users) == 0:
    c.execute('INSERT INTO users (name, email, password, role) VALUES ("Admin", "admin@gmail.com", "admin", "admin")')
conn.commit()
c.close()
conn.close()

app = Flask(__name__)
CORS(app)
index = 0
trackers = []
thread = []
shape = (640, 480)
nocam = cv2.imread(path + 'nocamera.png')

class Tracker:
    def __init__(self, camera_id, frameShape) -> None:
        self.camera_id = camera_id
        self.cam_reader = cv2.VideoCapture(camera_id)
        self.frame = None
        self.anotatedFrame = None
        self.model = YOLO('yolov8s.pt')
        self.frameName = f'Camera {camera_id}'
        self.frameShape = frameShape
        self.ids = {}
    
    def track(self):
        anotatedFrame = self.frame.copy()
        results = self.model.track(self.frame, persist=True, conf=0.6, iou=0.5, verbose=False, classes = (0,))[0]
        for i in results.summary():
            try:
                x1, y1, x2, y2 = int(i['box']['x1']), int(i['box']['y1']), int(i['box']['x2']), int(i['box']['y2'])
                if self.ids.get(i['track_id'], None) == None:
                    self.ids[i['track_id']] = face_compare.compareFaces(self.frame[y1:y2, x1:x2].copy(), self.camera_id)
                if self.ids.get(i['track_id'], None) and self.ids.get(i['track_id'], None)[0] != 0:
                    cv2.rectangle(anotatedFrame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(anotatedFrame, self.ids[i['track_id']][1], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            except KeyError:
                pass
        return anotatedFrame

    def destroyFrame(self):
        self.frame = None
        try:
            self.cam_reader.release()
            cv2.destroyWindow(self.frameName)
        except:
            pass

    def run(self):
        while self.cam_reader.isOpened():
            success, frame = self.cam_reader.read()

            if success:
                self.frame = cv2.resize(frame, self.frameShape)
                self.frame = cv2.flip(self.frame, 2)
                self.anotatedFrame = self.track()
                cv2.imshow(self.frameName, self.anotatedFrame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.destroyFrame()
                    return 1
            else:
                break
        self.destroyFrame()
        return 0
    
    def generate_frames(self):
        while self.frame is not None:
            _, buffer = cv2.imencode('.jpg', self.anotatedFrame)

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        _, buffer = cv2.imencode('.jpg', nocam)
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def main():
    global index
    while True:
        cam = cv2.VideoCapture(index)
        if cam.isOpened():
            cam.release()
            trackers.append(Tracker(index, shape))
        else:
            break
        index += 1
    # trackers.append(Tracker(0, shape))
    print(trackers)
    for i in trackers:
        t = threading.Thread(target = i.run)
        thread.append(t)
        t.start()
    app.run(debug=True)
    for i in thread:
        i.join()
    conn.close()

@app.route('/api/video_feed/<int:id>')
def video_feed(id):
    if 0 <= id < len(trackers):
        return Response(trackers[id].generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return "No feed found"

@app.route("/api/login", methods=['POST'])
def login():
    try:
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(path + 'database.sqlite')
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        if user:
            token = str(uuid.uuid4())
            id = user[0]
            c.execute('UPDATE users SET token = ? WHERE email = ?', (token, email))
            conn.commit()
            c.close()
            conn.close()
            print(token, id)
            return jsonify({'message': 'Login successful', 'status': 'success', 'token': token, "id":id}), 200
        print('Invalid credentials')
        c.close()
        conn.close()
        return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 400
    except Exception as e:
        print(e)
        return jsonify({'message': str(e), 'status': 'failed'}), 400

@app.route("/api/dashboard", methods=['POST'])
def dashboards():
    try:
        id = request.form['id']
        token = request.form['token']
        conn = sqlite3.connect(path + 'database.sqlite')
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE id = ? AND token = ?', (id, token)).fetchone()
        if user:
            camCount = len(trackers)
            criminalCount = c.execute('SELECT COUNT(*) FROM criminals').fetchone()[0]
            c.close()
            conn.close()
            return jsonify({'camCount': camCount, 'criminalCount': criminalCount, 'user': user, 'status': 'success'}), 200
        c.close()
        conn.close()
        return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 400
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'failed'}), 400

@app.route("/api/logs", methods=['POST'])
def logs():
    try:
        id = request.form['id']
        token = request.form['token']
        conn = sqlite3.connect(path + 'database.sqlite')
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE id = ? AND token = ?', (id, token)).fetchone()
        if user:
            logs = c.execute('SELECT c.name as name, l.camera_id as camid, c.image_path as path, l.image as image, l.timestamp as time from logs l, criminals c where l.criminal_id == c.id').fetchall()
            c.close()
            conn.close()
            return jsonify({'logs': logs, 'user': user, 'status': 'success'}), 200
        c.close()
        conn.close()
        return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 400
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'failed'}), 400

@app.route("/api/add_criminal", methods=['POST'])
def add_criminal():
    id = request.form['id']
    token = request.form['token']
    conn = sqlite3.connect(path + 'database.sqlite')
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ? AND token = ?', (id, token)).fetchone()
    if user:
        if not request.files.get('image'):
            c.close()
            conn.close()
            return jsonify({'message': 'No image found', 'status': 'failed'}), 400
        image = cv2.imdecode(np.frombuffer(request.files['image'].read(), np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            c.close()
            conn.close()
            return jsonify({'message': 'Invalid image', 'status': 'failed'}), 400
        name = request.form['name']
        message, status = face_compare.getEncodings(image, name)
        if status:
            criminals = c.execute('SELECT id, name, image_path FROM criminals').fetchall()
            c.close()
            conn.close()
            return jsonify({'message': message, 'criminals': criminals, 'status': 'success'}), 200
        return jsonify({'message': message, 'status': 'failed'}), 400
    return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 400

@app.route('/api/get_criminals', methods=['POST'])
def get_criminals():
    try:
        id = request.form['id']
        token = request.form['token']
        conn = sqlite3.connect(path + 'database.sqlite')
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE id = ? AND token = ?', (id, token)).fetchone()
        if user:
            criminals = c.execute('SELECT id, name, image_path FROM criminals').fetchall()
            c.close()
            conn.close()
            return jsonify({'criminals': criminals, 'user': user, 'status': 'success'}), 200
        c.close()
        conn.close()
        return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 400
    except Exception as e:
        return jsonify({'message' : str(e), 'status' : 'failed'}), 400

@app.route("/api/getCamCount")
def getCamCount():
    return jsonify({'count': len(trackers)})

@app.route("/api/add_user", methods=['POST'])
def add_user():
    user_id = request.form['id']
    token = request.form['token']
    conn = sqlite3.connect(path + 'database.sqlite')
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ? AND token = ?', (user_id, token)).fetchone()
    if user and user[5] == 'admin':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        c.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', (name, email, password, role))
        conn.commit()
        c.close()
        conn.close()
        return jsonify({'message': 'User added successfully', 'status': 'success'}), 200
    c.close()
    conn.close()
    return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 400

@app.route("/api/logout", methods=['POST'])
def logout():
    token = request.form['token']
    conn = sqlite3.connect(path + 'database.sqlite')
    c = conn.cursor()
    c.execute('UPDATE users SET token = NULL WHERE token = ?', (token,))
    conn.commit()
    c.close()
    conn.close()
    return jsonify({'message': 'Logout successful', 'status': 'success'}), 200
    
if __name__ == '__main__':
    main()