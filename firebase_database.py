import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://realtime-143c9-default-rtdb.firebaseio.com/"
    })

# ---------------- Door System ----------------
door_ref = db.reference("DoorSystem")

if door_ref.get() is None:
    door_ref.set({
        "status": False
    })
    print("DoorSystem created successfully")

# ---------------- Attendance System ----------------
def create_users_from_encoded_lists(types, names, ids):

    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_ref = db.reference("AttendanceSystem")

    for user_type, name, user_id in zip(types, names, ids):

        user_ref = base_ref.child(user_type).child(user_id)

        if user_ref.get() is not None:
            print(f"Already Exists → {name}")
            continue

        data = {
            "name": name,
            "id": user_id,
            "total_attendance": 0,
            "total_absent": 0,
            "last_attendance_time": "Never",
            "created_at": now_time
        }

        # Add department only for students
        if user_type == "students":
            data["department"] = "CSE"

        user_ref.set(data)

        print(f"DB User Created → {user_type[:-1]} | {name}")