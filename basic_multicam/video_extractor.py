"""
video_extractor: command line utility for extracting video created by multicam


  usage: tmp.py [-h] [--format FORMAT] filename
  
  Extracts videos from the hdf5 file created by multicam
  
  positional arguments:
    filename              name of hdf5 file with camera frames
  
  optional arguments:
    -h, --help            show this help message and exit
    --format FORMAT, -f FORMAT
                          video format
"""

import os
import argparse
import h5py
import json
import skvideo.io
import cv2
import tqdm
import numpy as np

def main():

    description_str = 'Extracts videos from the hdf5 file created by multicam'
    parser = argparse.ArgumentParser(description=description_str)

    parser.add_argument(
            'filename', 
            metavar='filename', 
            type=str,
            help='name of hdf5 file with camera frames'
            )

    parser.add_argument(
            '--format', '-f', 
            help='video format', 
            default='h264'
            )

    args = parser.parse_args()

    print(f'args: {args}')

    h5file = h5py.File(args.filename, 'r')

    path_to_h5file, h5file_name = os.path.split(args.filename)
    h5file_base_name, _ = os.path.splitext(h5file_name)

    # Load camera conifiguration
    camera_config = json.loads(h5file.attrs['jsonparam'])

    # Remove for now as datetime string will be added twice for old files.
    # -----------------------------------------------------------------------------------
    #try:
    #    metadata = camera_config['Metadata']
    #except KeyError:
    #    metadata = ''
    # -----------------------------------------------------------------------------------

    # Save camera_configuration
    camera_config_file_path = os.path.join(path_to_h5file, f'camera_config_{h5file_base_name}.json')
    with open(camera_config_file_path, 'w') as f:
        json.dump(camera_config, f, indent=4, sort_keys=True)

    # Loop over cameras
    for data_str in h5file:
        if '_t' in data_str:
            # Camera timestamps
            t_stamps = h5file[data_str][()]
            output_file  = os.path.join(path_to_h5file, f'{data_str}_{h5file_base_name}.txt')
            np.savetxt(output_file, t_stamps)
        else:
            # Camera data
            camera_name = camera_config[data_str]['Name']
            output_file = os.path.join(path_to_h5file, f'{data_str}_{camera_name}_{h5file_base_name}.mp4')
            framerate_str = str(camera_config[data_str]['AcquisitionFrameRate'])
            inputdict={'-framerate': framerate_str} 
            outputdict={'-vcodec':'libx264', '-r': framerate_str}
            video_writer = skvideo.io.FFmpegWriter(output_file, inputdict=inputdict, outputdict=outputdict)
            num_frame = h5file[data_str].shape[0]
            for frame in tqdm.tqdm(iterable=h5file[data_str], total=num_frame, desc='Extracting...', ascii=False, ncols=75):
                video_writer.writeFrame(frame)
            video_writer.close()


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    main()
