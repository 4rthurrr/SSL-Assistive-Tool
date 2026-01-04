"""
Analyze the newly trained model to extract training results and specifications
"""
import tensorflow as tf
import json
import os

print("="*80)
print("  📊 ANALYZING NEW TRAINED MODEL")
print("="*80 + "\n")

# Load the new model
model_path = "d:/shanuka git/SSL-Assistive-Tool/sign_language_app/latest model/best_sign_model_full_features.keras"

if not os.path.exists(model_path):
    print(f"❌ Model not found at: {model_path}")
    exit(1)

print(f"📂 Loading model from: {model_path}")
model = tf.keras.models.load_model(model_path)
print("✅ Model loaded successfully!\n")

# Get model architecture
print("="*80)
print("  🏗️ MODEL ARCHITECTURE")
print("="*80)
model.summary()

# Get input/output shapes
input_shape = model.input_shape
output_shape = model.output_shape

print("\n" + "="*80)
print("  📊 MODEL SPECIFICATIONS")
print("="*80)
print(f"Input Shape:  {input_shape}")
print(f"  - Batch Size: {input_shape[0]} (None = variable)")
print(f"  - Frames: {input_shape[1]}")
print(f"  - Features: {input_shape[2]}")
print(f"\nOutput Shape: {output_shape}")
print(f"  - Number of Classes: {output_shape[1]}")

# Calculate total parameters
total_params = model.count_params()
print(f"\nTotal Parameters: {total_params:,}")

# Count layers
total_layers = len(model.layers)
print(f"Total Layers: {total_layers}")

# Identify layer types
layer_types = {}
for layer in model.layers:
    layer_type = layer.__class__.__name__
    layer_types[layer_type] = layer_types.get(layer_type, 0) + 1

print(f"\nLayer Breakdown:")
for layer_type, count in sorted(layer_types.items()):
    print(f"  - {layer_type}: {count}")

# Compare with old model
print("\n" + "="*80)
print("  📈 COMPARISON WITH OLD MODEL")
print("="*80)

old_input_features = 4
new_input_features = input_shape[2]

print(f"Old Model Input: (50, {old_input_features}) - Only WRIST")
print(f"New Model Input: (50, {new_input_features}) - ALL LANDMARKS")
print(f"\n🎯 Improvement Factor: {new_input_features / old_input_features:.1f}x more features!")

# Calculate landmark count
num_landmarks = new_input_features // 4  # Assuming 4 values per landmark
print(f"\n📍 Number of Landmarks: {num_landmarks}")
print(f"   (33 landmarks × 4 values [x, y, z, visibility] = {num_landmarks * 4} features)")

# Expected accuracy improvement
print("\n" + "="*80)
print("  🎯 EXPECTED PERFORMANCE")
print("="*80)
print(f"Old Model (4 features):   67.33% accuracy")
print(f"New Model ({new_input_features} features): 80-85% accuracy (expected)")
print(f"Improvement: +13-18 percentage points")

print("\n" + "="*80)
print("  ✅ ANALYSIS COMPLETE")
print("="*80)

# Check if there's a training history or metadata
print("\n💡 Next Steps:")
print("  1. Check the training_results_full_features.png for actual accuracy")
print("  2. Move model to backend folder for deployment")
print("  3. Update frontend to extract all 132 features")
print("  4. Test with the new model!")
print("\n" + "="*80)

# Create summary JSON
summary = {
    "model_path": model_path,
    "input_shape": {
        "frames": input_shape[1],
        "features": input_shape[2],
        "landmarks": num_landmarks
    },
    "output_shape": {
        "classes": output_shape[1]
    },
    "total_parameters": int(total_params),
    "total_layers": total_layers,
    "layer_breakdown": layer_types,
    "improvement_factor": float(new_input_features / old_input_features),
    "expected_accuracy": "80-85%"
}

summary_path = "d:/shanuka git/SSL-Assistive-Tool/sign_language_app/latest model/model_analysis.json"
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✅ Analysis saved to: {summary_path}")
