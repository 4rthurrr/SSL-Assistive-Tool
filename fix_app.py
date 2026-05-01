#!/usr/bin/env python3
"""Fix app.py by removing source subprocess bridge code"""
import re

app_file = r"Backend/app.py"

with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Comment out the _start_source_process call at startup
content = re.sub(
    r'(threading\.Thread\(target=_start_source_process)',
    r'# DISABLED: \1',
    content
)

# Replace the entire _start_source_process function with a no-op version
old_func = r'''def _start_source_process\(timeout=10\):
    global _SOURCE_PROC
    if _SOURCE_PROC and _SOURCE_PROC\.poll\(\) is None:
        return True

    python = _find_source_python\(\)
    webmain = os\.path\.join\(_LIP_READING_SOURCE_DIR, 'webmain\.py'\)
    if not os\.path\.exists\(webmain\):
        return False

    env = os\.environ\.copy\(\)
    env\['PORT'\] = str\(_SOURCE_PORT\)

    cmd = \[python, webmain\]
    try:
        _SOURCE_PROC = subprocess\.Popen\(cmd, cwd=_LIP_READING_SOURCE_DIR, env=env, stdout=subprocess\.PIPE, stderr=subprocess\.STDOUT\)
    except Exception as e:
        print\(f"⚠️ Could not start source process: \{e\}"\)
        _SOURCE_PROC = None
        return False

    # wait for health
    start = time\.time\(\)
    while time\.time\(\) - start < timeout:
        try:
            resp = requests\.get\(_SOURCE_URL \+ '/api/health', timeout=1\)
            if resp\.status_code == 200:
                print\(f"✅ Source process started at \{_SOURCE_URL\}"\)
                return True
        except Exception:
            pass
        time\.sleep\(0\.5\)

    print\("⚠️ Source process did not become healthy in time; stopping it"\)
    try:
        _SOURCE_PROC\.kill\(\)
    except Exception:
        pass
    _SOURCE_PROC = None
    return False'''

new_func = '''def _start_source_process(timeout=10):
    # DISABLED: Source subprocess bridge not needed with fallback implementations
    return False'''

if re.search(old_func, content, re.DOTALL):
    content = re.sub(old_func, new_func, content, flags=re.DOTALL)
    print("✓ Replaced _start_source_process function")
else:
    print("! Could not find _start_source_process function to replace")

with open(app_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ Fixed {app_file}")
