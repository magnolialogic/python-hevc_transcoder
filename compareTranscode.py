#!/usr/local/bin/python3

import argparse
import cv2
import dill
import imutils
import numpy as np
import os
from skimage.metrics import structural_similarity
import subprocess
import sys

# Verify script is colocated with ./lib/ and import dependencies
sys.path.append(os.path.join(sys.path[0], "lib"))
try:
	from common import get_choice_from_menu
except ImportError:
	sys.exit("FATAL: failed to import dependencies from ./lib/\n")

# Parse command-line arguments
parser = argparse.ArgumentParser()
source_group = parser.add_mutually_exclusive_group()
source_group.add_argument("--source", help="Source filename to compare that exists in both ./source/ and ./hevc/)")
source_group.add_argument("--all", action="store_true", help="Compare all files which exist in both ./source/ and ./hevc/")
parser.add_argument("--frame", nargs=1, type=int, help="Compare SSIM values for specific frames from previously generated comparisons")
parser.add_argument("--num_frames", nargs="?", default=5, type=int, help="Number of comparison frames to generate")
parser.add_argument("--dill", action="store_true")
args = parser.parse_args()

# Verify we're working from a directory that contains expected subdirectories
if not set(["source", "hevc", "performance"]).issubset(set(os.listdir())):
	sys.exit("Invalid working directory, exiting.")

if args.all and args.frame:
	sys.exit("Error: --frame must be used with --source, not --all. Exiting.")
elif args.all:
	source_files = [filename for filename in os.listdir("source") if os.path.splitext(filename)[1] == ".mp4"]
elif args.source.endswith(".mp4"):
	source_files = [args.source]
# if args.frame, fail unless args.source exists
	# if args.frame, verify filename exists in "comparison"
else:
	sys.exit("Invalid filename, exiting.")

# if comparison directory already exists, exit

print("\nComparison frames:\t{frames}".format(frames=args.num_frames))

for source_file in source_files:
	source_file_path = os.path.join("source", source_file)
	source_file_size = int(os.path.getsize(source_file_path)/1000000)
	source_file_handle = cv2.VideoCapture(source_file_path)
	hevc_files = [filename for filename in os.listdir("hevc") if filename.startswith(os.path.splitext(source_file)[0])]

	for hevc_file in hevc_files:
		evaluate_frames = True
		output_directory = os.path.join(os.path.relpath("comparison"), os.path.splitext(os.path.basename(hevc_file))[0])
		hevc_file_path = os.path.join("hevc", hevc_file)
		hevc_file_handle = cv2.VideoCapture(hevc_file_path)
		hevc_file_size = int(os.path.getsize(hevc_file_path)/1000000)
		compression_ratio = int(100-(hevc_file_size/source_file_size*100))
		total_frames = source_file_handle.get(cv2.CAP_PROP_FRAME_COUNT)
		# get other attributes from ./performance/<<>>.log
		stride = int(total_frames/(args.num_frames+1))

		print("\nFilename:\t\t{filename}".format(filename=hevc_file))
		if source_file_handle.get(cv2.CAP_PROP_FRAME_COUNT) != hevc_file_handle.get(cv2.CAP_PROP_FRAME_COUNT):
			print("\t\t\t!!! WARNING: Frame counts do not match, screencaps may be time-shifted")
			evaluate_frames = False
		print("\tSource Size:\t{size} MB".format(size=source_file_size))
		print("\tHEVC Size:\t{size} MB".format(size=hevc_file_size))
		print("\tReduction:\t{ratio}%\n".format(ratio=compression_ratio))

		ssim_total = 0.0
		ssim_values = {}
		print("\tSSIM:")
		if not os.path.exists(output_directory): os.makedirs(output_directory)
		#if frame_resolution_differs: # e.g. letterboxing removed -- where does this go?
		for frame in range(1, args.num_frames+1):
			source_file_handle.set(cv2.CAP_PROP_POS_FRAMES,stride*frame)
			hevc_file_handle.set(cv2.CAP_PROP_POS_FRAMES,stride*frame)
			ret,source_frame = source_file_handle.read()
			ret,hevc_frame = hevc_file_handle.read()
			cv2.imwrite(os.path.join(output_directory, "{number}-source.png".format(number=frame)), source_frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
			cv2.imwrite(os.path.join(output_directory, "{number}-x265.png".format(number=frame)), hevc_frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
			if evaluate_frames:
				try:
					ssim = structural_similarity(cv2.cvtColor(source_frame, cv2.COLOR_BGR2GRAY), cv2.cvtColor(hevc_frame, cv2.COLOR_BGR2GRAY))
				except ValueError as error:
					print("\tERROR: " +str(error))
					evaluate_frames = False
				else:
					ssim_values[frame] = ssim
					ssim_total += ssim
					print("\t Frame {frame}:\t{ssim}".format(frame=frame, ssim=ssim))

		ssim_average = ssim_total/args.num_frames
		print("\tAverage:\t{average}\n".format(average=ssim_average))
		with open(os.path.join("performance", hevc_file[:-4] + ".log"), "r") as performance_file:
			duration = performance_file.readline().rstrip()
			fps = "{:0.2f}".format(float(performance_file.readline().rstrip().split(" ")[0]))
		with open(os.path.join(output_directory, "summary.txt"), "w") as summary_file:
			summary_file.write("SSIM Avg:\t{average}\nDuration:\t{duration}\nFPS:\t\t{fps}\nCompression:\t{compression}%\n\n".format(average=ssim_average, duration=duration, fps=fps, compression=compression_ratio))
			if evaluate_frames:
				for iterator in range(1, args.num_frames+1):
					summary_file.write("\t{iterator}:\t{ssim}\n".format(iterator=iterator, ssim=ssim_values[iterator]))

		hevc_file_handle.release()

	source_file_handle.release()

sys.exit("Done.\n")