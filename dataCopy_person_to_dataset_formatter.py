import os
import shutil

# Path to main persons folder
persons_root = "persons"     # change this
dataset_root = "dataset_video"     # change this

for person_name in os.listdir(persons_root):
    person_path = os.path.join(persons_root, person_name)

    if not os.path.isdir(person_path):
        continue

    # Loop through letter folders (letter_1, letter_2...)
    for letter_folder in os.listdir(person_path):
        letter_path = os.path.join(person_path, letter_folder)

        if not os.path.isdir(letter_path):
            continue

        # Destination letter folder inside dataset
        destination_letter_path = os.path.join(dataset_root, letter_folder)

        # Create destination folder if not exists
        os.makedirs(destination_letter_path, exist_ok=True)

        # Loop through video files
        for file_name in os.listdir(letter_path):
            if file_name.lower().endswith(".mp4"):
                source_file = os.path.join(letter_path, file_name)

                # New name: personname_filename.mp4
                new_name = f"{person_name}_{file_name}"
                destination_file = os.path.join(destination_letter_path, new_name)

                shutil.copy2(source_file, destination_file)

                print(f"Copied: {destination_file}")

print("✅ Done copying all files.")