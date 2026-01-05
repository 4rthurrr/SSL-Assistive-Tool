"""
Quick script to analyze the CSV structure from your Kaggle training data
Upload this to Kaggle and run it to see the exact format
"""
import pandas as pd
import ast
import os

# Path to your training CSV (update this)
SAMPLE_CSV = "/kaggle/input/ssl400-dynamic-sri-lankan-sign-language-dataset/Dataset - MP - CSV/Adjectives/Bad/1.csv"

print("=" * 80)
print("CSV STRUCTURE ANALYSIS")
print("=" * 80)

# Load CSV
df = pd.read_csv(SAMPLE_CSV, header=None)

print(f"\n1. CSV Shape: {df.shape}")
print(f"   Rows (frames): {df.shape[0]}")
print(f"   Columns (landmarks): {df.shape[1]}")

print(f"\n2. First cell type: {type(df.iloc[0, 0])}")
print(f"   First cell value: {df.iloc[0, 0]}")

# Check if string format
if isinstance(df.iloc[0, 0], str) and df.iloc[0, 0].startswith("["):
    print("\n3. Format: STRING ARRAYS")
    
    # Parse first cell
    first_landmark = ast.literal_eval(df.iloc[0, 0])
    print(f"   Features per landmark: {len(first_landmark)}")
    print(f"   First landmark data: {first_landmark}")
    
    # Calculate total features
    total_features = df.shape[1] * len(first_landmark)
    print(f"\n4. Total features per frame: {total_features}")
    print(f"   ({df.shape[1]} landmarks × {len(first_landmark)} values)")
    
    # Show first 3 columns of first row
    print(f"\n5. First 3 landmarks of first frame:")
    for col_idx in range(min(3, df.shape[1])):
        landmark = ast.literal_eval(df.iloc[0, col_idx])
        print(f"   Column {col_idx}: {landmark}")
        
else:
    print("\n3. Format: NUMERIC CSV")
    print(f"   Total features: {df.shape[1]}")
    print(f"   First row sample: {df.iloc[0, :8].tolist()}")

print("\n" + "=" * 80)
print("COPY THIS OUTPUT AND SHARE IT!")
print("=" * 80)
