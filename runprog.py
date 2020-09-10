from time import sleep
import subprocess
import multiprocessing

def thread_():
    subprocess.run(["python3", "subreddit.py"])

while True:
    thread = multiprocessing.Process(target = thread_, args = ())
    thread.start()

    sleep(60*60*2)

    print("closing...")
    file = open("pid.txt", "r")
    pid = file.readlines()[0]
    file.close()

    subprocess.run(["kill", pid])
    thread.terminate()

    print("killed ", pid)

