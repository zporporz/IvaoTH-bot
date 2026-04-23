import subprocess
import threading
import time

def run_bot():
    subprocess.run(["python", "bot.py"])

def run_api():
    subprocess.run(["python", "app.py"])

t1 = threading.Thread(target=run_bot)
t2 = threading.Thread(target=run_api)

t1.start()
time.sleep(2)   # รอ API / Bot แยกเริ่มทีละนิด
t2.start()

t1.join()
t2.join()