from pathlib import Path

path = Path("Backend/app.py")
text = path.read_text(encoding="utf-8")

old = """    except Exception as e:
        conf, ok, lbl = 0.0, False, f\"Error: {e}\"\n"""
new = """    except Exception:
        # Keep UI friendly and avoid leaking local filesystem paths in errors.
        conf, ok, lbl = 0.0, False, \"Prediction unavailable\"\n"""

if old in text:
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print("Patched run_prediction error label")
else:
    print("Target block not found")
