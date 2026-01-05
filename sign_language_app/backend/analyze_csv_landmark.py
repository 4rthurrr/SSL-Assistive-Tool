"""
Analyze CSV files to determine which landmark is in Column 0
by examining the coordinate patterns and movement characteristics.
"""

import numpy as np

# Sample data from your CSVs (first column values from Hello_001.csv)
# Format: [x, y, z, visibility]
hello_samples = [
    [0.4701215922832489, 0.35657134652137756, -0.5241742134094238, 0.9999418258666992],
    [0.4797811210155487, 0.33891957998275757, -0.49623093008995056, 0.9998773336410522],
    [0.4868374466896057, 0.33873018622398376, -0.49612534046173096, 0.9998444318771362],
    [0.491956889629364, 0.33847808837890625, -0.4961484372615814, 0.9998606443405151],
]

again_samples = [
    [0.4845457077026367, 0.3021540641784668, -0.9583510160446167, 0.9995326995849609],
    [0.5077046155929565, 0.28005844354629517, -0.9150920510292053, 0.9991728663444519],
    [0.5195519924163818, 0.2821844220161438, -0.9150465130805969, 0.9993529915809631],
    [0.530475914478302, 0.28555768728256226, -0.9152823090553284, 0.9992448091506958],
]

fast_samples = [
    [0.4981374740600586, 0.32041314244270325, -0.6115949153900146, 0.9999091625213623],
    [0.507370114326477, 0.3048321306705475, -0.5898370146751404, 0.9997856020927429],
    [0.512900173664093, 0.3052417039871216, -0.5899224877357483, 0.9997822642326355],
    [0.5183966755867004, 0.30573710799217224, -0.590034544467926, 0.9997672438621521],
]

def analyze_landmark_characteristics(samples, sign_name):
    """Analyze movement patterns to identify landmark type"""
    samples = np.array(samples)
    
    print(f"\n{'='*70}")
    print(f"  Analyzing: {sign_name}")
    print(f"{'='*70}")
    
    # Extract coordinates
    x_coords = samples[:, 0]
    y_coords = samples[:, 1]
    z_coords = samples[:, 2]
    visibility = samples[:, 3]
    
    # Calculate statistics
    x_mean, x_std = np.mean(x_coords), np.std(x_coords)
    y_mean, y_std = np.mean(y_coords), np.std(y_coords)
    z_mean, z_std = np.mean(z_coords), np.std(z_coords)
    vis_mean = np.mean(visibility)
    
    # Calculate movement range
    x_range = np.max(x_coords) - np.min(x_coords)
    y_range = np.max(y_coords) - np.min(y_coords)
    z_range = np.max(z_coords) - np.min(z_coords)
    
    # Calculate movement velocity (frame-to-frame changes)
    x_velocity = np.mean(np.abs(np.diff(x_coords)))
    y_velocity = np.mean(np.abs(np.diff(y_coords)))
    z_velocity = np.mean(np.abs(np.diff(z_coords)))
    
    print(f"\n📊 Coordinate Statistics:")
    print(f"  X: mean={x_mean:.4f}, std={x_std:.4f}, range={x_range:.4f}")
    print(f"  Y: mean={y_mean:.4f}, std={y_std:.4f}, range={y_range:.4f}")
    print(f"  Z: mean={z_mean:.4f}, std={z_std:.4f}, range={z_range:.4f}")
    
    print(f"\n🏃 Movement Characteristics:")
    print(f"  X velocity: {x_velocity:.4f} (horizontal movement)")
    print(f"  Y velocity: {y_velocity:.4f} (vertical movement)")
    print(f"  Z velocity: {z_velocity:.4f} (depth movement)")
    print(f"  Total movement: {(x_velocity + y_velocity + z_velocity):.4f}")
    
    print(f"\n👁️ Visibility:")
    print(f"  Average: {vis_mean:.4f} ({vis_mean*100:.2f}%)")
    print(f"  Status: {'✅ High visibility' if vis_mean > 0.99 else '⚠️ Moderate visibility'}")
    
    # Position analysis
    print(f"\n📍 Position Analysis:")
    if 0.4 <= x_mean <= 0.6:
        print(f"  ✓ X-position: CENTER (hand is in front of body)")
    elif x_mean < 0.4:
        print(f"  ✓ X-position: LEFT side")
    else:
        print(f"  ✓ X-position: RIGHT side")
    
    if 0.2 <= y_mean <= 0.5:
        print(f"  ✓ Y-position: UPPER region (chest/shoulder height)")
    elif y_mean < 0.2:
        print(f"  ✓ Y-position: VERY HIGH (above shoulders)")
    else:
        print(f"  ✓ Y-position: LOWER region (waist/hip height)")
    
    # Landmark identification
    print(f"\n🎯 Landmark Identification:")
    
    # High visibility + moderate movement = Wrist
    if vis_mean > 0.999 and 0.01 < (x_velocity + y_velocity) < 0.1:
        print(f"  ⭐ LIKELY: WRIST (Landmark 0)")
        print(f"     - Very high visibility (rarely occluded)")
        print(f"     - Moderate movement (base of hand)")
        print(f"     - Central position")
        return "WRIST"
    
    # High visibility + high movement = Finger tip
    elif vis_mean > 0.998 and (x_velocity + y_velocity) > 0.1:
        print(f"  ⭐ LIKELY: FINGER TIP (Index/Middle)")
        print(f"     - High visibility")
        print(f"     - High movement (fingertip is most mobile)")
        return "FINGER_TIP"
    
    # Moderate visibility = May be palm or knuckle
    elif vis_mean < 0.999:
        print(f"  ⭐ LIKELY: PALM or KNUCKLE")
        print(f"     - Slightly lower visibility (can be occluded)")
        return "PALM_OR_KNUCKLE"
    
    else:
        print(f"  ⚠️ UNKNOWN: Need more data for classification")
        return "UNKNOWN"

