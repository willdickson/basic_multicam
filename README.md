##  basic_multicam 

A simple python app for recording from multiple FLIR Spinnaker cameras.


```console
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

```


