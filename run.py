import subprocess
import sys
import time
import os
import signal
import webbrowser

def run_system():
    print("="*60)
    print("       Smart Elderly Nutritionist - System Start (Python)")
    print("="*60)

    # Get the python executable path
    python_exe = sys.executable

    # 1. Start Backend (FastAPI)
    print(f"[1/2] Starting Backend API (FastAPI) on port 8002...")
    # Using Popen to run in parallel
    backend_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "main:app", "--reload", "--port", "8002"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        shell=True
    )

    # Wait a bit for backend to initialize
    time.sleep(3)

    # 2. Start Frontend (Streamlit)
    print(f"[2/2] Starting Frontend UI (Streamlit) on port 8501...")
    frontend_process = subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        shell=True
    )

    print("\n" + "="*60)
    print("System is running!")
    print("-"*60)
    print("Backend API:   http://localhost:8002/docs")
    print("Frontend App:  http://localhost:8501")
    print("-"*60)
    print("Opening browser...")
    
    # Open browser automatically
    time.sleep(2) # Give streamlit a moment to start
    webbrowser.open("http://localhost:8501")
    
    print("Press Ctrl+C to stop the system...")
    print("="*60)

    try:
        # Keep the script running to monitor processes
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if backend_process.poll() is not None:
                print("Backend process ended unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("Frontend process ended unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping system...")
    finally:
        # Kill processes on exit
        print("Terminating processes...")
        # Note: taskkill is Windows specific, but effective for shell=True
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_process.pid)], capture_output=True)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], capture_output=True)
        else:
            backend_process.terminate()
            frontend_process.terminate()
        print("System stopped.")

if __name__ == "__main__":
    run_system()
