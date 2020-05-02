#!/usr/bin/python3

import argparse
import json
import os
import shlex
import subprocess
import sys

class MP4File(object):
	def __init__(self, path):
		cmd = "ffprobe -v quiet -print_format json -show_streams " + path
		metadata = subprocess.check_output(shlex.split(cmd)).decode("utf-8")
		metadata = json.loads(metadata)["streams"][0]
		self.path = path
		self.height = int(metadata["height"])
		self.width = int(metadata["width"])
		self.duration = metadata["duration"]
		self.filesize = os.path.getsize(self.path)
		self.bitrate = metadata["bit_rate"]
		self.codec = metadata["codec_name"]
		if args.preset:
			self.preset = "presets/" + args.preset + ".json"
		else:
			self.map_preset()
		self.validate()
		self.summarize()
	
	def validate(self):
		if any(value is None for attribute, value in self.__dict__.items()):
			print("FATAL: MP4File.validate(): found null attribute for " + self.path)
			sys.exit(1)
	
	def summarize(self):
		from pprint import pprint
		pprint(vars(self))
	
	def map_preset(self):
		# If 720P, 
		# If 1080P
		# If 
		self.preset = "presets/auto.json"

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-f", "--file", help="Relative path to H264 file (e.g. h264/example.mp4)")
group.add_argument("--all", action="store_true", help="Transcode all H264 files in h264 directory")
parser.add_argument("-p", "--preset", help="Name of HandBrake JSON preset file", required=False)
args = parser.parse_args()
valid_arguments = False

if not set(["h264", "hevc", "presets"]).issubset(set(os.listdir())):
	print("FATAL: invalid working directory!")
elif args.file and not os.path.exists(args.file):
	print("FATAL: " + args.file + " not found!")
elif args.preset and not os.path.exists("presets/" + args.preset + ".json"):
	presets = [filename for filename in os.listdir("presets") if os.path.splitext(filename)[1] == ".json"]
	if len(presets) == 0:
		print("FATAL: no .json preset found in presets directory.")
	else:
		print("FATAL: must use one of the following presets:")
		for preset in sorted(presets):
			print(" " + os.path.splitext(preset)[0])
else:
	valid_arguments = True
if not valid_arguments:
	print("Exiting.")
	sys.exit(1)
elif args.all and args.preset:
	print("Warning! Combining --all and --preset options is not recommended and may not produce optimal HEVC transcodes.")
	while "need response":
		reply = str(input("Proceed? (y/n) " )).lower().strip()
		if reply[0] == "y":
			break
		if reply[0] == "n":
			print("Exiting.")
			sys.exit(0)

source_files = []

if args.all:
	for file in os.listdir("h264"):
		if file.endswith(".mp4"):
			source_files.append("h264/" + file)
else:
	source_files.append(args.file)

for file in source_files:
	h264_file = MP4File(file)
	print()

sys.exit(0)