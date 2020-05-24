from datetime import datetime
import json
import os
from pprint import pprint
import shlex
import signal
import subprocess
import sys

class Session():

	#	Default encoder settings

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

	#	Object lifecycle methods

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

		self.output["filename"] = self.source["filename"] + self.output["file_decorator"]
		self.path["output"] = "hevc/" + self.output["filename"] + ".mp4"
		self.path["log"] = "performance/" + self.output["filename"] + ".log"

		# Verify no attributes are None
		self.validate()

		# Build HandBrakeCLI command
		self.command = "HandBrakeCLI --encoder-preset {encoder_preset} --preset-import-file {json_path} --preset {preset_name} --quality {quality} --encopts {encopts} --input {source_path} --output {output_path}".format(encoder_preset=self.encoder_preset, json_path=os.path.join(sys.path[0], "src/presets.json"), preset_name=self.preset_name, quality=str(self.encoder_quality), encopts=self.encoder_options, source_path=self.path["source"], output_path=self.path["output"])

	def signal_handler(self, sig, frame):
		"""	Delete output file if ctrl+c is caught, since file will be corrupt
		"""
		if hasattr(self, "job"):
			self.job.terminate()
			self.cleanup()

		sys.exit("\n\n{date}: Caught ctrl+c, aborting.\n\n".format(date=datetime.now()))

	#	Object task methods

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

		self.output = {"file_decorator": "_RF" + str(self.encoder_quality)}
		self.output["file_decorator"] += "_{preset}".format(preset=self.encoder_preset.capitalize())
		if self.args.baseline:
			self.output["file_decorator"] += "_Baseline"
		elif self.args.best:
			self.output["file_decorator"] += "_Best"

		if self.args.small:
			self.output["file_decorator"] += "_Small"

	def validate(self):
		"""	Verifies that no session attributes are null
		"""
		if any(value is None for attribute, value in self.__dict__.items()):
			sys.exit("FATAL: Session.validate(): found null attribute for " + self.path["source"])

	def start(self):
		"""	Starts HandBrakeCLI session and creates job attribute
		"""
		print("{date}: Starting transcode session for {source}:".format(date=str(datetime.now()), source=self.path["source"]))
		pprint(vars(self), indent=4)
		print("\n{command}\n".format(command=self.command))
		self.time = {"started": datetime.now()}
		self.job = subprocess.Popen(shlex.split(self.command, posix=False)) # Posix=False to escape double-quotes in arguments

	def finish(self):
		"""	Compute attributes needed to generate summary and performance log
		"""
		self.time["finished"] = datetime.now()
		print("\n{date}: Finished {output_file}".format(date=str(self.time["finished"]), output_file=self.path["output"]))
		self.time["duration"] = self.time["finished"] - self.time["started"]
		self.output["filesize"] = os.path.getsize(self.path["output"])
		self.output["compression_ratio"] = int(100 - (self.output["filesize"] / self.source["filesize"] * 100))
		self.fps = self.source["frames"] / self.time["duration"].seconds
		self.log(self.time["duration"], self.fps, self.output["compression_ratio"])
		print("\n\n\n\n\n")
		if self.args.delete:
			self.cleanup()

	def log(self, elapsed_time, fps, compression_ratio):
		"""	Summarizes transcode session for screen and log
		"""
		summary = "{duration}\n{fps:.2f} fps\n{compression_ratio}% reduction ({source_size}mb to {output_size}mb)".format(duration=self.time["duration"], fps=self.fps, compression_ratio=self.output["compression_ratio"], source_size=int(self.source["filesize"] / 1000000), output_size=int(self.output["filesize"] / 1000000))
		with open(self.path["log"], "w") as logfile:
			logfile.write(summary + "\n\n" + self.command + "\n\n")
			pprint(vars(self), logfile)

		print(summary)

	def cleanup(self):
		"""	Always deletes output file, deletes log if --delete is passed from command-line
		"""
		if os.path.exists(self.path["output"]):
			try:
				os.remove(self.path["output"])
			except FileNotFoundError:
				print("Session.cleanup():", self.path["output"], "does not exist.")

		if self.args.delete:
			if os.path.exists(self.path["log"]):
				try:
					os.remove(self.path["log"])
				except FileNotFoundError:
					print("Session.cleanup():", self.path["log"], "does not exist.")

# Check for Python 3.8 (required for shlex usage)
if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 8):
	sys.exit("\nFATAL: Requires Python3.8 or newer.\n")
elif __name__ == "__main__":
	sys.exit("I am a module, not a script.")