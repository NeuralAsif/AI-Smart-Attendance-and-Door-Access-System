import face_recognition
import cv2 as cv
import pickle
import os
from database_old import create_users_from_encoded_lists


base_path = 'inputs'  

img_list = []
label_list = []  
type_list = [] 
name_list = [] 
id_number_list = []  

#track perperson stats
person_stats = {}

print("Scanning folders...")

for group in ["faculties", "students"]:
    group_path = os.path.join(base_path, group)

    if not os.path.isdir(group_path):
        continue

    for person in os.listdir(group_path):
        person_folder_path = os.path.join(group_path, person)

        if not os.path.isdir(person_folder_path):
            continue

        try:
            person_name, person_id = person.split("_", 1)
        except:
            print(f"Invalid folder name format: {person}")
            continue

        label = f"{group}_{person}"  
        print(f"\nProcessing: {label}")

        # Initialize stats for this person
        person_stats[label] = {"success": 0, "skipped": 0}

        for img_name in os.listdir(person_folder_path):
            img_path = os.path.join(person_folder_path, img_name)
            img = cv.imread(img_path)

            if img is None:
                print(f"Could not read: {img_path}")
                person_stats[label]["skipped"] += 1
                continue

            img_list.append(img)
            label_list.append(label)
            type_list.append(group)
            name_list.append(person_name)
            id_number_list.append(person_id)

# Face encoding 
def face_encode(images, labels):
    encode_list = []
    for img, label in zip(images, labels):
        rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)

        if len(encodings) > 0:
            encode_list.append(encodings[0])
            person_stats[label]["success"] += 1
        else:
            print("Face not found → skipping")
            person_stats[label]["skipped"] += 1
    return encode_list


print("\n----------- Start Encoding -----------")
encoded_known = face_encode(img_list, label_list)


encoded_data = {
    "encodings": encoded_known,
    "labels": label_list,
    "types": type_list,
    "names": name_list,
    "ids": id_number_list
}

# Save file
with open('encoded_file.p', 'wb') as encoded_file:
    pickle.dump(encoded_data, encoded_file)

print("\nEncoding Completed Successfully!")
print("File: encoded_file.p saved.\n")

# Print summary
print("----------- Summary per person -----------")
for label, stats in person_stats.items():
    print(f"{label}: Encoded = {stats['success']}, Skipped = {stats['skipped']}")



create_users_from_encoded_lists(type_list, name_list, id_number_list)
