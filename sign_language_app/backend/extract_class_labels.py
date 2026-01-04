"""
Helper script to generate class labels from your training data folder structure
Run this script and copy the output to model_loader.py
"""

import os
import json

# UPDATE THIS PATH to point to your Kaggle training data folder
# Example: "D:/kaggle/sign_language_dataset/train"
TRAINING_DATA_PATH = "/kaggle/input/ssl400-dynamic-sri-lankan-sign-language-dataset/"

def extract_class_labels(data_path):
    """
    Extract class labels from folder structure
    Assumes folders are named with class labels
    """
    if not os.path.exists(data_path):
        print(f"❌ ERROR: Path not found: {data_path}")
        print("\n💡 Please update TRAINING_DATA_PATH in this script")
        return []
    
    # Get all subdirectories
    folders = []
    for item in os.listdir(data_path):
        item_path = os.path.join(data_path, item)
        if os.path.isdir(item_path):
            folders.append(item)
    
    # Sort alphabetically (Kaggle's default)
    folders.sort()
    
    return folders


if __name__ == "__main__":
    print("=" * 70)
    print("CLASS LABEL EXTRACTOR")
    print("=" * 70)
    
    print(f"\n📁 Scanning: {TRAINING_DATA_PATH}\n")
    
    class_labels = extract_class_labels(TRAINING_DATA_PATH)
    
    if not class_labels:
        print("\n⚠️  No class labels found!")
        print("\nTo use this script:")
        print("1. Open this file in an editor")
        print("2. Update TRAINING_DATA_PATH to your actual training data folder")
        print("3. Run this script again")
        print("\nExample paths:")
        print("  - D:/kaggle/sign_language_dataset/train")
        print("  - C:/Users/YourName/Downloads/dataset/train")
    else:
        print(f"✅ Found {len(class_labels)} classes!\n")
        print("=" * 70)
        print("COPY THE CODE BELOW TO model_loader.py")
        print("=" * 70)
        print("\nCLASS_LABELS = [")
        for i, label in enumerate(class_labels):
            # Format for Python list
            print(f'    "{label}",  # Index {i}')
        print("]\n")
        
        # Also save to file for backup
        output_file = "extracted_class_labels.json"
        with open(output_file, 'w') as f:
            json.dump(class_labels, f, indent=2)
        print(f"💾 Also saved to: {output_file}")
        
        print("\n" + "=" * 70)
        print(f"✅ Total: {len(class_labels)} classes")
        print("=" * 70)
