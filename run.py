import subprocess
import threading
import time
import os

def run_bot():
    subprocess.run(["python", "bot.py"])

def run_web():
    subprocess.run(["python", "app.py"])

t1 = threading.Thread(target=run_bot)
t1.start()

time.sleep(3)

t2 = threading.Thread(target=run_web)
t2.start()

t1.join()
t2.join()