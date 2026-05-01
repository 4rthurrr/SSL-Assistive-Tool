#!/usr/bin/env python3
"""Copy practice videos from source folder to Backend/lip-reading/"""
import os
import shutil

src_dir = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', '..', 'lip reading-final_finall4_21_2026', 'practis_letters'
))

dst_dir = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', 'lip-reading', 'practis_letters'
))

print(f"Source: {src_dir}")
print(f"Destination: {dst_dir}")

# Create destination directory
os.makedirs(dst_dir, exist_ok=True)

# Copy all MP4 files
copied = []
if os.path.isdir(src_dir):
    for filename in os.listdir(src_dir):
        if filename.endswith('.mp4'):
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join(dst_dir, filename)
            shutil.copy2(src_file, dst_file)
            copied.append(filename)
            print(f"✅ Copied: {filename}")

print(f"\n📦 Total copied: {len(copied)} files")
print(f"Files: {sorted(copied)}")
