import subprocess
import sys
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))

SERVERS = [
    {"script": "app.py",               "label": "Game API       ", "port": 5001},
    {"script": "app_translator.py",     "label": "SSL Translator ", "port": 5002},
    {"script": "flask_sentence_game.py","label": "Sentence Game  ", "port": 5003},
]

def main():
    print("="*55)
    print(" SSL Assistive Tool — Flask Server Launcher")
    print("="*55)

    processes = []
    for srv in SERVERS:
        script_path = os.path.join(BASE, srv["script"])
        proc = subprocess.Popen(
            [sys.executable, script_path],
            cwd=BASE,
        )
        processes.append(proc)
        print(f"  [+] {srv['label']}  ->  http://localhost:{srv['port']}  (PID {proc.pid})")
        time.sleep(1)   # slight stagger to avoid startup races

    print()
    print("  All servers started.  Press Ctrl+C to stop all.")
    print("="*55)

    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n  Stopping all servers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("  All servers stopped.")

if __name__ == "__main__":
    main()
