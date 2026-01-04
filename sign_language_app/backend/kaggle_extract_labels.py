"""
Run this script in your Kaggle notebook to extract the 383 class labels.
Copy the output and paste it into model_loader.py
"""
import os

DATASET_PATH = "/kaggle/input/ssl400-dynamic-sri-lankan-sign-language-dataset/Dataset - MP - CSV/"

def collect_labels(base_path):
    """Extract labels from folder structure: {category}/{subcat}"""
    labels = []
    for category in sorted(os.listdir(base_path)):
        cat_path = os.path.join(base_path, category)
        if not os.path.isdir(cat_path):
            continue
        for subcat in sorted(os.listdir(cat_path)):
            subcat_path = os.path.join(cat_path, subcat)
            if not os.path.isdir(subcat_path):
                continue
            labels.append(f"{category}/{subcat}")
    return sorted(labels)

# Extract labels
print("Extracting SSL400 class labels...\n")
class_labels = collect_labels(DATASET_PATH)

print(f"Total classes found: {len(class_labels)}\n")
print("="*80)
print("Copy the list below and paste it into model_loader.py:")
print("="*80)
print("\nCLASS_LABELS = [")
for i, label in enumerate(class_labels):
    print(f'    "{label}",  # {i}')
print("]")
print("\n" + "="*80)
print(f"✓ {len(class_labels)} classes exported")
print("="*80)
