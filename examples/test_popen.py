import time
import signal
import subprocess

cmd = ['multicam', '-c', 'camera_config.ini',  '-n']
print(f'starting process: {cmd}')

proc = subprocess.Popen(cmd)

print(f'sleeping')
time.sleep(10)

print(f'sending signal SIGINT')
proc.send_signal(signal.SIGINT)


