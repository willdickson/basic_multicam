"""
basic_multicam:  implements the multicam command line application


  usage: multicam [-h] [--config CONFIG] [--output OUTPUT] [--norecord]
                [--softtrig] [--metadata METADATA]
  
  Acquires simultaneous images from multiple cameras and save to an hdf5 file.
  
  optional arguments:
    -h, --help            show this help message and exit
    --config CONFIG, -c CONFIG
                          camera configuration file
    --output OUTPUT, -o OUTPUT
                          output file
    --norecord, -n        option to not record video
    --softtrig, -s        use software camera trigger
    --metadata METADATA, -m METADATA
                          meta data to be added to hdf5 file
"""

import os
import sys
import time
import queue
import signal
import argparse
import collections
import threading
import configparser
import cv2
import numpy as np
import platform
import EasyPySpin
import h5_logger

OS_TYPE = platform.system()
if OS_TYPE == 'Windows':
    from pyspin import PySpin
else:
    import PySpin

DEFAULT_CONFIG_FILE = 'camera_config.ini'
if OS_TYPE == 'Windows':
    DEFAULT_CONFIG_DIR = os.path.join(os.environ['USERPROFILE'], '.config', 'multicam')
else:
    DEFAULT_CONFIG_DIR = os.path.join(os.environ['HOME'], '.config', 'multicam')

done = False
def handle_sigint(signum, frame):
    global done
    done = True
signal.signal(signal.SIGINT, handle_sigint)

PropertyConverter = { 
        'AcquisitionFrameRateEnable': bool, 
        'AcquisitionFrameRate': float,  
        'GainAuto': str, 
        'ExposureAuto': str,
        'TriggerMode': str, 
        'TriggerDelay': float, 
        'Width': int, 
        'Height': int, 
        'OffsetX': int, 
        'OffsetY': int,
        'ExposureTime': float,
        'Gain': float, 
        }

AcquisitionParamConverter = {
        'Duration': float,
        }


def get_config(filename):
    """
    Read camera configuration .ini file.  Convert properties to appropriate
    types using PropertyConverter data.  Return dictionary of camera settings.

    Argument:

      filename:  name of camera configuration file

    Return:

      camera_config_dict: dictionary of properties for each camera
    """

    # Check that file exists
    if not os.path.exists(filename):
        raise RuntimeError(f"camera configuration file, {filename}, doesn't exist")

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

    # Load in optional acquisition configuration 
    acquisition_config_dict = {}
    try:
        acquisition_config_dict = dict(config['Acquisition'])
    except KeyError:
        pass
    for k,v in acquisition_config_dict.items():
        acquisition_config_dict[k] = AcquisitionParamConverter[k](v)

    return camera_config_dict, acquisition_config_dict



def setup_cameras(config, args):
    """
    Creates VideoCapture objects for each camera and sets camera properties based on 
    camera configuration.

    Arguments:
    
      config:  camera configuration dictionary
      args:    program command line arguments

    Return:

      cap_dict:  dictionary of camera name to VideoCapture objects.
      
    """
    cap_dict = {}
    print()
    print('setting up cameras')
    for camera, prop_dict in config.items():
        print(f'  {camera}')
        cap_dict[camera] =  EasyPySpin.VideoCapture(prop_dict['SerialNumber'])
        cap_dict[camera].setExceptionMode(True)
        cap_dict[camera].grabTimeout = 100 # DEBUG: move this to constant??
        for prop_name, value in prop_dict.items():
            if prop_name in PropertyConverter:
                cap_dict[camera].set_pyspin_value(prop_name, value)
        if args.softtrig:
            # override hardware trigger mode if softtrig option selected
            cap_dict[camera].set_pyspin_value('TriggerMode', 'Off')
    print()
    return cap_dict


