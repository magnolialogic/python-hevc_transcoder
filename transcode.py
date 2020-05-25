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

def evaluate_args():
	"""	Exits with error messages if command-line arguments are invalid
	"""
	parser = argparse.ArgumentParser(description="Transcodes given file(s) to HEVC format.")
	install_group = parser.add_mutually_exclusive_group()
	install_group.add_argument("--install", action="store_true", help="install symlink to transcode.py on $PATH")
	install_group.add_argument("--uninstall", action="store_true", help="remove symlink to transcode.py")
	files_group = parser.add_mutually_exclusive_group()
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

	if args.install or args.uninstall:
		if len(sys.argv) > 2:
			print("\nFATAL: --install/--uninstall may not be called with any other arguments")
		else:
			if args.install:
				symlink(True)
			else:
				symlink(False)
	elif os.path.dirname(os.path.realpath(__file__)) == os.getcwd():
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

def get_user_response():
	"""	Accepts yes/no answer as user input and returns answer as boolean
	"""
	while "need response":
		reply = str(input(" Proceed? (y/n) ")).lower().strip()
		if len(reply) > 0:
			if reply[0] == "y":
				response = True
				break
			if reply[0] == "n":
				response = False
				break

	return response

def symlink(install):
	"""	Installs / uninstalls a symlink to transcode.py in /usr/local/bin or alternate $PATH location
	"""
	def link():
		print("\nCreate symlink for {script_name} on $PATH?".format(script_name=script_name))
		proceed = get_user_response()
		if proceed:
			if not oct(os.stat(script_realpath).st_mode)[-3:] == 755:
				try:
					os.chmod(script_realpath, 0o755)
				except PermissionError:
					sys.exit("\nError: failed to make {script_name} executable, operation not permitted.".format(script_name=script_name))
			print("Use default location? /usr/local/bin")
			default_location = get_user_response()
			if default_location:
				try:
					os.symlink(script_realpath, os.path.join(os.sep, "usr", "local", "bin", script_name))
				except PermissionError:
					sys.exit("\nError: failed to create symlink, operation not permitted.")
				else:
					sys.exit("Created symlink to {script_name} in /usr/local/bin\n")
			else:
				print("Use alternate $PATH location?")
				alternate_location = get_user_response()
				if alternate_location:
					alternate_path = str(input("Alternate $PATH location: (case-sensitive) "))
					if alternate_path[0] == "~": alternate_path = os.path.expanduser(alternate_path)
					if alternate_path in os.get_exec_path():
						try:
							os.symlink(script_realpath, os.path.join(alternate_path, script_name))
						except PermissionError:
							sys.exit("\nError: failed to create symlink, operation not permitted.")
						else:
							sys.exit("Created symlink to {script_name} in {alternate_path}\n".format(script_name=script_name, alternate_path=alternate_path))
					else:
						sys.exit("\nError: {alternate_path} not found on $PATH, aborting install.\n".format(alternate_path=alternate_path))
				else:
					sys.exit("Aborting install.\n")
		else:
			sys.exit("Aborting install.\n")

	def unlink():
		print("\nFound {script_name} on $PATH in {path_dir}\n".format(script_name=script_name, path_dir=path_dir))
		if os.path.islink(script_path_location):
			print("Remove symlink to {script_name} in {path_dir}?".format(script_name=script_name, path_dir=path_dir))
			proceed = get_user_response()
			if proceed:
				try:
					os.unlink(script_path_location)
				except PermissionError:
					sys.exit("\nError: operation not permitted.")
				else:
					print("Unlinked {script_path_location}\n".format(script_path_location=script_path_location))
			else:
				sys.exit("Aborting uninstall.\n")
		else:
			sys.exit("Error: {script_path_location} exists on $PATH but is not a symlink, skipping uninstall.\n".format(script_path_location=script_path_location))
		sys.exit()

	script_name=os.path.basename(sys.argv[0])
	script_realpath = os.path.realpath(__file__)
	script_on_path = False
	for location in os.get_exec_path():
		if script_name in os.listdir(location):
			script_on_path = True
			script_path_location = os.path.join(location, script_name)
			break

	if script_on_path:
		path_dir = os.path.dirname(script_path_location)
		script_executable = os.access(script_realpath, os.X_OK)

	if install:
		if script_on_path:
			sys.exit("\n{script_name} already on $PATH at {script_path_location}, skipping install.\n".format(script_name=script_name, script_path_location=script_path_location))
		else:
			link()
	else:
		if not script_on_path:
			sys.exit("\n{script_name} not on $PATH, skipping uninstall.\n".format(script_name=script_name))
		else:
			unlink()

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