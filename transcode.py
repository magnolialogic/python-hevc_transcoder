#!/usr/local/bin/python3

import argparse
from datetime import datetime
import json
import os
from pprint import pprint
import shlex
import signal
import subprocess
import sys

class Session():
	class Settings:
		class Low:
			RF = 21 # 18-22
			ENCOPTS = "ctu=32:qg-size:16"
		
		class Medium:
			RF = 22 # 19-23
			ENCOPTS = "ctu=32:qg-size:32"
		
		class High:
			RF = 23 # 20-24
			ENCOPTS = "ctu=64:qg-size:64"
		
		class Ultra:
			RF = 26 # 22-28
			ENCOPTS = "ctu=64:qg-size:64"
	
	def __init__(self, file):
		signal.signal(signal.SIGINT, self.signal_handler)
		
		# Get source file metadata
		cmd = "ffprobe -v quiet -print_format json -show_streams " + file
		metadata = subprocess.check_output(shlex.split(cmd)).decode("utf-8")
		metadata = json.loads(metadata)["streams"][0]
		
		# Populate metadata-based attributes
		self.source_path = file
		self.height = int(metadata["height"])
		self.width = int(metadata["width"])
		self.duration = metadata["duration"]
		self.filename = os.path.splitext(os.path.relpath(self.source_path, "source"))[0]
		self.filesize = os.path.getsize(self.source_path)
		self.bitrate = metadata["bit_rate"]
		self.codec = metadata["codec_name"]
		
		# Create empty attributes for dynamic session options
		self.quality = None
		self.preset = None
		self.preset_name = None
		self.encopts = None
		
		# Construct session options and parameters
		self.map_options()
		self.output_filename_decorator = "_RF" + str(self.quality)
		if args.best:
			self.output_filename_decorator += "_Best"
		elif args.baseline:
			self.output_filename_decorator += "_Baseline"
		if args.small:
			self.output_filename_decorator += "_Small"
		self.output_path = "hevc/" + self.filename + self.output_filename_decorator + ".mp4"
		self.log_path = "performance/" + self.filename + self.output_filename_decorator + ".log"
		
		# Build HandBrakeCLI command
		self.arguments = "HandBrakeCLI --encoder-preset {video_preset} --preset-import-file presets.json --preset {preset_name} --quality {quality} --encopts {encopts} --input {source_path} --output {output_path}".format(video_preset=self.preset, preset_name=self.preset_name, quality=str(self.quality), encopts=self.encopts, source_path=self.source_path, output_path=self.output_path)
		
		# Validate and finish
		self.validate()
		self.summarize()
	
	def validate(self):
		if any(value is None for attribute, value in self.__dict__.items()):
			sys.exit("FATAL: Session.validate(): found null attribute for " + self.source_path)
	
	def summarize(self):
		print()
		print(self.source_path)
		pprint(vars(self))
		print()
	
	def map_options(self):
		# Start with settings based on source resolution
		if self.height < 720:
			self.quality = self.Settings.Low.RF
			self.encopts = self.Settings.Low.ENCOPTS
		elif 720 <= self.height < 1080:
			self.quality = self.Settings.Medium.RF
			self.encopts = self.Settings.Medium.ENCOPTS
		elif 1080 <= self.height < 2160:
			self.quality = self.Settings.High.RF
			self.encopts = self.Settings.High.ENCOPTS
		elif 2160 <= self.height:
			self.quality = self.Settings.Ultra.RF
			self.encopts = self.Settings.Ultra.ENCOPTS
		
		# Override defaults based on command-line arguments
		if args.best:
			self.preset_name = "Best"
		elif args.baseline:
			self.preset_name = "Baseline"
		else:
			self.preset_name = "Default"
		
		if args.preset:
			self.preset = args.preset.lower()
		else:
			self.preset = "slow"
		
		if args.quality:
			self.quality = args.quality
		
		if args.small:
			self.encopts += ":tu-intra-depth=3:tu-inter-depth=3"
	
	def signal_handler(self, sig, frame):
		self.cleanup()
		sys.exit("Caught ^c: exiting.")
	
	def cleanup(self):
		if args.delete:
			if os.path.exists(self.output_path):
				os.remove(self.output_path)
			if os.path.exists(self.log_path):
				os.remove(self.log_path)

# Define command-line arguments
parser = argparse.ArgumentParser()
files_group = parser.add_mutually_exclusive_group(required=True)
files_group.add_argument("-f", "--file", help="filename of movie in source directory")
files_group.add_argument("--all", action="store_true", help="transcode all supported movies in source directory")
parser.add_argument("-q", "--quality", type=int, help="HandBrake quality slider value (-12,51)")
parser.add_argument("--preset", help="override video encoder preset")
preset_group = parser.add_mutually_exclusive_group(required=False)
preset_group.add_argument("--baseline", action="store_true", help="use baseline encoder options")
preset_group.add_argument("--best", action="store_true", help="use highest quality encoder options")
parser.add_argument("--small", action="store_true", help="use additional encoder options to minimize filesize at the expense of speed")
parser.add_argument("--delete", action="store_true", help="delete output files when complete/interrupted")
args = parser.parse_args()
valid_arguments = False

# Validate command-line arguments
if not set(["source", "presets.json"]).issubset(set(os.listdir())):
	print("FATAL: invalid working directory!")
elif args.file and not os.path.exists(args.file):
	print("FATAL:", args.file, "not found!")
elif args.preset and not args.preset.lower() in ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"):
	print("FATAL:", args.preset, "not valid!")
elif args.quality and not args.quality in range(-12, 51):
	print("FATAL: quality must be between -12 and 51 (lower is slower/higher quality)")
else:
	valid_arguments = True
if not valid_arguments:
	sys.exit("Invalid command-line arguments.")
elif args.all and args.quality:
	print("Warning! Combining --all and --quality options is not recommended and may not produce optimal HEVC transcodes.")
	while "need response":
		reply = str(input("Proceed? (y/n) cccccccccc" )).lower().strip()
		if reply[0] == "y":
			break
		if reply[0] == "n":
			sys.exit("Aborting invocation with --all and --quality options.")

# Build list of source files
extensions = [".mp4", ".m4v", ".mov", ".mkv", ".mpg", ".mpeg", ".avi", ".wmv", ".flv", ".webm", ".ts"]
if args.all:
	source_files = ["source/" + file for file in os.listdir("source") if file[file.rindex("."):].lower() in extensions]
else:
	source_files = [args.file]

# Do the thing
if not os.path.exists("performance"):
	os.mkdir("performance")
if not os.path.exists("hevc"):
	os.mkdir("hevc")
for file in source_files:
	session = Session(file)
	if not os.path.exists(session.output_path):
		with open(session.log_path, "w") as log:
			sys.stdout.write(session.arguments)
			log.write(session.arguments)
			sys.stdout.write("")
			log.write("")
			start_time = datetime.now()
			with subprocess.Popen(shlex.split(session.arguments, posix=False), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1) as process:
				for line in process.stdout:
					sys.stdout.write(line)
					log.write(line)
			end_time = datetime.now()
			elapsed_time = end_time - start_time
			sys.stdout.write(str(elapsed_time))
			log.write(str(elapsed_time))
	else:
		print(session.output_path, "already exists, skipping.")
	if args.delete:
		session.cleanup()
	print()

sys.exit("{date}: Done.\n".format(date=str(datetime.now())))