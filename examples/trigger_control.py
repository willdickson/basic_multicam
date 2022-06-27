from camera_trigger import CameraTrigger

trigger_port = '/dev/ttyUSB0'
cam_hz = 60 

trig = CameraTrigger(trigger_port) 
trig.set_freq(cam_hz) 
trig.set_width(10) 
trig.stop()

input('press enter to start trigger')
trig.start()

input('press enter to stop trigger')

trig.stop()
trig.close()
