import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'

import sys
sys.stderr = open(os.devnull, "w")
import cv2 as cv
import mediapipe as mp
import time



# USER INPUTS
user_type = input("Are you Faculty or Student? (f/s): ").strip().lower()
if user_type == 'f':
    user_type = "faculties"
elif user_type == 's':
    user_type = "students"
else:
    print("INPUT ERROR: Enter only f or s")
    exit()

name = input("Enter your Name: ").strip()
user_id = input("Enter your ID: ").strip()


main_folder = "inputs"  # main folder
folder_name = f"{name}_{user_id}"
save_type_folder = os.path.join(main_folder, user_type)
save_path = os.path.join(save_type_folder, folder_name)

os.makedirs(save_type_folder, exist_ok=True)
os.makedirs(save_path, exist_ok=True)

print(f"\n Images will be saved in: {save_path}\n")

poses = ["straight", "left", "right", "up", "down"]
images_per_pose = 10               # 80 images
total_images = len(poses) * images_per_pose
per_image_delay = 0.6              
countdown_seconds = 3               
font = cv.FONT_HERSHEY_SIMPLEX


mp_face = mp.solutions.face_detection

video = cv.VideoCapture(0,cv.CAP_DSHOW)
if not video.isOpened():
    print("ERROR: Camera not detected!")
    exit()


with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
    print("Get ready! Capture will begin in 3 seconds...")
    time.sleep(3)

    global_count = 0
    for pose in poses:
        pose_count = 0
        # countdown
        start_time = time.time()
        countdown_start = time.time()
        while True:
            ret, frame = video.read()
            if not ret:
                print("ERROR: Failed to capture frame!")
                break
            frame = cv.flip(frame, 1)
            h, w, _ = frame.shape

            elapsed = int(time.time() - countdown_start)
            remain = countdown_seconds - elapsed
            if remain > 0:
                cv.putText(frame, f"Pose: {pose.upper()}  | Starting in {remain}s", (20, 50),
                           font, 0.9, (0, 255, 255), 2, cv.LINE_AA)
                cv.putText(frame, "Please position your face accordingly.", (20, 90),
                           font, 0.7, (200, 200, 200), 1, cv.LINE_AA)
                cv.imshow("Capture Faces - Pose Instructions", frame)
                if cv.waitKey(1) & 0xFF == ord('q'):
                    print("Interrupted by user.")
                    video.release()
                    cv.destroyAllWindows()
                    exit()
                continue
            else:
                # Start capturing 
                cv.putText(frame, f"Pose: {pose.upper()}  | Capturing {pose_count+1}/{images_per_pose}", (20, 50),
                           font, 0.9, (0, 255, 0), 2, cv.LINE_AA)

                # Face detection
                rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                result = face_detection.process(rgb)

                if result.detections:
                    bbox = result.detections[0].location_data.relative_bounding_box
                    x1 = max(0, int((bbox.xmin - 0.12) * w))
                    y1 = max(0, int((bbox.ymin - 0.12) * h))
                    x2 = min(w, int((bbox.xmin + bbox.width + 0.12) * w))
                    y2 = min(h, int((bbox.ymin + bbox.height + 0.12) * h))

                    face_crop = frame[y1:y2, x1:x2]

                    if face_crop.size > 0:
                        # save image
                        pose_count += 1
                        global_count += 1
                        file_name = f"{name}_{user_id}_{pose}_{pose_count}.jpg"
                        cv.imwrite(os.path.join(save_path, file_name), face_crop)
                        print(f" Saved [{global_count}/{total_images}] -> {file_name}")

                        
                        time.sleep(per_image_delay)

                    cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                else:
                    cv.putText(frame, "No face detected - adjust position", (20, 120),
                               font, 0.7, (0, 0, 255), 2, cv.LINE_AA)

                cv.putText(frame, f"Total: {global_count}/{total_images}", (20, h - 30),
                           font, 0.8, (255, 255, 255), 2, cv.LINE_AA)

                cv.imshow("Capture Faces - Pose Instructions", frame)

                if pose_count >= images_per_pose:
                    print(f"--> Completed pose: {pose} ({pose_count} images)\n")
                    time.sleep(0.8)
                    break

                if cv.waitKey(1) & 0xFF == ord('q'):
                    print("Interrupted by user.")
                    video.release()
                    cv.destroyAllWindows()
                    exit()


video.release()
cv.destroyAllWindows()

print(f"\n Capture complete! {global_count} images saved in: {save_path}")
