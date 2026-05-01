#!/usr/bin/env python3
import shutil
import os

src = r"Backend\lip-reading\practis_letters"
dst = r"frontend\public\practis_letters"

if os.path.exists(src):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"✓ Copied {src} to {dst}")
    print(f"Files: {os.listdir(dst)}")
else:
    print(f"✗ Source folder not found: {src}")
