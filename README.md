# Criminal-Detection-using-yolo-face-recognition
Real-time multi-camera criminal detection system using YOLOv8 object tracking and facial recognition, served via Flask API.


# Real-Time Crowd Detection and Criminal Identification System

This project is a full-stack **real-time crowd monitoring and facial recognition system** built using:

- 🔍 **YOLOv8** for object detection
- 😎 **Face recognition** for identifying known individuals
- 🎥 **OpenCV** for video capture and processing
- 🌐 **Flask API** for backend services
- 🧠 **SQLite** for database management
- 🖥️ **Frontend (React/Vite)** for live camera views and admin dashboard

---

## 🚀 Features

- Detect and track people in **real-time video feeds**
- Identify known criminals using facial recognition
- Live video streaming via Flask and OpenCV
- Admin authentication system
- Dashboard for logs, cameras, and criminal statistics
- Multi-camera support
- Upload and manage criminal face encodings
- Modular and scalable design

---

## 🧠 Tech Stack

| Layer         | Tools Used                          |
|---------------|--------------------------------------|
| Detection     | [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) |
| Face Matching | OpenCV, custom `face_compare.py`     |
| Backend       | Flask, SQLite                        |
| Frontend      | React (Vite), HTML/CSS               |
| Database      | `database.sqlite`                    |

---

## 📁 Project Structure

CrowdDetection/
├── crowdDetection/ # React frontend
│ ├── index.html
│ ├── .eslintrc.cjs
│ ├── vite.config.js
│ ├── package.json
│ ├── package-lock.json
│ ├── public/
│ │ └── vite.svg
│ └── src/
│ ├── App.jsx
│ ├── Cam.jsx
│ ├── CamList.jsx
│ ├── Criminals.jsx
│ ├── Dashboard.jsx
│ ├── Log.jsx
│ ├── Login.jsx
│ ├── Navbar.jsx
│ ├── main.jsx
│ ├── cam.css
│ ├── camlist.css
│ ├── dashboard.css
│ ├── index.css
│ ├── log.css
│ ├── login.css
│
├── main.py # Flask backend entry point
├── face_compare.py # Facial recognition logic
├── database.sqlite # SQLite database
├── yolov8s.pt # YOLOv8 model weights
├── nocamera.png # Fallback image when camera isn't available
├── package.json # Additional backend or node dependencies
├── package-lock.json
├── venv/ # Python virtual environment (optional)
├── pycache/ # Compiled Python files (ignore or .gitignore)
└── README.md # Project documentation (this file)
