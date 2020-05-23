#!/usr/local/bin/python3

import argparse
from datetime import datetime
import os
import sys
sys.path.append(os.path.join(sys.path[0], "src"))
from TranscodeSession import Session

"""

TODO:
- allow comma-separated string for --preset, e.g. medium,slow,slower, map to list
- ~~if presets.json does not exist, download from github~~
- need to format source / output filenames: drop resolution suffixes
- add check: if working directory == script location, exit with warning to symlink transcode.py onto $PATH
- add --install arg to create symlink at /usr/local/bin?

"""

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
	valid_arguments = False

	# Validate command-line arguments
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

	# Build list of source files and create directories if necessary
	extensions = [".mp4", ".m4v", ".mov", ".mkv", ".mpg", ".mpeg", ".avi", ".wmv", ".flv", ".webm", ".ts"]
	print("\nBuilding source list...")
	if args.all:
		source_files = ["source/" + file for file in os.listdir("source") if os.path.splitext(file)[1].lower() in extensions]
	else:
		source_files = [args.file]
	for source_file in source_files:
		session = Session(source_file, args)
		if os.path.exists(session.path["output"]):
			print(" Skipping", source_file)
			source_files = [file for file in source_files if file is not source_file]
	if len(source_files) == 0:
		sys.exit("All source files have already been transcoded. Exiting.\n")
	else:
		print(str(source_files) + "\n")
	if not os.path.exists("performance"):
		os.mkdir("performance")
	if not os.path.exists("hevc"):
		os.mkdir("hevc")

	# Do the thing
	task_start_time = datetime.now()
	for file in source_files:
		session = Session(file, args)
		session.summarize()
		print(session.command + "\n")
		job_start_time = datetime.now()
		session.start()
		session.job.wait()
		job_end_time = datetime.now()
		job_elapsed_time = job_end_time - job_start_time
		fps = session.source["frames"] / job_elapsed_time.seconds
		source_file_size = session.source["filesize"] / 1000000
		output_file_size = os.path.getsize(session.path["output"]) / 1000000
		compression_ratio = int(100 - (output_file_size / source_file_size * 100))
		print("\n{date}: Finished {output_file}".format(date=str(job_end_time), output_file=session.path["output"]))
		session.log(job_elapsed_time, fps, compression_ratio)
		print("\n\n\n\n\n")
		if args.delete:
			session.cleanup()

	task_end_time = datetime.now()
	task_elapsed_time = task_end_time - task_start_time

	sys.exit("{date}: Finished after {task_elapsed_time}.\n".format(date=str(datetime.now()), task_elapsed_time=task_elapsed_time))

# Check for Python 3.8 (required for shlex usage)
if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 8):
	sys.exit("FATAL: Requires Python3.8 or newer.\n")
elif __name__ == "__main__":
	main()