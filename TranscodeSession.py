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
			UHD = "ctu=64:qg-size=64"

	def __init__(self, file, args):
		signal.signal(signal.SIGINT, self.signal_handler)

		self.args = args

		# Get source file metadata
		cmd = "ffprobe -v quiet -print_format json -show_streams " + file
		metadata = subprocess.check_output(shlex.split(cmd)).decode("utf-8")
		metadata = json.loads(metadata)["streams"][0]

		# Populate metadata-based attributes
		self.path = {"source": file}
		self.source = {"height": int(metadata["height"]), "width": int(metadata["width"]), "duration": float(metadata["duration"]), "filename": os.path.splitext(os.path.relpath(self.path["source"], "source"))[0], "filesize": os.path.getsize(self.path["source"]), "bitrate": int(metadata["bit_rate"]), "frames": int(metadata["nb_frames"]), "codec": metadata["codec_name"]}
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
		self.file_decorator += "_{preset}".format(preset=self.encoder_preset.capitalize())
		if self.args.baseline:
			self.file_decorator += "_Baseline"
		elif self.args.best:
			self.file_decorator += "_Best"
		if self.args.small:
			self.file_decorator += "_Small"
		self.path["output"] = "hevc/" + self.source["filename"] + self.file_decorator + ".mp4"
		self.path["log"] = "performance/" + self.source["filename"] + self.file_decorator + ".log"

		# Verify no attributes are None
		self.validate()

		# Build HandBrakeCLI command
		self.command = "HandBrakeCLI --encoder-preset {encoder_preset} --preset-import-file presets.json --preset {preset_name} --quality {quality} --encopts {encopts} --input {source_path} --output {output_path}".format(encoder_preset=self.encoder_preset, preset_name=self.preset_name, quality=str(self.encoder_quality), encopts=self.encoder_options, source_path=self.path["source"], output_path=self.path["output"])

	def signal_handler(self, sig, frame):
		"""	Delete output file if ctrl+c is caught, since file will be corrupt
		"""
		if hasattr(self, "job"):
			self.job.terminate()
			self.cleanup()
		sys.exit("\n\n{date}: Caught ctrl+c, aborting.\n\n".format(date=datetime.now()))

	def cleanup(self):
		"""	Always deletes output file, deletes log if --delete is passed from command-line
		"""
		if os.path.exists(self.path["output"]):
			os.remove(self.path["output"])
		if self.args.delete:
			if os.path.exists(self.path["log"]):
				os.remove(self.path["log"])

	def log(self, elapsed_time, fps, compression_ratio):
		"""	Summarizes transcode session for screen and log
		"""
		with open(self.path["log"], "w") as logfile:
			summary = "{elapsed_time}\n{fps} fps\n{compression_ratio}% reduction".format(elapsed_time=elapsed_time, fps=fps, compression_ratio=compression_ratio)
			logfile.write(summary + "\n\n" + session.args + "\n\n")
			pprint(vars(self), logfile)
			print(summary)

	def map_options(self):
		"""	Start with settings based on source resolution and then override defaults based on command-line arguments
		"""
		self.encoder_quality = getattr(self.Settings.RF, self.source["resolution"])
		self.encoder_options = getattr(self.Settings.ENCOPTS, self.source["resolution"])
		if self.args.best:
			self.preset_name = "Best"
		elif self.args.baseline:
			self.preset_name = "Baseline"
		else:
			self.preset_name = "Default"
		if self.args.preset:
			self.encoder_preset = self.args.preset.lower()
		else:
			self.encoder_preset = "slow"
		if self.args.quality:
			self.encoder_quality = self.args.quality
		if self.args.small:
			self.encoder_options += ":tu-intra-depth=3:tu-inter-depth=3"

	def start(self):
		"""	Starts HandBrakeCLI session and creates job attribute
		"""
		self.job = subprocess.Popen(shlex.split(self.command, posix=False)) # Posix=False to escape double-quotes in arguments

	def summarize(self):
		"""	Summarize transcode session before starting
		"""
		print("{date}: Starting transcode session for {source}:".format(date=str(datetime.now()), source=self.path["source"]))
		pprint(vars(self))
		print()

	def validate(self):
		"""	Verifies that no session attributes are null
		"""
		if any(value is None for attribute, value in self.__dict__.items()):
			sys.exit("FATAL: Session.validate(): found null attribute for " + self.path["source"])