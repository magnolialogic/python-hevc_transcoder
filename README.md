# compareEncoding
python script to compare H.264 and HEVC rips of the same file


#### usage:
`python compareEncoding.py <filename.mp4> <numComparisonFrames> -s/--stack`

e.g.
`python3 compareEncoding.py all`
or
`python3 compareEncoding.py Taipei101Fireworks.mp4 10`


#### dependencies:
[numpy](https://pypi.org/project/numpy/)<br>
[cv2](https://pypi.org/project/opencv-python/)


Assumes that H.264 and HEVC encodes have the same base filename and live in "h264" and "hevc" directories relative to compareEncoding.py:<br>
<img src="https://i.imgur.com/1hZwNnV.png" width="200"/>

You can also compare multiple encodes created with different presets by appending preset names to the HEVC filename.

e.g.
```
compareEncoding.py
└── h264
    └── test.mp4
└── ao
    ├── test-rf18.mp4
    └── test-rf24.mp4
```
