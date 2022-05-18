import argparse
import h5py
import json
import skvideo.io
import cv2



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

    # Load camera conifiguration
    camera_config = json.loads(h5file.attrs['jsonparam'])

    # Loop over cameras
    for camera_str in h5file:
        camera_name = camera_config[camera_str]['Name']
        output_file = f'{camera_str}_{camera_name}.mp4'
        video_writer = skvideo.io.FFmpegWriter(output_file, outputdict={'-vcodec':'libx264'})
        num_frame = h5file[camera_str].shape[0]
        for i, frame in enumerate(h5file[camera_str]):
            print(f'{camera_str}, {i}/{num_frame}')
            frame_bgr = cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR)
            video_writer.writeFrame(frame)
        video_writer.close()



# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    main()
