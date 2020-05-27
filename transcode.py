#!/usr/local/bin/python3

import argparse
from datetime import datetime
import os
import sys

# Verify script is colocated with ./lib/ and import dependencies
if not os.path.isdir(os.path.join(sys.path[0], "lib")):
	sys.exit("FATAL: ./lib/ not present in parent diectory.\n")
sys.path.append(os.path.join(sys.path[0], "lib"))
try:
	from TranscodeSession import Session
	from common import get_user_response
except ImportError:
	sys.exit("FATAL: failed to import dependencies from ./lib/\n")

def evaluate_args():
	"""	Exits with error messages if command-line arguments are invalid
	"""
	parser = argparse.ArgumentParser(description="Transcodes given file(s) in .{sep}source{sep} to HEVC format.".format(sep=os.sep))
	files_group = parser.add_mutually_exclusive_group(required=True)
	files_group.add_argument("--file", help="relative path to movie in source directory")
	files_group.add_argument("--all", action="store_true", help="transcode all supported movies in source directory")
	parser.add_argument("--quality", type=int, help="HandBrake quality slider value (-12,51)")
	parser.add_argument("--preset", help="override video encoder preset")
	preset_group = parser.add_mutually_exclusive_group()
	preset_group.add_argument("--baseline", action="store_true", help="use baseline encoder options")
	preset_group.add_argument("--best", action="store_true", help="use highest quality encoder options")
	parser.add_argument("--small", action="store_true", help="use additional encoder options to minimize filesize at the expense of speed")
	parser.add_argument("--delete", action="store_true", help="delete output files when complete/interrupted")
	args = parser.parse_args()

	valid_arguments = False

	if os.path.dirname(os.path.realpath(__file__)) == os.getcwd():
		print("\nFATAL: invalid working directory: running from master directory. Please create working directory in another location.")
	elif not "source" in os.listdir():
		print("\nFATAL: invalid working directory: ./source/ does not exist")
	elif args.file and not os.path.exists(args.file):
		print("\nFATAL:", args.file, "not found!")
	elif args.preset and not args.preset.lower() in ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"):
		print("\nFATAL:", args.preset, "not valid!")
	elif args.quality and not args.quality in range(-12, 51):
		print("\nATAL: quality must be between -12 and 51 (lower is slower + higher quality)")
	else:
		valid_arguments = True

	if not valid_arguments:
		sys.exit("Invalid command-line arguments.\n")
	elif args.all and args.quality:
		print("\nWarning! Combining --all and --quality options is not recommended and may not produce optimal HEVC transcodes.")
		proceed = get_user_response()
		if not proceed:
			sys.exit("Aborting invocation with --all and --quality options.\n")

	for directory in ["performance", "hevc"]:
		if not os.path.isdir(directory):
			os.mkdir(directory)

	return args

def build_source_list(args):
	"""	Constructs and returns list of source files
	"""
	extensions = [".mp4", ".m4v", ".mov", ".mkv", ".mpg", ".mpeg", ".avi", ".wmv", ".flv", ".webm", ".ts"]

	print("\nBuilding source list...")

	if args.all:
		source_files = [os.path.join("source", file) for file in os.listdir("source") if os.path.splitext(file)[1].lower() in extensions]
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
		if args.all:
			sys.exit("All supported files in ./source/ have already been transcoded. Exiting.\n")
		else:
			sys.exit("File exists. Exiting.")
	else:
		print(str(source_files) + "\n")

	return source_files

def main():
	args = evaluate_args()
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

if __name__ == "__main__":
	main()