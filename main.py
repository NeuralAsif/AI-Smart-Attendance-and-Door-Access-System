import cv2
import pickle
import face_recognition
import numpy as np
import cvzone
from datetime import datetime, time as time_module
import firebase_admin
from firebase_admin import credentials, db
import subprocess
import threading
import os
import sys
from collections import Counter
import time

FACE_MATCH_THRESHOLD = 0.45
STABILITY_TIME = 1.0  # seconds
REQUIRED_STABLE_FRAMES = 4  # minimum stable frames
DISPLAY_TIME = 3.0  # seconds to display profile

face_buffer = []
buffer_start_time = None

# Add these global variables for stability checking
stable_ids = []
stable_start_time = None

# Variables for display management
verified_user = None
verified_start_time = None
display_active = False
database_updated = False  # NEW: track if database was updated

# ------------------ Firebase Init ------------------
cred = credentials.Certificate("serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://realtime-143c9-default-rtdb.firebaseio.com/'
    })
# ---------------- Door Reference ----------------
door_ref = db.reference("DoorSystem")
# ------------------ Load Encodings ------------------
print("Loading encoded faces ...")
with open('encoded_file.p', 'rb') as f:
    encoded_data = pickle.load(f)
encodeListKnown = encoded_data['encodings']
name_list = encoded_data['names']
id_list = encoded_data['ids']
type_list = encoded_data['types']
label_list = encoded_data['labels']

counter = 0
already_marked_user = None
already_marked_timer = 0
absent_check_done = False

print("Encodings loaded.")


# ------------------ Helper Functions ------------------
def is_attendance_time():
    """Check if current time is between 7:00 PM and 7:40 PM"""
    now = datetime.now().time()
    start_time = time_module(22, 20)
    end_time = time_module(23, 50)
    return start_time <= now <= end_time


def is_after_attendance_time():
    """Check if current time is after 6:30 PM"""
    now = datetime.now().time()
    end_time = time_module(23, 50)  # 7:40 PM
    return now > end_time


def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")


def check_already_marked(user_type, user_id):
    """Check if user already marked attendance today"""
    try:
        ref = db.reference(f'AttendanceSystem/{user_type}/{user_id}')
        information = ref.get()
        if information and 'last_attendance_date' in information:
            last_date = information['last_attendance_date']
            today = get_today_date()
            return last_date == today
        return False
    except:
        return False


def mark_all_absent():
    """Mark all students who didn't attend today as absent"""
    global absent_check_done
    print("\n=== Checking for absent students ===")
    today = get_today_date()

    try:
        # Get all user types
        all_data = db.reference('AttendanceSystem').get()
        if not all_data:
            print("No data found in database")
            return

        absent_count = 0
        present_count = 0

        # Loop through all user types and users
        for user_type in all_data:
            users = all_data[user_type]
            if not isinstance(users, dict):
                continue

            for user_id in users:
                user_info = users[user_id]

                # Check if user marked attendance today
                last_date = user_info.get('last_attendance_date', '')

                if last_date != today:
                    # User is absent - mark them
                    ref = db.reference(f'AttendanceSystem/{user_type}/{user_id}')

                    # Get current absent count
                    current_absent = user_info.get('total_absent', 0)

                    # Update absent info
                    ref.update({
                        'total_absent': current_absent + 1,
                        'last_absent_date': today,
                        'status': 'Absent'
                    })

                    absent_count += 1
                    user_name = user_info.get('name', user_id)
                    print(f"✗ Marked ABSENT: {user_name} ({user_id}) - Type: {user_type}")
                else:
                    # User is present
                    ref = db.reference(f'AttendanceSystem/{user_type}/{user_id}')
                    ref.update({'status': 'Present'})
                    present_count += 1
                    user_name = user_info.get('name', user_id)
                    print(f"✓ Present: {user_name} ({user_id}) - Type: {user_type}")

        print(f"\n=== Summary ===")
        print(f"Present: {present_count}")
        print(f"Absent: {absent_count}")
        print(f"Total: {present_count + absent_count}")
        print("===================\n")

        absent_check_done = True

    except Exception as e:
        print(f"Error marking absent students: {e}")


def check_and_mark_absent_background():
    """Background thread to check time and mark absent students"""
    global absent_check_done
    while True:
        # Reset flag at start of new day (midnight)
        now = datetime.now().time()
        if now.hour == 0 and now.minute == 0:
            absent_check_done = False
            print("New day started - Reset absent check flag")

        # Check if it's after 7:40 PM and we haven't done the check today
        if is_after_attendance_time() and not absent_check_done:
            print("Attendance time has passed. Marking absent students...")
            mark_all_absent()

        # Sleep for 60 seconds before next check
        import time as time_module_sleep
        time_module_sleep.sleep(60)


# Start background thread for absent checking
absent_thread = threading.Thread(target=check_and_mark_absent_background, daemon=True)
absent_thread.start()
print("Background absent checker started...")

