import subprocess
import sys
import os
import time

# Backend root directory (where this script lives)
BASE = os.path.dirname(os.path.abspath(__file__))

SERVERS = [
    {
        "script": os.path.join(BASE, "app.py"),
        "label":  "Game API       ",
        "port":   5001,
    },
    {
        "script": os.path.join(BASE, "text-to-sign", "services", "app_translator.py"),
        "label":  "SSL Translator ",
        "port":   5002,
    },
    {
        "script": os.path.join(BASE, "game-engine", "flask_sentence_game.py"),
        "label":  "Sentence Game  ",
        "port":   5003,
    },
]


def main():
    print("=" * 55)
    print(" SSL Assistive Tool — Flask Server Launcher")
    print("=" * 55)

    processes = []
    for srv in SERVERS:
        if not os.path.exists(srv["script"]):
            print(f"  [!] MISSING: {srv['script']}")
            continue

        proc = subprocess.Popen(
            [sys.executable, srv["script"]],
            cwd=BASE,           # all servers run relative to Backend root
        )
        processes.append(proc)
        print(
            f"  [+] {srv['label']}  ->  http://localhost:{srv['port']}"
            f"  (PID {proc.pid})"
        )
        time.sleep(1)   # slight stagger to avoid startup races

    if not processes:
        print("  No servers started — check paths above.")
        return

    print()
    print("  All servers started.  Press Ctrl+C to stop all.")
    print("=" * 55)

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
