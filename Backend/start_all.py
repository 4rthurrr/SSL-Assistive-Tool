import subprocess
import sys
import time

def main():
    print("🚀 Starting both backend servers...")
    
    # Start app.py
    process1 = subprocess.Popen([sys.executable, "app.py"])
    print("✅ Started app.py (Main Backend)")
    
    # Wait a moment to ensure ports don't clash on startup
    time.sleep(2)
    
    # Start flask_sentence_game.py
    process2 = subprocess.Popen([sys.executable, "flask_sentence_game.py"])
    print("✅ Started flask_sentence_game.py (Sentence Game Backend)")
    
    print("\n⚠️ Press Ctrl+C to stop both servers\n")
    
    try:
        # Wait for both processes
        process1.wait()
        process2.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        process1.terminate()
        process2.terminate()
        process1.wait()
        process2.wait()
        print("✅ Servers stopped.")

if __name__ == "__main__":
    main()
