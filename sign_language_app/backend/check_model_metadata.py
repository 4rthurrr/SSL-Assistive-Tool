"""
Check if the trained model has class information embedded
"""
import tensorflow as tf
import json
import os

model_path = "best_sign_model_65plus.keras"

print("Inspecting model for embedded class information...\n")

# Load model
model = tf.keras.models.load_model(model_path)

# Check for custom metadata
if hasattr(model, 'history'):
    print("✓ Model has training history")
    
# Check model config
config = model.get_config()
if 'class_names' in config:
    print("✓ Found class names in config!")
    print(config['class_names'])
else:
    print("✗ No class names found in model config")

# Check for accompanying files
model_dir = os.path.dirname(model_path)
possible_files = [
    'class_mapping.json',
    'class_names.txt',
    'label_map.json',
    'classes.json'
]

print("\nLooking for label files...")
for filename in possible_files:
    filepath = os.path.join(model_dir if model_dir else '.', filename)
    if os.path.exists(filepath):
        print(f"✓ Found: {filename}")
        try:
            with open(filepath, 'r') as f:
                if filename.endswith('.json'):
                    data = json.load(f)
                    print(f"  Content: {list(data.keys()) if isinstance(data, dict) else len(data)}")
                else:
                    lines = f.readlines()
                    print(f"  Lines: {len(lines)}")
        except Exception as e:
            print(f"  Error reading: {e}")
    else:
        print(f"✗ Not found: {filename}")

print("\n" + "="*80)
print("Model output shape:", model.output.shape)
print("Expected classes: 383")
print("="*80)
