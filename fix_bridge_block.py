from pathlib import Path

path = Path("Backend/app.py")
text = path.read_text(encoding="utf-8")

bad_block = '''try:
    # Source bridge disabled for self-contained backend operation
    # threading.Thread(target=_start_source_process, args=(12,), daemon=True).start()
    # print("[BRIDGE] Attempting to start source subprocess bridge (background)")
except Exception as e:
    print(f"[BRIDGE] Failed to spawn bridge starter: {e}")
'''

if bad_block in text:
    text = text.replace(bad_block, '# Source bridge disabled for self-contained backend operation\n')
    path.write_text(text, encoding="utf-8")
    print("Fixed broken try/except block")
else:
    print("Block not found; no changes made")
