import multiprocessing
import subprocess
import sys
import os

def run_logger():
    # Run the logger script
    logger_path = os.path.join(os.path.dirname(__file__), "ad_impressions_logger_with_names.py")
    subprocess.run([sys.executable, logger_path])

def run_flask():
    # Run the Flask app
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    subprocess.run([sys.executable, app_path])

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_logger)
    p2 = multiprocessing.Process(target=run_flask)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