# Analyze all samples
print("\n" + "="*70)
print("  🔍 CSV LANDMARK ANALYSIS - REVERSE ENGINEERING")
print("="*70)

landmark_hello = analyze_landmark_characteristics(hello_samples, "Hello_001.csv")
landmark_again = analyze_landmark_characteristics(again_samples, "Again_001.csv")
landmark_fast = analyze_landmark_characteristics(fast_samples, "Fast_001.csv")

# Final determination
print("\n" + "="*70)
print("  🎯 FINAL DETERMINATION")
print("="*70)

landmarks_found = [landmark_hello, landmark_again, landmark_fast]
most_common = max(set(landmarks_found), key=landmarks_found.count)

print(f"\n✅ Most Consistent Identification: {most_common}")

if most_common == "WRIST":
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    🎯 LANDMARK IDENTIFIED: WRIST                  ║
║                         (MediaPipe Landmark 0)                     ║
╚═══════════════════════════════════════════════════════════════════╝

📌 Characteristics:
   - Very high visibility (>99.9%) - wrist is rarely occluded
   - Moderate movement - base of hand, not as mobile as fingertips
   - Central position (x ≈ 0.45-0.52) - in front of body
   - Consistent across all signs

🔧 Frontend Implementation:
   Use MediaPipe landmarks[0] (WRIST) to extract:
   - landmarks[0].x
   - landmarks[0].y
   - landmarks[0].z
   - landmarks[0].visibility

✅ This makes sense for sign language:
   - Wrist is the reference point for hand gestures
   - Wrist position indicates where the hand is in space
   - Most stable landmark for tracking
""")

elif most_common == "FINGER_TIP":
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                🎯 LANDMARK IDENTIFIED: FINGER TIP                 ║
║                  (MediaPipe Landmark 8 - Index Tip)               ║
╚═══════════════════════════════════════════════════════════════════╝

📌 Characteristics:
   - High visibility (>99.8%)
   - High movement - fingertips move most during signing
   - Variable position depending on sign

🔧 Frontend Implementation:
   Use MediaPipe landmarks[8] (INDEX_FINGER_TIP) to extract:
   - landmarks[8].x
   - landmarks[8].y
   - landmarks[8].z
   - landmarks[8].visibility
""")

print("\n" + "="*70)
print("  💡 RECOMMENDATION")
print("="*70)

print("""
Based on the analysis, the most likely landmark is the WRIST.

NEXT STEPS:
1. Update frontend to extract landmarks[0] (wrist)
2. Collect 50 frames with [x, y, z, visibility]
3. Test predictions with corrected feature extraction

Would you like me to update the frontend code now?
""")

print("="*70 + "\n")
