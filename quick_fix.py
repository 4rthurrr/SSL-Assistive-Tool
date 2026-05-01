#!/usr/bin/env python3
"""Patch app.py to remove source folder dependencies"""
import os

app_file = r"Backend\app.py"
lines = []

with open(app_file, 'r', encoding='utf-8') as f:
    for line in f:
        # Comment out the _start_source_process call
        if 'threading.Thread(target=_start_source_process' in line:
            lines.append('    # ' + line)
        # Comment out the print statement after it
        elif 'print("[BRIDGE] Attempting to start source subprocess' in line:
            lines.append('    # ' + line)
        # Disable the _start_source_process function - replace its body
        elif 'def _start_source_process(timeout=10):' in line:
            lines.append(line)
            lines.append('    # DISABLED: Source subprocess bridge not needed with fallback implementations\n')
            lines.append('    return False\n')
            # Skip to the next function
            skip_until_next_def = True
            in_docstring = False
        elif line.startswith('def ') and 'skip_until_next_def' in locals() and skip_until_next_def:
            skip_until_next_def = False
            lines.append(line)
        elif 'skip_until_next_def' in locals() and skip_until_next_def:
            continue
        else:
            lines.append(line)

with open(app_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ Fixed app.py")