class DisplayHandler:
    """
    Implements a simple simple window video display.  The current camera image
    is shown in an opencv named window. Double clicking on the window cycles
    through the currently selected camera. The run method should be run as the
    target of the thread. 
    """

    def __init__(self, camera_config):
        self.queue = queue.Queue() 
        self.camera_config = camera_config
        self.display_cam_num = 0
        self.display_name = 'cameras'

    def on_mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDBLCLK:
            self.display_cam_num += 1

    def run(self):

        cv2.namedWindow(self.display_name)
        cv2.setMouseCallback(self.display_name, self.on_mouse_callback)

        while True:
            frame_dict = None
            try:
                frame_dict, fps = self.queue.get()
            except queue.Empty():
                continue

            camera_list = [camera for camera in frame_dict if not '_t' in camera]
            cam_num = self.display_cam_num%len(camera_list)
            camera = camera_list[cam_num]
            frame = frame_dict[camera]

            name = self.camera_config[camera]['Name'].lower()
            info_str = f'({cam_num+1}/{len(camera_list)}) {name} {int(fps[camera]):03d}fps'
            cv2.putText(frame, info_str, (10,27), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 1, 2)
            cv2.imshow(self.display_name, frame)
            cv2.waitKey(1)


def main():
    """
    Main entry point multicam command line application
    """
    global done

    description_str = 'Acquires simultaneous images from multiple cameras and save to an hdf5 file.'

    parser = argparse.ArgumentParser(description=description_str)
    parser.add_argument(
            '--config', '-c', 
            type=str, 
            help='camera configuration file', 
            default='' 
            )

    parser.add_argument(
            '--output', '-o', 
            help='output file', 
            default='data.hdf5'
            )

    parser.add_argument(
            '--norecord', '-n', 
            help='option to not record video', 
            action='store_true'
            )

    parser.add_argument(
            '--softtrig', '-s',
            help='use software camera trigger',
            action='store_true'
            )

    parser.add_argument(
            '--metadata', '-m',
            type=str,
            help='meta data to be added to hdf5 file',
            default='',
            )

    args = parser.parse_args()

    # Check configuration
    config_file = args.config
    if not config_file:
        curdir_config_file = os.path.join(os.curdir, DEFAULT_CONFIG_FILE)
        if os.path.exists(curdir_config_file):
            config_file = curdir_config_file
        else:
            config_file = os.path.join(DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE)
    print(f'config_file: {config_file}')

    # Setup cameras based configuration
    camera_config, acquisition_config = get_config(config_file)
    cap_dict = setup_cameras(camera_config, args)

    if not args.norecord:
        param_attr = dict(camera_config)
        param_attr['Metadata'] = args.metadata
        logger = h5_logger.H5Logger(args.output, param_attr=param_attr)

    display_handler = DisplayHandler(camera_config)
    display_thread = threading.Thread(target=display_handler.run, daemon=True)
    display_thread.start()

    # Set timing data
    t_start = time.time()
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

    duration = None
    try:
        duration = acquisition_config['Duration']
    except KeyError:
        pass

    while not done:

        frame_dict = collections.OrderedDict() 

        for camera, cap in cap_dict.items(): 
            try:
                rval, frame = cap.read()
            except PySpin.SpinnakerException as err:
                print('PySpin.SpinnakerException')
                break

            if not rval:
                frame_dict[camera] = dummy_frame[camera]
            else:
                frame_dict[camera] = frame

            t_now = time.time()
            dt = t_now - t_last[camera]
            t_last[camera] = t_now
            frame_dict[f'{camera}_t'] = t_now

            try:
                fps[camera] = 0.95*fps[camera] + 0.05*(1.0/dt)
            except ZeroDivisionError:
                pass

        if frame_dict:
            if not args.norecord:
                logger.add(frame_dict)

            if display_handler.queue.qsize() == 0: 
                display_handler.queue.put((frame_dict, fps))

        if duration is not None:
            done = time.time() - t_start > duration

    for camera, cap in cap_dict.items():
        cap.release()




