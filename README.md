# AI Smart Attendance and Smart Door System

An AI-powered smart attendance and door automation system using Face Recognition, OpenCV, Firebase Realtime Database, ESP32, and Computer Vision.

This project automatically recognizes faces, marks attendance, updates cloud records, and controls a smart door lock in real time.

---
# ESP32 setup
<img width="1376" height="768" alt="Image" src="https://github.com/user-attachments/assets/90b843c1-35d6-4333-9afa-08c3e6dff995" />

# Door System

This system automatically controls a door using face recognition. When a detected person is identified as a registered student or faculty member, the door opens automatically, stays open for 3 seconds, and then closes securely. It ensures smart, contactless, and secure access control.

https://github.com/user-attachments/assets/337feb4b-3167-4b35-85ad-2729bdd5f35d


# Features

## Face Recognition Attendance
- Real-time face detection and recognition
- Stable face verification system
- Multiple-angle face training
- Unknown face rejection
- Automatic attendance marking

## Smart Door Automation
- ESP32-based smart door control
- Servo motor automation
- Automatic door open/close
- Firebase realtime synchronization

## Attendance Management
- Duplicate attendance prevention
- Attendance time restriction
- Automatic absent marking
- Present/Absent status tracking
- Attendance history storage

## User Registration System
- Automatic face dataset collection
- Multi-pose face image capture
- Student and faculty support
- Automatic Firebase user creation

## Firebase Cloud Integration
- Realtime database synchronization
- Live attendance updates
- Smart door status control
- Cloud-based user management

---

# Technologies Used

## Programming Languages
- Python
- C++ (Arduino ESP32)

## Computer Vision & AI
- OpenCV
- face_recognition
- MediaPipe
- NumPy
- cvzone

## Database & Cloud
- Firebase Realtime Database
- Firebase Admin SDK

## Hardware
- ESP32
- Servo Motor
- Webcam

---

# Project Structure

```bash
AI-SMART-ATTENDANCE-AND-SMART-DOOR-SYSTEM/
│
├── ESP32/
│   └── door_control.ino
│
├── graphics/
│     
│
├── inputs/
│   ├── faculties/
│   └── students/
│
├── profile/
│
├── EncodeGenerator.py
├── firebase_database.py
├── input_user.py
├── main.py
│
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
```

---

# System Workflow

## Step 1 — Register New User

Run:

```bash
python input_user.py
```

The system:
- Captures multiple face poses
- Creates datasets automatically
- Saves images into organized folders

Supported poses:
- Straight
- Left
- Right
- Up
- Down

---

## Step 2 — Generate Face Encodings

Run:

```bash
python EncodeGenerator.py
```

This will:
- Encode all face images
- Generate face embeddings
- Create Firebase database users automatically

---

## Step 3 — Start Smart Attendance System

Run:

```bash
python main.py
```

The system will:
- Detect and recognize faces
- Verify user identity
- Mark attendance
- Open smart door
- Update Firebase database

---

# Attendance System Logic

## Attendance Time Control

Attendance is accepted only during a specific configured time window.

Example:

```python
start_time = 22:20
end_time = 23:50
```

---

## Duplicate Prevention

The same user cannot mark attendance multiple times on the same day.

---

## Automatic Absent Detection

After attendance time ends:
- Present users are marked as Present
- Missing users are marked as Absent automatically

---

# Smart Door System

The ESP32 continuously monitors Firebase:

```cpp
/DoorSystem/status
```

When the status becomes `true`:
1. Door opens
2. Waits for 3 seconds
3. Door closes automatically

---

# Firebase Database Structure

```bash
AttendanceSystem/
│
├── students/
│   └── student_id/
│
├── faculties/
│   └── faculty_id/
│
DoorSystem/
│
└── status: true/false
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/NeuralAsif/AI-Smart-Attendance-and-Door-Access-System.git
```h

---

## 2. Install Requirements

```bash
pip install -r requirements.txt
```

---

## 3. Configure Firebase

Download your Firebase Admin SDK JSON file:

```text
serviceAccountKey.json
```

Place it in the project root directory.

---

## 4. Configure ESP32

Update your WiFi and Firebase credentials:

```cpp
#define WIFI_SSID "YOUR_WIFI_NAME"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define API_KEY "YOUR_FIREBASE_API_KEY"
```

---

# Requirements

```txt
opencv-python
face-recognition
numpy
cvzone
firebase-admin
mediapipe
cmake
dlib
pickle-mixin
```

---

# Security Notes

Do NOT upload:
- `serviceAccountKey.json`
- Firebase secrets
- WiFi passwords
- Personal datasets
- Encoded face files

Use `.gitignore` properly.

---

# Future Improvements

- Anti-spoofing detection
- Face liveness verification
- Mobile application integration
- Admin dashboard
- Attendance analytics
- Cloud deployment
- Multi-camera support
- AI-based anomaly detection

---

# Screenshots

## Face Recognition Interface
(Add screenshot here)

## Attendance Dashboard
(Add screenshot here)

## Smart Door System
(Add screenshot here)

---

# Hardware Components

- ESP32
- Servo Motor
- Webcam
- Computer/Laptop

---

# Author

## Md. Asaduzzaman Asif

Computer Science and Engineering Student

Fields of Interest:
- Artificial Intelligence
- Machine Learning
- Computer Vision
- IoT Systems
- Smart Automation

---

# License

This project is licensed under the MIT License.

---

# Disclaimer

This project is developed for educational, research, and learning purposes only.
