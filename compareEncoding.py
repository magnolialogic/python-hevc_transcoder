#!/usr/bin/python3

import argparse
import cv2
import json
import numpy as np
import os
import shlex
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Source filename")
parser.add_argument("num_frames", nargs="?", default=5, type=int, help="Number of frames to generate")
parser.add_argument("-s", "--stack", action="store_true", help="Also create 2-up stacked comparison")
args = parser.parse_args()

if not set(["source", "hevc"]).issubset(set(os.listdir())):
	print("Invalid working directory, exiting.")
	sys.exit(1)

if args.filename.lower() == "all":
	source_files = [filename for filename in os.listdir("source") if os.path.splitext(filename)[1] == ".mp4"]
elif args.filename.endswith(".mp4"):
	source_files = [args.filename]
else:
	print("Invalid filename, exiting.")
	sys.exit(1)

print("\nComparison frames:\t{frames}".format(frames=args.num_frames))

for source_file in source_files:
	source_file_path = os.path.relpath("source/{filename}".format(filename=source_file))
	source_file_size = int(os.path.getsize(source_file_path) / 1000000)
	source_file_handle = cv2.VideoCapture(source_file_path)
	hevc_files = [filename for filename in os.listdir("hevc") if filename.startswith(os.path.splitext(source_file)[0])]

	for hevc_file in hevc_files:
		output_directory = os.path.join(os.path.relpath("comparison"), os.path.splitext(os.path.basename(hevc_file))[0])
		hevc_file_path = os.path.relpath("hevc/{filename}".format(filename=hevc_file))
		hevc_file_handle = cv2.VideoCapture(hevc_file_path)
		hevc_file_size = int(os.path.getsize(hevc_file_path) / 1000000)
		compression_ratio = int(100-(hevc_file_size/source_file_size*100))
		total_frames = source_file_handle.get(cv2.CAP_PROP_FRAME_COUNT)
		stride = int(total_frames / (args.num_frames + 1))

		print("\nFilename:\t\t{filename}".format(filename=hevc_file))
		if source_file_handle.get(cv2.CAP_PROP_FRAME_COUNT) != hevc_file_handle.get(cv2.CAP_PROP_FRAME_COUNT):
			print("\t\t\t!!! WARNING: Frame counts do not match, screencaps may be time-shifted")
		print("\tSource Size:\t{size} MB".format(size=source_file_size))
		print("\tHEVC Size:\t{size} MB".format(size=hevc_file_size))
		print("\tReduction:\t{ratio}%\n".format(ratio=compression_ratio))

		if not os.path.exists(output_directory): os.makedirs(output_directory)
		with open(os.path.join(output_directory, "summary.txt"), "w") as summary_file:
			summary_file.write("{source} MB to {hevc} MB, saving {ratio}%".format(source=str(source_file_size), hevc=str(hevc_file_size), ratio=str(compression_ratio)))
		for frame in range(1, args.num_frames+1):
			source_file_handle.set(cv2.CAP_PROP_POS_FRAMES,stride*frame)
			hevc_file_handle.set(cv2.CAP_PROP_POS_FRAMES,stride*frame)
			ret,source_frame = source_file_handle.read()
			ret,hevc_frame = hevc_file_handle.read()
			if args.stack:
				comparison_frame = np.vstack((source_frame,hevc_frame))
				cv2.imwrite(os.path.join(output_directory, "{number}-2up.png".format(number=frame)), comparison_frame)
			cv2.imwrite(os.path.join(output_directory, "{number}-original.png".format(number=frame)), source_frame)
			cv2.imwrite(os.path.join(output_directory, "{number}-x265.png".format(number=frame)), hevc_frame)

		hevc_file_handle.release()

	source_file_handle.release()

sys.exit(0)