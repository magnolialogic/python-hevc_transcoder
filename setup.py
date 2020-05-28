#!/usr/local/bin/python3

import argparse
import os
import sys

# Verify script is colocated with ./lib/ and import dependencies
if not os.path.isdir(os.path.join(sys.path[0], "lib")):
	sys.exit("FATAL: ./lib/ not present in parent diectory.\n")
sys.path.append(os.path.join(sys.path[0], "lib"))
try:
	from common import get_yn_answer
except ImportError:
	sys.exit("FATAL: failed to import dependencies from ./lib/\n")

def main():
	def link():
		"""	Creates symlink to transcode.py in /usr/local/bin or alternate $PATH
		"""
		print("\nCreate symlink for {script_name} on $PATH?".format(script_name=script_name))
		proceed = get_yn_answer()
		if proceed:
			if not oct(os.stat(script_realpath).st_mode)[-3:] == 755:
				try:
					os.chmod(script_realpath, 0o755)
				except PermissionError:
					sys.exit("\nError: failed to make {script_name} executable, operation not permitted.".format(script_name=script_name))
			print("Use default location? /usr/local/bin")
			default_location = get_yn_answer()
			if default_location:
				try:
					os.symlink(script_realpath, os.path.join(os.sep, "usr", "local", "bin", script_name))
				except PermissionError:
					sys.exit("\nError: failed to create symlink, operation not permitted.")
				else:
					sys.exit("Created symlink to {script_name} in /usr/local/bin\n")
			else:
				print("Use alternate $PATH location?")
				alternate_location = get_yn_answer()
				if alternate_location:
					alternate_path = str(input("Alternate $PATH location: (case-sensitive) "))
					if alternate_path[0] == "~": alternate_path = os.path.expanduser(alternate_path)
					if alternate_path in os.get_exec_path():
						try:
							os.symlink(script_realpath, os.path.join(alternate_path, script_name))
						except PermissionError:
							sys.exit("\nError: failed to create symlink, operation not permitted.")
						else:
							sys.exit("\nCreated symlink to {script_name} in {alternate_path}\n".format(script_name=script_name, alternate_path=alternate_path))
					else:
						sys.exit("\nError: {alternate_path} not found on $PATH, aborting install.\n".format(alternate_path=alternate_path))
				else:
					sys.exit("Aborting install.\n")
		else:
			sys.exit("Aborting install.\n")

	def unlink():
		"""	Removes symlink to transcode.py from $PATH
		"""
		print("\nFound {script_name} on $PATH in {path_dir}\n".format(script_name=script_name, path_dir=path_dir))
		if os.path.islink(script_path_location):
			print("Remove symlink to {script_name} in {path_dir}?".format(script_name=script_name, path_dir=path_dir))
			proceed = get_yn_answer()
			if proceed:
				try:
					os.unlink(script_path_location)
				except PermissionError:
					sys.exit("\nError: operation not permitted.")
				else:
					print("\nUnlinked {script_path_location}\n".format(script_path_location=script_path_location))
			else:
				sys.exit("Aborting uninstall.\n")
		else:
			sys.exit("Error: {script_path_location} exists on $PATH but is not a symlink, skipping uninstall.\n".format(script_path_location=script_path_location))
		sys.exit()

	parser = argparse.ArgumentParser(description="Manages $PATH symlink for transcode.py".format(sep=os.sep))
	install_group = parser.add_mutually_exclusive_group(required=True)
	install_group.add_argument("--install", action="store_true", help="install symlink to transcode.py on $PATH")
	install_group.add_argument("--uninstall", action="store_true", help="remove symlink to transcode.py")
	args = parser.parse_args()

	script_name = "transcode.py"
	script_realpath = os.path.realpath(script_name)
	script_on_path = False
	for location in os.get_exec_path():
		if script_name in os.listdir(location):
			script_on_path = True
			script_path_location = os.path.join(location, script_name)
			break

	if script_on_path:
		path_dir = os.path.dirname(script_path_location)
		script_executable = os.access(script_realpath, os.X_OK)

	if args.install:
		if script_on_path:
			sys.exit("\n{script_name} already on $PATH at {script_path_location}, skipping install.\n".format(script_name=script_name, script_path_location=script_path_location))
		else:
			link()
	else:
		if not script_on_path:
			sys.exit("\n{script_name} not on $PATH, skipping uninstall.\n".format(script_name=script_name))
		else:
			unlink()

	if len(sys.argv) > 2:
		print("\nFATAL: --install/--uninstall may not be called with any other arguments")
	else:
		if args.install:
			symlink(True)
		else:
			symlink(False)

if __name__ == "__main__":
	main()