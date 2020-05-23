#!/usr/local/bin/python3

import argparse
from datetime import datetime
import os
import sys

# Verify script is colocated with ./src/ and import TranscodeSession.py
if not os.path.isdir(os.path.join(sys.path[0], "src")):
	sys.exit("FATAL: ./src/ not present in parent diectory.\n")
sys.path.append(os.path.join(sys.path[0], "src"))
try:
	from TranscodeSession import Session
except ImportError:
	sys.exit("FATAL: failed to import TranscodeSession from src/TranscodeSession.py\n")

"""

TODO:
- allow comma-separated string for --preset, e.g. medium,slow,slower, map to list
- add check: if working directory == script location, exit with warning to symlink transcode.py onto $PATH, else if different directory but no symlink, prompt to run --install
- add --install arg (with optional path to custom $PATH location) to create symlink at /usr/local/bin or custom $PATH location?
- once profiling is complete, only append file decorator if --test is specified

"""

def build_source_list(args):
	"""	Constructs and returns list of source files
	"""
	extensions = [".mp4", ".m4v", ".mov", ".mkv", ".mpg", ".mpeg", ".avi", ".wmv", ".flv", ".webm", ".ts"]
	print("\nBuilding source list...")
	if args.all:
		source_files = ["source/" + file for file in os.listdir("source") if os.path.splitext(file)[1].lower() in extensions]
	else:
		if os.path.splitext(args.file)[1].lower() in extensions:
			source_files = [args.file]
		else:
			sys.exit("FATAL: " + args.file + " has invalid file extension!\n")

	for source_file in source_files:
		session = Session(source_file, args)
		if os.path.exists(session.path["output"]):
			print(" Skipping", source_file)
			source_files = [file for file in source_files if file is not source_file]

	if len(source_files) == 0:
		sys.exit("All supported files in ./source/ have already been transcoded. Exiting.\n")
	else:
		print(str(source_files) + "\n")

	return source_files

def validate_args(args):
	"""	Exits with error messages if command-line arguments are invalid
	"""
	valid_arguments = False
	if not "source" in os.listdir():
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
		sys.exit("Invalid command-line arguments.\n")
	elif args.all and args.quality:
		print("Warning! Combining --all and --quality options is not recommended and may not produce optimal HEVC transcodes.")
		while "need response":
			reply = str(input("Proceed? (y/n)" )).lower().strip()
			if reply[0] == "y":
				break
			if reply[0] == "n":
				sys.exit("Aborting invocation with --all and --quality options.\n")

	if not os.path.isdir("performance"):
		try:
			os.mkdir("performance")
		except FileExistsError:
			sys.exit("FATAL: can't create directory \"performance\" because file with same name exists")
	if not os.path.isdir("hevc"):
		try:
			os.mkdir("hevc")
		except FileExistsError:
			sys.exit("FATAL: can't create directory \"hevc\" because file with same name exists")

def main():
	# Define command-line arguments
	parser = argparse.ArgumentParser()
	files_group = parser.add_mutually_exclusive_group(required=True)
	files_group.add_argument("-f", "--file", help="relative path to movie in source directory")
	files_group.add_argument("--all", action="store_true", help="transcode all supported movies in source directory")
	parser.add_argument("-q", "--quality", type=int, help="HandBrake quality slider value (-12,51)")
	parser.add_argument("--preset", help="override video encoder preset")
	preset_group = parser.add_mutually_exclusive_group(required=False)
	preset_group.add_argument("--baseline", action="store_true", help="use baseline encoder options")
	preset_group.add_argument("--best", action="store_true", help="use highest quality encoder options")
	parser.add_argument("--small", action="store_true", help="use additional encoder options to minimize filesize at the expense of speed")
	parser.add_argument("--delete", action="store_true", help="delete output files when complete/interrupted")
	args = parser.parse_args()
	validate_args(args)

	# Do the thing
	source_files = build_source_list(args)
	time_script_started = datetime.now()
	for file in source_files:
		session = Session(file, args)
		session.start()
		session.job.wait()
		session.finish()

	time_script_finished = datetime.now()
	time_script_duration = time_script_finished - time_script_started

	sys.exit("{date}: Finished after {duration}.\n".format(date=str(datetime.now()), duration=time_script_duration))

# Check for Python 3.8 (required for shlex usage)
if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 8):
	sys.exit("FATAL: Requires Python3.8 or newer.\n")
elif __name__ == "__main__":
	main()