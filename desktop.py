import webview
import subprocess
import threading
import os
import time
import sys
import signal

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def start_laravel():
    """Start the Laravel server."""
    print("Starting Laravel server...")
    subprocess.Popen(
        ["php", "artisan", "serve", "--port=8000"],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def start_worker():
    """Start the AI worker."""
    print("Starting AI worker...")
    subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "ai_worker", "worker.py")],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def start_queue():
    """Start the Laravel queue listener."""
    print("Starting queue listener...")
    subprocess.Popen(
        ["php", "artisan", "queue:listen", "--tries=1"],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def cleanup(signum, frame):
    """Cleanup processes on exit."""
    print("Cleaning up processes...")
    # This is a bit rough, but kills processes on the ports we use
    if sys.platform == "win32":
        os.system("taskkill /f /im php.exe")
        os.system("taskkill /f /im python.exe")
    else:
        os.system("pkill -f 'php artisan serve'")
        os.system("pkill -f 'php artisan queue:listen'")
        os.system("pkill -f 'worker.py'")
    sys.exit(0)

import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == "__main__":
    # Register cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    if is_port_in_use(8000):
        print("Error: Port 8000 is already in use. Please stop other Laravel instances.")
        sys.exit(1)

    # Start backend services in threads
    threading.Thread(target=start_laravel, daemon=True).start()
    threading.Thread(target=start_worker, daemon=True).start()
    threading.Thread(target=start_queue, daemon=True).start()

    # Wait for Laravel to start
    print("Waiting for services to initialize...")
    time.sleep(3)

    # Create the webview window with debugging enabled
    window = webview.create_window(
        'AI Video Creator',
        'http://127.0.0.1:8000',
        width=1200,
        height=800,
        min_size=(1000, 700),
        text_select=False,
        frameless=False
    )

    # Start the webview with debug enabled
    webview.start(debug=True)

    # When window is closed, cleanup
    cleanup(None, None)
