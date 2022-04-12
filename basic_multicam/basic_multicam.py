import sys
import cv2
import time
import queue
import signal
import threading
import EasyPySpin
import configparser
import numpy as np
import h5_logger

done = False
def handle_sigint(signum, frame):
    global done
    done = True
    print(f'sigint_handler: {done}')
signal.signal(signal.SIGINT, handle_sigint)


PropertyConverter = { 
        'AcquisitionFrameRateEnable': bool, 
        'GainAuto': str, 
        'ExposureAuto': str,
        'TriggerMode': str, 
        'TriggerDelay': float, 
        'Width': int, 
        'Height': int, 
        'OffsetX': int, 
        'OffsetY': int,
        'AcquisitionFrameRate': float,  
        'ExposureTime': float,
        'Gain': float, 
        }


def get_config(filename):

    # Read configuration from file
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(filename)
    common_config_dict = {k:v for k,v in config['CameraCommon'].items()}
    camera_sections = [item for item in config if 'Camera' in item and not 'Common' in item]
    camera_config_dict = {}

    # Load section in config dict
    for section in camera_sections:
        camera_config_dict[section] = dict(common_config_dict)
        camera_config_dict[section].update({k:v for k,v in config[section].items()})

    # Convert camera properties to appropriate types
    for section, config_dict in camera_config_dict.items():
        for prop_name, value in config_dict.items():
            try:
                converter = PropertyConverter[prop_name]
            except KeyError:
                continue
            config_dict[prop_name] = converter(value)

    return camera_config_dict


def setup_cameras(config):
    cap_dict = {}
    print('setting up cameras')
    for camera, prop_dict in config.items():
        print(camera)
        cap_dict[camera] =  EasyPySpin.VideoCapture(prop_dict['SerialNumber'])
        for prop_name, value in prop_dict.items():
            if prop_name in PropertyConverter:
                cap_dict[camera].set_pyspin_value(prop_name, value)
    print()
    return cap_dict


class DisplayHandler:

    def __init__(self, camera_config):
        self.queue = queue.Queue() 
        self.camera_config = camera_config

    def run(self):
        while True:
            frame_dict = None
            try:
                frame_dict, fps = self.queue.get()
            except queue.Empty():
                continue
            for camera, frame in frame_dict.items():
                name = self.camera_config[camera]['Name']
                fps_str = f'{int(fps[camera]):03d}'
                cv2.putText(frame, fps_str, (10,25), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 1, 2)
                cv2.imshow(name, frame)
            cv2.waitKey(100)


def main():

    config_filename = sys.argv[1]
    camera_config = get_config(config_filename)
    cap_dict = setup_cameras(camera_config)

    logger = h5_logger.H5Logger('data.hdf5', param_attr=camera_config)

    display_handler = DisplayHandler(camera_config)
    display_thread = threading.Thread(target=display_handler.run, daemon=True)
    display_thread.start()

    # Set timing data
    t_last = {}
    fps = {}
    for camera in cap_dict:
        t_last[camera] = time.time()
        fps[camera] = 0.0

    # Create dumm frames - for cases of missed frames
    dummy_frame = {}
    for camera in  camera_config:
        w = camera_config[camera]['Width']
        h = camera_config[camera]['Height']
        dummy_frame[camera] = np.zeros((h,w),dtype=np.uint8)

    while not done:

        frame_dict = {}
        for camera, cap in cap_dict.items(): 
            rval, frame = cap.read()
            if not rval:
                print(f'{camera} dummy frame')
                frame_dict[camera] = dummy_frame[camera]
            else:
                frame_dict[camera] = frame

            t_now = time.time()
            dt = t_now - t_last[camera]
            t_last[camera] = t_now
            fps[camera] = 0.9*fps[camera] + 0.1*(1.0/dt)

        logger.add(frame_dict)
        if display_handler.queue.qsize() == 0:
            display_handler.queue.put((frame_dict, fps))


    for camera, cap in cap_dict.items():
        cap.release()




