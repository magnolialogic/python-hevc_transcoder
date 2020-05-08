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
		class RF:
			SD = 21
			HD = 22
			FHD = 23
			UHD = 26
		
		class ENCOPTS:
			SD = "ctu=32:qg-size=16"
			HD = "ctu=32:qg-size=32"
			FHD = "ctu=64:qg-size=64"
			ENCOPTS = "ctu=64:qg-size=64"
	
	def __init__(self, file):
		signal.signal(signal.SIGINT, self.signal_handler)
		
		# Get source file metadata
		cmd = "ffprobe -v quiet -print_format json -show_streams " + file
		metadata = subprocess.check_output(shlex.split(cmd)).decode("utf-8")
		metadata = json.loads(metadata)["streams"][0]
		
		# Populate metadata-based attributes
		self.paths = {"source": file}
		self.source = {"height": int(metadata["height"]), "width": int(metadata["width"]), "duration": float(metadata["duration"]), "filename": os.path.splitext(os.path.relpath(self.paths["source"], "source"))[0], "filesize": os.path.getsize(self.paths["source"]), "bitrate": int(metadata["bit_rate"]), "frames": int(metadata["nb_frames"]), "codec": metadata["codec_name"]}
		height = self.source["height"]
		if height < 720:
			resolution = "SD"
		elif 720 <= height < 1080:
			resolution = "HD"
		elif 1080 <= height < 2160:
			resolution = "FHD"
		elif 2160 <= height:
			resolution = "UHD"
		self.source["resolution"] = resolution
		
		# Create empty attributes for dynamic session options
		self.encoder_quality = None
		self.encoder_preset = None
		self.preset_name = None
		self.encoder_options = None
		
		# Construct session options and parameters
		self.map_options()
		self.file_decorator = "_RF" + str(self.encoder_quality)
		if args.best:
			self.file_decorator += "_Best"
		elif args.baseline:
			self.file_decorator += "_Baseline"
		if args.small:
			self.file_decorator += "_Small"
		if args.preset:
			self.file_decorator += "_{preset}".format(preset=args.preset.capitalize())
		self.paths["output"] = "hevc/" + self.source["filename"] + self.file_decorator + ".mp4"
		self.paths["log"] = "performance/" + self.source["filename"] + self.file_decorator + ".log"
		
		# Build HandBrakeCLI command
		self.args = "HandBrakeCLI --encoder-preset {encoder_preset} --preset-import-file presets.json --preset {preset_name} --quality {quality} --encopts {encopts} --input {source_path} --output {output_path}".format(encoder_preset=self.encoder_preset, preset_name=self.preset_name, quality=str(self.encoder_quality), encopts=self.encoder_options, source_path=self.paths["source"], output_path=self.paths["output"])
		
		# Validate and finish
		self.validate()
		self.summarize()
	
	def validate(self):
		"""	Verifies that no session attributes are null
		"""
		if any(value is None for attribute, value in self.__dict__.items()):
			sys.exit("FATAL: Session.validate(): found null attribute for " + self.paths["source"])
	
	def summarize(self):
		"""	Summarize transcode session before starting
		"""
		print("{date}: {source}:".format(date=str(datetime.now()), source=self.paths["source"]))
		pprint(vars(self))
		print()
	
	def map_options(self):
		"""	Start with settings based on source resolution and then override defaults based on command-line arguments
		"""
		self.encoder_quality = getattr(self.Settings.RF, self.source["resolution"])
		self.encoder_options = getattr(self.Settings.ENCOPTS, self.source["resolution"])
		if args.best:
			self.preset_name = "Best"
		elif args.baseline:
			self.preset_name = "Baseline"
		else:
			self.preset_name = "Default"
		if args.preset:
			self.encoder_preset = args.preset.lower()
		else:
			self.encoder_preset = "slow"
		if args.quality:
			self.encoder_quality = args.quality
		if args.small:
			self.encoder_options += ":tu-intra-depth=3:tu-inter-depth=3"
	
	def signal_handler(self, sig, frame):
		"""	Delete output file if ctrl+c is caught, since file will be corrupt
		"""
		self.cleanup()
	
	def log(self, elapsed_time, fps):
		"""	Summarizes transcode session for screen and log
		"""
		with open(self.paths["log"], "w") as logfile:
			summary = str(elapsed_time) + "\n" + str(fps) + " fps"
			logfile.write(summary + "\n\n" + session.args + "\n\n")
			pprint(vars(self), logfile)
			print(summary)
	
	def cleanup(self):
		"""	Always deletes output file, deletes log if --delete is passed from command-line
		"""
		if os.path.exists(self.paths["output"]):
				os.remove(self.paths["output"])
		if args.delete:
			if os.path.exists(self.paths["log"]):
				os.remove(self.paths["log"])

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
	print("FATAL: quality must be between -12 and 51 (lower is slower + higher quality)")
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

# Build list of source files and create directories if necessary
extensions = [".mp4", ".m4v", ".mov", ".mkv", ".mpg", ".mpeg", ".avi", ".wmv", ".flv", ".webm", ".ts"]
if args.all:
	source_files = ["source/" + file for file in os.listdir("source") if os.path.splitext(file)[1].lower() in extensions]
else:
	source_files = [args.file]
if not os.path.exists("performance"):
	os.mkdir("performance")
if not os.path.exists("hevc"):
	os.mkdir("hevc")

# Do the thing
start_time = datetime.now()
print("\n{date}: Starting transcode session for {source_files}\n".format(date=str(datetime.now()), source_files=str(source_files)))
for file in source_files:
	session = Session(file)
	if not os.path.exists(session.paths["output"]):
		print(session.args + "\n")
		session_start_time = datetime.now()
		transcode = subprocess.Popen(shlex.split(session.args, posix=False))
		transcode.wait()
		session_end_time = datetime.now()
		session_elapsed_time = session_end_time - session_start_time
		fps = session.source["frames"] / session_elapsed_time.seconds
		print("\n{date}: Finished {output_file}".format(date=str(session_end_time), output_file=session.paths["output"]))
		session.log(session_elapsed_time, fps)
	else:
		print(session.paths["output"], "already exists, skipping.")
	if args.delete:
		session.cleanup()
	print("\n\n\n\n\n")

end_time = datetime.now()
elapsed_time = end_time - start_time

sys.exit("{date}: Finished after {elapsed_time}.\n".format(date=str(datetime.now()), elapsed_time=elapsed_time))