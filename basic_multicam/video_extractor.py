import os
import argparse
import h5py
import json
import skvideo.io
import cv2
import tqdm



def main():

    parser = argparse.ArgumentParser(description='extract videos from hdf5 file created by multicam')

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

    path_to_h5file, _ = os.path.split(args.filename)

    # Load camera conifiguration
    camera_config = json.loads(h5file.attrs['jsonparam'])
    metadata = camera_config['Metadata']

    # Save camera_configuration
    camera_config_file_path = os.path.join(path_to_h5file, f'camera_config_{metadata}.json')
    with open(camera_config_file_path, 'w') as f:
        json.dump(camera_config, f, indent=4, sort_keys=True)

    # Loop over cameras
    for camera_str in h5file:
        camera_name = camera_config[camera_str]['Name']
        output_file = os.path.join(path_to_h5file, f'{camera_str}_{camera_name}_{metadata}.mp4')
        video_writer = skvideo.io.FFmpegWriter(output_file, outputdict={'-vcodec':'libx264'})
        num_frame = h5file[camera_str].shape[0]
        for frame in tqdm.tqdm(iterable=h5file[camera_str], total=num_frame, desc='Extracting...', ascii=False, ncols=75):
            video_writer.writeFrame(frame)
        video_writer.close()


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    main()
