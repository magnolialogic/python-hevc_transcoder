#!/usr/local/bin/python3

import argparse
import cv2
import imutils
import os
from skimage.metrics import structural_similarity
import sys

sys.path.append(os.path.join(sys.path[0], "lib"))
try:
	from common import get_choice_from_menu
except ImportError:
	sys.exit("FATAL: failed to import dependencies from ./lib/\n")

parser = argparse.ArgumentParser()
parser.add_argument("--dir")
parser.add_argument("--frame")
args = parser.parse_args()

if not args.dir:
	choices = sorted([file for file in os.listdir("comparison") if os.path.isdir(os.path.join("comparison", file))])
	if len(choices) == 0:
		sys.exit("\nNo transcode directories to evaluate.\n")
	else:
		print("\nChoose a transcode to evaluate:")
		transcode = choices[get_choice_from_menu(choices)]
else:
	if args.dir in os.listdir("comparison"):
		transcode = args.dir
	else:
		sys.exit("Invalid directory.\n")

# TODO: frame arg

screenshots = sorted([file for file in os.listdir(os.path.join("comparison", transcode)) if file.endswith(".png")], key=lambda filename: int(filename.split("-")[0]))

if not (len(screenshots) % 2 == 0):
	sys.exit("ERROR: Odd number of screenshots found in {directory}".format(directory=transcode))
else:
	num_screenshots = int(len(screenshots)/2)


#TODO: integrate into compareEncoding.py, error out if source/hevc dimenions !=

if os.path.exists(os.path.join("comparison", transcode, "summary.txt")):
	sys.exit("\nsummary.txt exists, {transcode} has already been evaluated.\n\nExiting.\n".format(transcode=transcode))

file_info = {"filename": transcode}
with open(os.path.join("performance", transcode + ".log"), "r") as log_file:
	file_info["duration"] = log_file.readline().rstrip()
	file_info["fps"] = "{:0.2f}".format(float(log_file.readline().rstrip().split(" ")[0]))
	file_info["compression"] = log_file.readline().rstrip().split(" ")[0]
	for line in log_file:
		if "bitrate" in line:
			file_info["bitrate"] = int(line.rstrip().split(": ")[2][:-1])
		elif "height" in line:
			file_info["height"] = line.rstrip().split(": ")[1][:-1]
		elif "width" in line:
			file_info["width"] = line.rstrip().split(": ")[1][:-2]
		elif "encoder_quality" in line:
			file_info["encoder_quality"] = line.rstrip().split(": ")[1][:-1]
		elif "encoder_preset" in line:
			file_info["encoder_preset"] = line.rstrip().split(": ")[1][1:-2]
		elif "encoder_options" in line:
			file_info["encoder_options"] = line.rstrip().split(": ")[1][1:-2]

print(" Resolution:\t{resolution}".format(resolution=file_info["width"] + "x" + file_info["height"]))
print(" Bitrate:\t{bitrate}".format(bitrate=str(int(file_info["bitrate"] / 1000)) + "kbps"))
print(" Encoder:\t{settings}".format(settings=str("RF" + file_info["encoder_quality"] + " " + file_info["encoder_preset"] + ", " + file_info["encoder_options"])))
print(" Duration:\t{duration}".format(duration=file_info["duration"]))
print(" FPS:\t\t{fps}".format(fps=str(file_info["fps"])))
print(" Compression:\t{ratio}".format(ratio=file_info["compression"]))

print("\n SSIM:")
ssim_total = 0.0
ssim_values = {}
for image_iterator in range(1, num_screenshots+1):
	screenshot_pair = sorted([os.path.join("comparison", transcode, screenshot) for screenshot in screenshots if screenshot.split("-")[0] == str(image_iterator)])
	ssim = structural_similarity(cv2.cvtColor(cv2.imread(screenshot_pair[0]), cv2.COLOR_BGR2GRAY), cv2.cvtColor(cv2.imread(screenshot_pair[1]), cv2.COLOR_BGR2GRAY))
	#(score, diff) = structural_similarity(source_grayscale, hevc_grayscale, full=True)
	# What does the full image get me?
	ssim_values[image_iterator] = ssim
	print("  Frame {image_iterator}:\t{ssim}".format(image_iterator=image_iterator, ssim=ssim))
	ssim_total += ssim

ssim_average = ssim_total/num_screenshots
print(" Average:\t{average}\n".format(average=ssim_average))

with open(os.path.join("comparison", transcode, "summary.txt"), "w") as summary_file:
	summary_file.write("SSIM Avg:\t{average}\nDuration:\t{duration}\nFPS:\t\t{fps}\nCompression:\t{compression}\n\n".format(average=ssim_average, duration=file_info["duration"], fps=file_info["fps"], compression=file_info["compression"]))
	for iterator in range(1, num_screenshots+1):
		summary_file.write("\t{iterator}:\t{ssim}\n".format(iterator=iterator, ssim=ssim_values[iterator]))