# python-hevc_encoder

Tools to transcode video files into HEVC, experiment with different encoder presets and options, and pixel-peep/compare the source file to your HEVC output.
<br>
<br>
## transcode.py
python script to transcode movies to HEVC using custom encoder options based on source file's resolution. This has only been tested with H.264 MP4 files, but should work with source files with any of the following extensions: ".mp4", ".m4v", ".mov", ".mkv", ".mpg", ".mpeg", ".avi", ".wmv", ".flv", ".webm", ".ts" but YMMV.

```
usage: transcode [-h] (-f FILE | --all) [-q QUALITY] [--preset PRESET] [--baseline | --best] [--small] [--delete]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  filename of movie in source directory
  --all                 transcode all supported movies in source directory
  -q QUALITY, --quality QUALITY
                        HandBrake quality slider value (-12,51)
  --preset PRESET       override video encoder preset
  --baseline            use baseline encoder options
  --best                use highest quality encoder options
  --small               use additional encoder options to minimize filesize at the expense of speed
  --delete              delete output files when complete/interrupted
```
<br>
<br>
## compareEncoding.py
python script to compare screenshots of source and transcoded files

```
usage: compareEncoding.py [-h] [-s] filename [num_frames]

positional arguments:
  filename     Source filename
  num_frames   Number of comparison frames to generate

optional arguments:
  -h, --help   show this help message and exit
  -s, --stack  Also create 2-up stacked comparison
```
<br>
<br>
## Notes:

### Dependencies:
python >= 3.8 at `/usr/local/bin/python3`
[HandBrakeCLI](https://handbrake.fr/downloads2.php) and [ffmpeg](https://www.ffmpeg.org/download.html) on your `$PATH`
[numpy](https://pypi.org/project/numpy/)
[cv2](https://pypi.org/project/opencv-python/)
<br>
<br>
### Tips:
You can also compare multiple encodes created with different presets by appending preset names to the HEVC filename.
e.g.
```
compareEncoding.py
└── source 
    └── test.mp4
└── hevc
    ├── test-RF18.mp4
    └── test-RF24.mp4
```
<br>
<br>
#### Assumptions:
Assumes that H.264 and HEVC encodes have the same base filename and live in "h264" and "hevc" directories relative to compareEncoding.py and transcode.py:<br>
<img src="https://i.imgur.com/1hZwNnV.png" width="200"/>
