#!/bin/python

"""
Takes a standard SOMD output folder with lambda directories that each contain a complete simfile.dat.
Creates a new output directory for split MBARs; native MBAR can be run on each folder in this new directory.
"""

import os
import csv
import glob
import numpy as np 
from subprocess import call

def findSimfiles():
	"""Finds all simfiles available, checks them and sorts them"""
	lam_folders = glob.glob("lambda_*/")
	simfiles = glob.glob("lambda_*/simfile.dat")
	simfiles.sort()
	# check that each lambda folder contains a simfile.
	if not len(simfiles) == len(lam_folders):
		raise Exception("Number of simfiles does not match number of lambda windows. Did they all run?")

	# check that each simfile contains data. Simfile head is 13 lines.
	for simfile in simfiles:
		num_lines = sum(1 for line in open(simfile, "r"))
		if num_lines < 50:
			raise Exception(simfile, "does not seem to contain simulation outputs. Did it run correctly?")

	return simfiles

def generateSelections(simfiles):
	"""Makes selections directory, figures out which combinations of lambdas to take and returns paths."""
	if not os.path.exists("./mbar_selections/"):
		os.mkdir("./mbar_selections/")

	num_lambdas = len(simfiles)


	# figure out which subselections of simfiles to run:
	simfile_indices = np.array(range(len(simfiles)))

	print("Constructing the following subselections of lambda windows:")
	for split_iteration in range(100):
		# if the current index array contains three or more indices:
		if len(simfile_indices) >= 3:
			print(simfile_indices)

			# Make directory for this selection:
			selection_size = len(simfile_indices)
			selection_path = "./mbar_selections/mbar_selection_"+str(selection_size)
			if not os.path.exists(selection_path):
				os.mkdir(selection_path)

			# write out a file directing the indices:
			indices_file = selection_path+"/indices.txt"
			np.savetxt(indices_file, simfile_indices, fmt='%.f')

			
			# break into the next index array (i.e. skip every other window)
			simfile_indices = simfile_indices[0::2]
		else:
			print("\n")
			break

def writeSelections(simfiles):
	"""Copy simfiles while editing them to make them correspond with their MBAR subselection"""
	mbar_selection_folders = glob.glob("mbar_selections/mbar_selection_*")
	

	for selection in mbar_selection_folders:
		print("Working on", selection+"..")
		# retrieve indices for this selection:
		selection_indices = np.loadtxt(selection+"/indices.txt", dtype=int)

		selected_simfiles = np.take(simfiles, indices=selection_indices)
		lambda_array = [simfile_path.replace("lambda_", "").replace("/simfile.dat", "") for simfile_path in selected_simfiles]

		# format floats:
		lambda_array = [round(float(lam_value), 4) for lam_value in lambda_array]


		# start grabbing simfiles:
		for simfile in selected_simfiles:
			selected_lambda_path = selection + "/" + simfile.replace("simfile.dat", "")
			if not os.path.exists(selected_lambda_path):
				os.mkdir(selected_lambda_path)

			with open(simfile, "r") as readfile, open(selected_lambda_path+"simfile.dat", "w") as writefile:
				writer = csv.writer(writefile, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar=" ")

				for row in readfile:
					if row.startswith("#"):
						# row belongs to header. We only have to adjust the lambda array:
						if row.startswith("#Alchemical array is"):

							# take the new (subselected) lambda array and make into sire formatting:
							lam_array_str = ', '.join([str(f) for f in lambda_array])
							newrow = "#Alchemical array is		 ("+lam_array_str+")"
							writer.writerow([newrow])
						else:
							writer.writerow([row])
					else:
						# row belongs to data. Columns are largely kept intact but entries have to be excluded
						# from [u_kl] to correspond with this lambda subselection.
						row_values = row.rsplit()
						fixed_values = row_values[:5]
						lambda_u_kl_values = row_values[5:]

						# using the indices that we know, take the subselection of u_kl columns for this row:
						new_u_kl_values = np.take(lambda_u_kl_values, indices=selection_indices)
						newrow = fixed_values + list(new_u_kl_values)

						# write to the new simfile:
						writer.writerow(newrow)
		print("Running MBAR..\n")
		mbar_command = "~/biosimspace.app/bin/analyse_freenrg  mbar  -i lam*/simfile.dat \
						--overlap  -p  95  --temperature  300 > MBAR.out 2> MBAR.err"
		call(mbar_command, cwd=selection, shell=True)

if __name__ == "__main__":

	simfiles = findSimfiles()

	generateSelections(simfiles)

	writeSelections(simfiles)























