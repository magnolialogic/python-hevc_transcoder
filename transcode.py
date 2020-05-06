#!/usr/local/bin/python3

import argparse
from datetime import datetime
import json
import os
import shlex
import signal
import subprocess
import sys

class MP4(object):
	def __init__(self, path):
		signal.signal(signal.SIGINT, self.signal_handler)
		cmd = "ffprobe -v quiet -print_format json -show_streams " + path
		metadata = subprocess.check_output(shlex.split(cmd)).decode("utf-8")
		metadata = json.loads(metadata)["streams"][0]
		self.input_file = path
		self.height = int(metadata["height"])
		self.width = int(metadata["width"])
		self.duration = metadata["duration"]
		self.filename = os.path.splitext(os.path.relpath(self.input_file, "h264"))[0]
		self.filesize = os.path.getsize(self.input_file)
		self.bitrate = metadata["bit_rate"]
		self.codec = metadata["codec_name"]
		if args.preset:
			self.preset_name = args.preset
			self.preset_file = "presets/" + args.preset + ".json"
		else:
			self.map_preset()
		self.output_file = "hevc/" + self.filename + "_" + self.preset_name + ".mp4"
		self.log = "performance/" + self.filename + "-" + self.preset_name + ".log"
		self.arguments = shlex.split("HandBrakeCLI --preset-import-file " + self.preset_file + " --preset " + self.preset_name + " --input " + self.input_file + " --output " + self.output_file + " --optimize")
		self.validate()
		self.summarize()
	
	def validate(self):
		if any(value is None for attribute, value in self.__dict__.items()):
			print("FATAL: MP4.validate(): found null attribute for " + self.input_file)
			sys.exit(1)
	
	def summarize(self):
		import pprint
		print()
		print(self.filename)
		pprint.pprint(vars(self))
		print()
	
	def map_preset(self):
		# Select correct RF based on resolution/bitrate
		self.preset_name = "RF23"
		self.preset_file = "presets/RF23.json"
	
	def signal_handler(self, sig, frame):
		self.cleanup()
	
	def cleanup(self):
		if args.delete:
			if os.path.exists(source.output_file): os.remove(source.output_file)
			if os.path.exists(source.log): os.remove(source.log)

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-f", "--file", help="Relative path to H264 file (e.g. h264/example.mp4)")
group.add_argument("--all", action="store_true", help="Transcode all H264 files in h264 directory")
parser.add_argument("-p", "--preset", help="Name of HandBrake JSON preset file", required=False)
parser.add_argument("-d", "--delete", action="store_true", help="Delete output files when complete/interrupted")
args = parser.parse_args()
valid_arguments = False

if not set(["h264", "hevc", "performance", "presets"]).issubset(set(os.listdir())):
	print("FATAL: invalid working directory!")
elif args.file and not os.path.exists(args.file):
	print("FATAL:", args.file, "not found!")
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
	sys.exit("Invalid command-line arguments.")
elif args.all and args.preset:
	print("Warning! Combining --all and --preset options is not recommended and may not produce optimal HEVC transcodes.")
	while "need response":
		reply = str(input("Proceed? (y/n) " )).lower().strip()
		if reply[0] == "y":
			break
		if reply[0] == "n":
			sys.exit("Aborting invocation with --all and --preset options.")

source_files = []

if args.all:
	for file in os.listdir("h264"):
		if file.endswith(".mp4"):
			source_files.append("h264/" + file)
else:
	source_files.append(args.file)

for file in source_files:
	source = MP4(file)
	if not os.path.exists(source.output_file):
		print(shlex.join(source.arguments))
		with open(source.log, "w") as log:
			start_time = datetime.now()
			with subprocess.Popen(source.arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1) as process:
				for line in process.stdout:
					sys.stdout.write(line)
					log.write(line)
			end_time = datetime.now()
			elapsed_time = end_time - start_time
			sys.stdout(write(elapsed_time))
			log.write(str(elapsed_time))
	else:
		print(source.output_file, "already exists, skipping.")
	print()
	if args.delete: source.cleanup()

# Add date to "done" print
sys.exit("Done.\n")