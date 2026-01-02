import os

# Your video directory
VIDEO_DIR = r"D:\Game new\Backend\public\Dataset - Original-20251215T123918Z-3-001"

print("="*70)
print("🔍 VIDEO DIRECTORY DIAGNOSTIC")
print("="*70)

print(f"\n📁 Base Directory: {VIDEO_DIR}")
print(f"✓ Exists: {os.path.exists(VIDEO_DIR)}")

if not os.path.exists(VIDEO_DIR):
    print("❌ Directory does not exist!")
    exit()

print("\n📂 Directory Structure:")
print("-"*70)

# Walk through and show structure
video_count = 0
for root, dirs, files in os.walk(VIDEO_DIR):
    level = root.replace(VIDEO_DIR, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}📁 {os.path.basename(root)}/')
    
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        if file.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv')):
            video_count += 1
            # Show full path info
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, VIDEO_DIR)
            print(f'{subindent}🎥 {file}')
            print(f'{subindent}   → Relative: {rel_path}')
            print(f'{subindent}   → URL safe: {rel_path.replace(chr(92), "/")}')
            
            if video_count >= 5:  # Show only first 5 for brevity
                print(f'{subindent}... and more files')
                break
    
    if video_count >= 5:
        break

print(f"\n📊 Total Videos Found: {video_count}")

# Test specific file access
print("\n🧪 Testing File Access:")
print("-"*70)

# Try to find a specific video
test_file = "Beautiful_002.mp4"
found = False

for root, dirs, files in os.walk(VIDEO_DIR):
    if test_file in files:
        full_path = os.path.join(root, test_file)
        rel_path = os.path.relpath(full_path, VIDEO_DIR)
        print(f"✓ Found: {test_file}")
        print(f"  Full path: {full_path}")
        print(f"  Relative: {rel_path}")
        print(f"  URL format: {rel_path.replace(chr(92), '/')}")
        print(f"  File exists: {os.path.exists(full_path)}")
        print(f"  File size: {os.path.getsize(full_path)} bytes")
        found = True
        break

if not found:
    print(f"❌ {test_file} not found in directory tree")

print("\n" + "="*70)