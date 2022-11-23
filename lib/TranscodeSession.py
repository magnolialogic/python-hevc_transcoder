from datetime import datetime
import dill
import json
import os
from pprint import pprint
import shlex
import signal
import subprocess
import sys

class Session():

	#	Object lifecycle methods

	def __init__(self, file, args):
		signal.signal(signal.SIGINT, self.signal_handler)
		self.args = args

		# Get source file metadata
		cmd = "ffprobe -v quiet -print_format json -show_streams " + file
		metadata = subprocess.check_output(shlex.split(cmd)).decode("utf-8")
		metadata = json.loads(metadata)["streams"]
		metadata = next(stream for stream in metadata if stream["codec_name"] == "h264")

		# Populate metadata-based attributes
		self.path = {"source": os.path.relpath(file)}
		self.source = {
				"height": int(metadata["height"]),
				"width": int(metadata["width"]),
				"duration": float(metadata["duration"]),
				"filename": os.path.splitext(os.path.relpath(self.path["source"], "source"))[0],
				"filesize": os.path.getsize(self.path["source"]),
				"bitrate": int(metadata["bit_rate"]),
				"frames": int(metadata["nb_frames"]),
				"codec": metadata["codec_name"]
			}
		if self.source["height"] < 720:
			self.encoder_quality = 18
			#self.encoder_quality = 21
			self.encoder_options = "ctu=32:qg-size=16"
		elif 720 <= self.source["height"] < 1080:
			self.encoder_quality = 20
			#self.encoder_quality = 22
			self.encoder_options = "ctu=32:qg-size=32"
		elif 1080 <= self.source["height"] < 2160:
			self.encoder_quality = 21
			#self.encoder_quality = 23
			self.encoder_options = "ctu=64:qg-size=64"
		elif 2160 <= self.source["height"]:
			self.encoder_quality = 24
			#self.encoder_quality = 26
			self.encoder_options = "ctu=64:qg-size=64"

		# Create empty attributes for dynamic session options
		self.preset_name = None

		# Construct session options and parameters based on command-line arguments
		self.options_for_args()

		# Construct output parameters
		self.output["filename"] = self.source["filename"] + self.output["file_decorator"]
		self.path["output"] = os.path.join("hevc", self.output["filename"] + ".mp4")
		self.path["log"] = os.path.join("performance", self.output["filename"] + ".log")
		self.path["session"] = os.path.join("performance", self.output["filename"] + ".session")

		# Verify no attributes are None
		self.validate()

		# Build HandBrakeCLI command
		self.command = "HandBrakeCLI --encoder-preset {encoder_preset} --preset-import-file {json_path} --preset {preset_name} --quality {quality} --encopts {encopts} --input {source_path} --output {output_path}".format(encoder_preset=self.encoder_preset, json_path=os.path.join(sys.path[0], "lib", "presets.json"), preset_name=self.preset_name, quality=str(self.encoder_quality), encopts=self.encoder_options, source_path=self.path["source"], output_path=self.path["output"])

	def signal_handler(self, sig, frame):
		"""	Delete output file if ctrl+c is caught, since file will be corrupt
		"""
		if hasattr(self, "job"):
			self.job.terminate()
			self.cleanup()

		sys.exit("\n\n{date}: Caught ctrl+c, aborting.\n\n".format(date=datetime.now()))

	#	Object task methods

	def options_for_args(self):
		"""	Override defaults based on command-line arguments
		"""
		if self.args.quality:
			self.encoder_quality = self.args.quality

		if self.args.preset:
			self.encoder_preset = self.args.preset.lower()
		else:
			self.encoder_preset = "medium"

		self.output = {"file_decorator": "_RF" + str(self.encoder_quality)}
		self.output["file_decorator"] += "_{preset}".format(preset=self.encoder_preset.capitalize())

		if self.args.best:
			self.preset_name = "Best"
			self.output["file_decorator"] += "_Best"
		elif self.args.baseline:
			self.preset_name = "Baseline"
			self.output["file_decorator"] += "_Baseline"
		else:
			self.preset_name = "Default"

		if self.args.small:
			self.encoder_options += ":tu-intra-depth=3:tu-inter-depth=3"
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
		with open(self.path["session"], "wb") as session_file:
			dill.dump(self, session_file)
		print("\n\n\n\n\n")
		if self.args.delete:
			self.cleanup()

	def log(self, elapsed_time, fps, compression_ratio):
		"""	Summarizes transcode session for screen and log
		"""
		summary = "{duration}\n{fps:.2f} fps\n{compression_ratio}% reduction ({source_size}mb to {output_size}mb)".format(duration=self.time["duration"], fps=self.fps, compression_ratio=self.output["compression_ratio"], source_size=int(self.source["filesize"] / 1000000), output_size=int(self.output["filesize"] / 1000000))
		with open(self.path["log"], "w") as log_file:
			log_file.write(summary + "\n\n" + self.command + "\n\n")
			pprint(vars(self), log_file)

		print(summary)

	def cleanup(self):
		"""	Deletes output file if it exists
		"""
		if os.path.exists(self.path["output"]):
			try:
				os.remove(self.path["output"])
			except FileNotFoundError:
				print("Session.cleanup():", self.path["output"], "does not exist.")

	def repair(self):
		with open(os.path.join("performance", self.output["filename"] + ".log"), "r") as log_file:
			self.output["filesize"] = os.path.getsize(self.path["output"])
			self.time = {"duration": log_file.readline().rstrip()}
			self.fps = "{:0.2f}".format(float(log_file.readline().rstrip().split(" ")[0]))
			self.output["compression_ratio"] = log_file.readline().rstrip().split(" ")[0][:-1]
			if self.output["compression_ratio"] == "":
				self.output["filesize"] = os.path.getsize(self.path["output"])
				self.output["compression_ratio"] = int(100 - (self.output["filesize"] / self.source["filesize"] * 100))
		with open(self.path["session"], "wb") as session_file:
			dill.dump(self, session_file)
		print("Wrote " + self.path["session"])

# Check for Python 3.8 (required for shlex usage)
if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 8):
	sys.exit("\nFATAL: Requires Python3.8 or newer.\n")
elif __name__ == "__main__":
	sys.exit("I am a module, not a script.")