#!/usr/local/bin/python3

import argparse
import cv2
from datetime import datetime, timedelta
import dill
import imutils
import numpy as np
import os
from pprint import pprint
from skimage.metrics import structural_similarity
import subprocess
import sys

# Verify script is colocated with ./lib/ and import dependencies
sys.path.append(os.path.join(sys.path[0], "lib"))
try:
	from common import get_choice_from_menu
except ImportError:
	sys.exit("FATAL: failed to import dependencies from ./lib/\n")

# Verify we're working from a directory that contains expected subdirectories
if not set(["source", "performance"]).issubset(set(os.listdir())):
	sys.exit("Invalid working directory, exiting.")

source_files = [filename for filename in os.listdir("source") if os.path.splitext(filename)[1] == ".mp4"]
comparisons = {}

for source_file in source_files:
	comparison_directories = [filename for filename in os.listdir("comparison") if filename.startswith(os.path.splitext(source_file)[0])]
	movie_name = source_file.split(".")[0]

	transcodes = {}

	for directory in comparison_directories:
		summary_file = os.path.join("comparison", directory, "summary.txt")
		transcode_options = directory.split("-")[1].split("_")
		transcode_options.pop(0)

		if "Baseline" in transcode_options:
			quality = "Baseline"
		else:
			quality = transcode_options[0]
			transcode_options.pop(0)

		if quality not in transcodes:
			transcodes[quality] = {}

		with open(summary_file, "r") as file:
			data = {"ssim": file.readline().rstrip().split("\t")[1]}
			data["duration"] = file.readline().rstrip().split("\t")[1]
			data["fps"] = file.readline().rstrip().split("\t")[2]
			data["compression"] = file.readline().rstrip().split("\t")[1]

		if quality == "Baseline":
			transcodes[quality] = data
		else:
			transcodes[quality]["_".join(transcode_options)] = data

	comparisons[movie_name] = transcodes

for movie_name in sorted(comparisons.keys()):
	print(movie_name)
	for key, value in sorted(comparisons[movie_name].items()):
		if key == "Baseline":
			print("Baseline", value["ssim"], "-", value["duration"], "-", str(value["compression"]) + "%", "-", value["fps"], sep="\t")
		else:
			for variant in comparisons[movie_name][key]:
				name = key + "_" + variant
				ssim_delta = float(value[variant]["ssim"]) - float(comparisons[movie_name]["Baseline"]["ssim"])
				#duration_delta = timedelta(seconds = (datetime.strptime(value[variant]["duration"], "%H:%M:%S.%f") - datetime.strptime(comparisons[movie_name]["Baseline"]["duration"], "%H:%M:%S.%f")).total_seconds())
				compression_delta = str(int(value[variant]["compression"]) - int(comparisons[movie_name]["Baseline"]["compression"])) + "%"
				print(name, value[variant]["ssim"], ssim_delta, value[variant]["duration"], "", str(value[variant]["compression"]) + "%", compression_delta, value[variant]["fps"], sep="\t")
	print()
	print()
	print()