from pathlib import Path

app_path = Path("Backend/app.py")
text = app_path.read_text(encoding="utf-8")

text = text.replace(
    "for _site_packages in (\n    os.path.join(_LIP_READING_SOURCE_DIR, \".venv\", \"Lib\", \"site-packages\"),\n    os.path.join(_LIP_READING_SOURCE_DIR, \".realtime\", \"Lib\", \"site-packages\"),\n):\n    if os.path.isdir(_site_packages) and _site_packages not in sys.path:\n        sys.path.insert(0, _site_packages)\nif _LIP_READING_SOURCE_DIR not in sys.path:\n    sys.path.insert(0, _LIP_READING_SOURCE_DIR)\n",
    "for _site_packages in (\n    os.path.join(_LIP_READING_LOCAL_DIR, \".venv\", \"Lib\", \"site-packages\"),\n    os.path.join(_LIP_READING_LOCAL_DIR, \".realtime\", \"Lib\", \"site-packages\"),\n):\n    if os.path.isdir(_site_packages) and _site_packages not in sys.path:\n        sys.path.insert(0, _site_packages)\nif _LIP_READING_LOCAL_DIR not in sys.path:\n    sys.path.insert(0, _LIP_READING_LOCAL_DIR)\n",
)

text = text.replace(
    "threading.Thread(target=_start_source_process, args=(12,), daemon=True).start()\n    print(\"[BRIDGE] Attempting to start source subprocess bridge (background)\")",
    "# Source bridge disabled for self-contained backend operation\n    # threading.Thread(target=_start_source_process, args=(12,), daemon=True).start()\n    # print(\"[BRIDGE] Attempting to start source subprocess bridge (background)\")",
)

old_start = """def _start_source_process(timeout=10):
    global _SOURCE_PROC
    if _SOURCE_PROC and _SOURCE_PROC.poll() is None:
        return True

    python = _find_source_python()
    webmain = os.path.join(_LIP_READING_SOURCE_DIR, 'webmain.py')
    if not os.path.exists(webmain):
        return False

    env = os.environ.copy()
    env['PORT'] = str(_SOURCE_PORT)

    cmd = [python, webmain]
    try:
        _SOURCE_PROC = subprocess.Popen(cmd, cwd=_LIP_READING_SOURCE_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as e:
        print(f"⚠️ Could not start source process: {e}")
        _SOURCE_PROC = None
        return False

    # wait for health
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(_SOURCE_URL + '/api/health', timeout=1)
            if resp.status_code == 200:
                print(f"✅ Source process started at {_SOURCE_URL}")
                return True
        except Exception:
            pass
        time.sleep(0.5)

    print("⚠️ Source process did not become healthy in time; stopping it")
    try:
        _SOURCE_PROC.kill()
    except Exception:
        pass
    _SOURCE_PROC = None
    return False
"""

new_start = """def _start_source_process(timeout=10):
    # Source bridge intentionally disabled.
    # This backend runs independently from the external lip-reading project folder.
    return False
"""

if old_start in text:
    text = text.replace(old_start, new_start)

app_path.write_text(text, encoding="utf-8")
print("Patched Backend/app.py")
