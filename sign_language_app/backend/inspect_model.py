"""
Utility script to inspect your trained model
Run this to get model information and help determine class labels
"""

import tensorflow as tf
from tensorflow import keras
import numpy as np

# Path to your model
MODEL_PATH = "best_sign_model_65plus.keras"

print("=" * 60)
print("MODEL INSPECTION TOOL")
print("=" * 60)

try:
    # Load the model
    print("\n📦 Loading model...")
    model = keras.models.load_model(MODEL_PATH)
    print("✅ Model loaded successfully!\n")
    
    # Model architecture
    print("🏗️  MODEL ARCHITECTURE:")
    print("-" * 60)
    print(f"Input Shape: {model.input_shape}")
    print(f"Output Shape: {model.output_shape}")
    print(f"Number of Classes: {model.output_shape[-1]}")
    print(f"Total Parameters: {model.count_params():,}")
    print(f"Number of Layers: {len(model.layers)}")
    
    # Model summary
    print("\n📋 MODEL SUMMARY:")
    print("-" * 60)
    model.summary()
    
    # Output layer information
    print("\n🎯 OUTPUT LAYER INFO:")
    print("-" * 60)
    output_layer = model.layers[-1]
    print(f"Layer Name: {output_layer.name}")
    print(f"Layer Type: {type(output_layer).__name__}")
    print(f"Output Units: {output_layer.units if hasattr(output_layer, 'units') else 'N/A'}")
    print(f"Activation: {output_layer.activation.__name__ if hasattr(output_layer, 'activation') else 'N/A'}")
    
    # Number of classes
    num_classes = model.output_shape[-1]
    print(f"\n✨ Your model predicts {num_classes} different classes")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print(f"1. You need to provide exactly {num_classes} class labels")
    print("2. Check your Kaggle training notebook for class names")
    print("3. Look for 'train_generator.class_indices' in your code")
    print("4. Update CLASS_LABELS in model_loader.py with your actual labels")
    print("\nExample format:")
    print("CLASS_LABELS = [")
    print('    "class_0", "class_1", "class_2", ...')
    print("]")
    print(f"\n⚠️  Make sure the list has exactly {num_classes} items!")
    
except FileNotFoundError:
    print(f"\n❌ ERROR: Model file not found!")
    print(f"   Expected location: {MODEL_PATH}")
    print("\n💡 Make sure to:")
    print("   1. Copy 'best_sign_model_65plus.keras' to the backend folder")
    print("   2. Run this script from the backend directory")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\n💡 Full error details:")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
