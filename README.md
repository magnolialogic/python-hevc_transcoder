#### Dependencies:
[HandBrakeCLI](https://handbrake.fr/downloads2.php) and [ffmpeg](https://www.ffmpeg.org/download.html) on your `$PATH`

[numpy](https://pypi.org/project/numpy/)

[cv2](https://pypi.org/project/opencv-python/)

# transcode.py
python script to transcode a given H.264 file to HEVC using preset with RF appropriate for resolution/bitrate (unless preset manually selected with `--preset` option)

```
usage: transcode [-h] (--file FILE | --all) [--preset PRESET] [--delete]

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  Relative path to H264 file (e.g. h264/example.mp4)
  --all                 Transcode all H264 files in h264 directory
  --preset PRESET, -p PRESET
                        Name of HandBrake JSON preset file
  --delete              Delete output files when complete/interrupted
```


# compareEncoding.py
python script to compare H.264 and HEVC rips of the same file.

```
usage: compareEncoding [-h] [-s] filename [num_frames]

positional arguments:
  filename     H264 filename
  num_frames   Number of frames to generate

optional arguments:
  -h, --help   show this help message and exit
  -s, --stack  Also create 2-up stacked comparison
```

You can also compare multiple encodes created with different presets by appending preset names to the HEVC filename.

e.g.
```
compareEncoding.py
└── h264
    └── test.mp4
└── hevc
    ├── test-rf18.mp4
    └── test-rf24.mp4
```

#### Assumptions:

Assumes that H.264 and HEVC encodes have the same base filename and live in "h264" and "hevc" directories relative to compareEncoding.py and transcode.py:<br>
<img src="https://i.imgur.com/1hZwNnV.png" width="200"/>
