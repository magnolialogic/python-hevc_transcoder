#### Dependencies:
python >= 3.8 at `/usr/local/bin/python3`

[HandBrakeCLI](https://handbrake.fr/downloads2.php) and [ffmpeg](https://www.ffmpeg.org/download.html) on your `$PATH`

[numpy](https://pypi.org/project/numpy/)

[cv2](https://pypi.org/project/opencv-python/)

# transcode.py
python script to transcode movies to HEVC using custom encoder options based on source file's resolution

```
usage: transcode [-h] (-f FILE | --all) [-q QUALITY] [--baseline | --best] [--preset PRESET] [--small] [--delete]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  filename of movie in source directory
  --all                 transcode all supported movies in source directory
  -q QUALITY, --quality QUALITY
                        HandBrake quality slider value (-12,51)
  --baseline            use baseline options
  --best                use highest quality options
  --preset PRESET       override video encoder preset
  --small               add additional encoder options to minimize filesize at the expense of speed
```

# compareEncoding.py
python script to compare screenshots of source and transcoded files


```
usage: compareEncoding.py [-h] [-s] filename [num_frames]

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
└── source 
    └── test.mp4
└── hevc
    ├── test-rf18.mp4
    └── test-rf24.mp4
```

#### Assumptions:

Assumes that H.264 and HEVC encodes have the same base filename and live in "h264" and "hevc" directories relative to compareEncoding.py and transcode.py:<br>
<img src="https://i.imgur.com/1hZwNnV.png" width="200"/>