# ------------------ Webcam Setup ------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

# Background for overlay
imgBackground = cv2.imread('graphics/background.jpg')
imgBackground = cv2.resize(imgBackground, (1142, 678))
font = cv2.FONT_HERSHEY_SIMPLEX

while True:
    true, frame = cap.read()
    if not true:
        break

    imgBackground = cv2.imread('graphics/background.jpg')
    imgBackground = cv2.resize(imgBackground, (1142, 678))

    # -------- Button settings --------
    button_x1, button_y1 = 0, 50
    button_x2, button_y2 = 200, 100

    # Draw button rectangle
    cv2.rectangle(
        imgBackground,
        (button_x1, button_y1),
        (button_x2, button_y2),
        (0, 120, 255),
        -1
    )

    # Button text
    cv2.putText(
        imgBackground,
        "NEW ADD",
        (button_x1 + 20, button_y1 + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 255, 255),
        3
    )


    def mouse_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if button_x1 <= x <= button_x2 and button_y1 <= y <= button_y2:
                print("NEW button clicked")
                subprocess.Popen(["python", "new_add.py"])


    frame = cv2.flip(frame, 1)
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # ------------------ Check if display time has ended ------------------
    current_time = time.time()

    if display_active and verified_user is not None:
        elapsed_time = current_time - verified_start_time

        # After 3 seconds, update database (only once)
        if elapsed_time >= DISPLAY_TIME and not database_updated:
            user_id = verified_user['user_id']
            name = verified_user['name']
            user_type = verified_user['user_type']

            # Only update if within time and not already marked
            if is_attendance_time() and not check_already_marked(user_type, user_id):
                try:
                    print(f"\n=== Updating Database ===")
                    print(f"User: {name} ({user_id})")
                    print(f"Type: {user_type}")

                    # Get current information
                    ref = db.reference(f'AttendanceSystem/{user_type}/{user_id}')
                    information = ref.get()

                    if information:
                        # Calculate new values
                        new_total = information.get('total_attendance', 0) + 1
                        today = get_today_date()
                        current_time_str = datetime.now().strftime("%H:%M:%S")

                        # Update database
                        ref.update({
                            'total_attendance': new_total,
                            'last_attendance_date': today,
                            'last_attendance_time': current_time_str,
                            'status': 'Present'
                        })

                        print(f"✓ Attendance marked successfully!")
                        print(f"  Total Attendance: {new_total}")
                        print(f"  Date: {today}")
                        print(f"  Time: {current_time_str}")
                        print(f"========================\n")

                        # Mark database as updated
                        database_updated = True

                        # Set timer to show "already marked" message
                        already_marked_user = user_id
                        already_marked_timer = 90  # 3 seconds at 30fps
                    else:
                        print(f"✗ Error: User information not found in database")
                        database_updated = True

                except Exception as e:
                    print(f"✗ Error updating attendance: {e}")
                    import traceback

                    traceback.print_exc()
                    database_updated = True
            else:
                if not is_attendance_time():
                    print(f" Cannot mark attendance - Outside attendance hours")
                elif check_already_marked(user_type, user_id):
                    print(f" Already marked today: {name} ({user_id})")
                database_updated = True

        # After display time + 1 second buffer, reset everything
        if elapsed_time >= DISPLAY_TIME + 1.0:
            print(f"Display ended for {verified_user['name']}\n")
            display_active = False
            verified_user = None
            verified_start_time = None
            database_updated = False

    # ------------------ Face Recognition ------------------
    face_locations = face_recognition.face_locations(rgb_small)
    face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

    # Decrease already marked timer
    if already_marked_timer > 0:
        already_marked_timer -= 1
        if already_marked_timer == 0:
            already_marked_user = None

    # If no face detected and not displaying verified user, reset stability buffer
    if len(face_encodings) == 0 and not display_active:
        stable_ids.clear()
        stable_start_time = None

    # If currently displaying verified user, show the profile
    if display_active and verified_user is not None:
        user_id = verified_user['user_id']
        name = verified_user['name']
        user_type = verified_user['user_type']
        face_location = verified_user['face_location']

        # Scale back face locations
        y1, x2, y2, x1 = face_location
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

        # Draw rectangle
        cvzone.cornerRect(frame, (x1, y1, x2 - x1, y2 - y1), rt=0)

        # Display user information
        cv2.putText(
            imgBackground,
            f"{user_id}",
            (770, 625),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )
        cv2.putText(
            imgBackground,
            f"{name}",
            (770, 537),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )
        cv2.putText(
            imgBackground,
            f" {user_type}",
            (770, 450),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )

        # Display profile picture
        try:
            profile = cv2.imread(f'profile/{user_id}.jpg')
            profile = cv2.resize(profile, (300, 300))
            imgBackground[54:354, 776:1076] = profile
        except:
            pass

        # Check if already marked today
        is_marked_today = check_already_marked(user_type, user_id)

        if is_marked_today or (already_marked_user == user_id and already_marked_timer > 0):
            # Show "Already Marked" message
            already_marked = cv2.imread('graphics/marked.png', cv2.IMREAD_UNCHANGED)
            if already_marked is not None:
                already_marked = cv2.resize(already_marked, (192, 128))
                bgr_marked = already_marked[:, :, :3]
                alpha_mask = already_marked[:, :, 3] / 255.0

                y1_img, y2_img = 250, 378
                x1_img, x2_img = 900, 1092
                roi = imgBackground[y1_img:y2_img, x1_img:x2_img]

                for c in range(0, 3):
                    roi[:, :, c] = (alpha_mask * bgr_marked[:, :, c] +
                                    (1 - alpha_mask) * roi[:, :, c])

                imgBackground[y1_img:y2_img, x1_img:x2_img] = roi
            else:
                # Fallback text if image not found
                cv2.putText(
                    imgBackground,
                    "ALREADY MARKED",
                    (850, 320),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA
                )
        else:
            # Check if it's attendance time
            if not is_attendance_time():
                # Show "Outside Attendance Hours" message
                cv2.putText(
                    imgBackground,
                    "Outside Hours",
                    (850, 300),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA
                )
                cv2.putText(
                    imgBackground,
                    "7:00-7:40 PM",
                    (850, 340),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA
                )
            else:
                # Show "OK" mark
                marked = cv2.imread('graphics/ok.png', cv2.IMREAD_UNCHANGED)
                if marked is not None:
                    marked = cv2.resize(marked, (192, 128))
                    bgr_marked = marked[:, :, :3]
                    alpha_mask = marked[:, :, 3] / 255.0

                    y1_img, y2_img = 250, 378
                    x1_img, x2_img = 900, 1092
                    roi = imgBackground[y1_img:y2_img, x1_img:x2_img]

                    for c in range(0, 3):
                        roi[:, :, c] = (alpha_mask * bgr_marked[:, :, c] +
                                        (1 - alpha_mask) * roi[:, :, c])

                    imgBackground[y1_img:y2_img, x1_img:x2_img] = roi

    # Process face recognition only if not currently displaying
    elif not display_active:
        for face_encoding, face_location in zip(face_encodings, face_locations):
            face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
            match_index = np.argmin(face_distances)
            current_time_loop = time.time()

            if face_distances[match_index] < FACE_MATCH_THRESHOLD:
                detected_id = id_list[match_index]
            else:
                detected_id = "UNKNOWN"

            # -------- STABILITY BUFFER --------
            if stable_start_time is None:
                stable_start_time = current_time_loop
                stable_ids.clear()

            stable_ids.append(detected_id)

            # -------- DECIDE AFTER 2 SECONDS --------
            if current_time_loop - stable_start_time >= STABILITY_TIME:
                if len(stable_ids) >= REQUIRED_STABLE_FRAMES:
                    # Count most common ID
                    id_counts = Counter(stable_ids)
                    final_id, count = id_counts.most_common(1)[0]

                    if final_id != "UNKNOWN" and count >= REQUIRED_STABLE_FRAMES:
                        match_index = id_list.index(final_id)
                        user_id = id_list[match_index]
                        name = name_list[match_index]
                        user_type = type_list[match_index]

                        # Set verified user for display
                        verified_user = {
                            'user_id': user_id,
                            'name': name,
                            'user_type': user_type,
                            'face_location': face_location
                        }
                        verified_start_time = time.time()
                        display_active = True
                        database_updated = False  # Reset flag for new user

                        print(f"\n✓ Verified: {name} ({user_id})")
                        print(f"  Displaying profile for {DISPLAY_TIME} seconds...")

                        # ---------------- Door Open Signal ----------------
                        try:
                            door_ref.update({
                                "status": True
                            })

                            print("Door Opened")

                            # Small delay
                            time.sleep(0.5)

                            door_ref.update({
                                "status": False
                            })

                            print("Door Closed")

                        except Exception as e:
                            print(f"Door Error: {e}")

                # Reset for next scan
                stable_ids.clear()
                stable_start_time = None
            else:
                # Show "Verifying..." message during stability check
                remaining = STABILITY_TIME - (current_time_loop - stable_start_time)
                cv2.putText(
                    imgBackground,
                    f"Verifying... {remaining:.1f}s",
                    (820, 300),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
                    2,
                    cv2.LINE_AA
                )

    # ------------------ Overlay ------------------
    imgBackground[160:160 + 480, 60:60 + 640] = frame
    cv2.imshow("Face Attendance", imgBackground)
    cv2.setMouseCallback("Face Attendance", mouse_click)

    if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q')]:
        break

cap.release()
cv2.destroyAllWindows()