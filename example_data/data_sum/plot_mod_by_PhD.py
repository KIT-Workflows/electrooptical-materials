import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
'''
For guidance, Nature's standard figure sizes are 89 mm wide (single column) and 183 mm wide (double column).
The full depth of a Nature page is 247 mm. Figures can also be a column-and-a-half where necessary (120–136 mm).
'''
width =89
height =  89# width double column183
global_figsize=(width/25.4, height/25.4)  # Convert mm to inches for matplotlib
matplotlib.rcParams['figure.figsize'] = global_figsize
matplotlib.rcParams['font.size'] = 7 # nature itself recommends 5-7 pt
matplotlib.rc("image", cmap="viridis")  # Set default colormap to viridis for color blind friendliness
#colors should cycle through  colors from viridis
matplotlib.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=plt.cm.viridis(np.linspace(0, 1, 6)))
# Use LaTeX for all text rendering
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'Computer Modern Sans Serif']
#set latex default font size to 7pt

# Custom LaTeX preamble for Helvetica and proper math rendering
matplotlib.rcParams['text.latex.preamble'] = r"""
	\usepackage{tgheros}
	\usepackage{sansmath}
	\sansmath
	\usepackage{siunitx}
	\sisetup{detect-all}
"""

def main():
	#first we need the dataframe
	file="example_data/data_sum/electroopitcal.xlsx"
	df = pd.read_excel(file, sheet_name="Tabelle1")
	
	#set the "name" column as index
	df.set_index("name", inplace=True)
	
	sorted_df = df.sort_values(by="exp", ascending=True)
	#plot values of sorted_df exp vs all columns that are not exp not source and not name
	columns_to_plot = sorted_df.columns.difference(["exp", "source", "name"])
	fig, ax = plt.subplots(figsize=global_figsize)
	for col in columns_to_plot:
		ax.plot(sorted_df["exp"], sorted_df[col], "x", label=col)
	#plot the exp column as a line
	ax.plot(sorted_df["exp"], sorted_df["exp"], "k-")
	ax.set_xlabel(r"literature [$10^{-30}$ esu]", usetex=True)
	ax.xaxis.set_label_position('top')
	ax.xaxis.set_label_coords(0.5, 1.05)
	
	ax.set_ylabel(r"prediction [$10^{-30}$ esu]", usetex=True)
	#we want the xticks to be the name entries
	# Keep the x-axis scale as normal (exp values), but annotate each point with the index string below the x-axis
	scale_it=.3# to scale the offsets- needs to be adapted to the figure size
	for x, label in zip(sorted_df["exp"], sorted_df.index):
		if label =="P1":
			xoffset=10
		elif label =="P3":
			xoffset=-0
		elif label =="P4":
			xoffset=-10
		elif label =="P5":
			xoffset= -20
		else:
			xoffset=0	
		ax.annotate(
			fr"\texttt{{{label}}}",  # Use LaTeX monospace for labels
			(x, ax.get_ylim()[0]),
			xytext=(xoffset*scale_it, -20),
			textcoords='offset points',
			ha='center',
			va='top',
			rotation=90,
			fontsize=7,
			usetex=True
		)
	#set x axis and y axis to be equal
	#ax.set_aspect('equal', adjustable='box')
	#move it down further to avoid overlap with inset
	ax.legend(loc='center left', bbox_to_anchor=(0, 0.3))
	
	#make an inset of the plot focusing on the lower left corner. position the inset at the upper left corner
	from mpl_toolkits.axes_grid1.inset_locator import inset_axes
	axins = inset_axes(ax, width="40%", height="40%", loc='upper left', borderpad=1)
	# Set the limits for the inset
	x1, x2 = 40, 120  # Adjust these values as needed
	y1, y2 = 40, 240  # Adjust these values as needed
	axins.set_xlim(x1, x2)
	axins.set_ylim(y1, y2)
	# Plot the same data on the inset axes if it contains the P1, P3, P4, P5 points
	for col in columns_to_plot:
		if ((sorted_df["exp"] >= x1) & (sorted_df["exp"] <= x2) & (sorted_df[col] >= y1) & (sorted_df[col] <= y2)).any():
			axins.plot(sorted_df["exp"], sorted_df[col], "x", label=col)
	axins.plot(sorted_df["exp"], sorted_df["exp"], "k-")
	
	#legend for insert
	#axins.legend(fontsize=6)
	#annotate points in inset
	for x, label in zip(sorted_df["exp"], sorted_df.index):
		if x1 <= x <= x2:
			y = sorted_df.loc[label, columns_to_plot].max()
			if y1 <= y <= y2:
				# annotate the inset's x-axis (place label just below the inset x-axis)
				axins.annotate(
					fr"\texttt{{{label}}}",
					(x, axins.get_ylim()[0]),
					xytext=(0, -8),
					textcoords='offset points',
					ha='center',
					va='top',
					rotation=90,
					fontsize=6,
				)

	plt.savefig("example_data/data_sum/plot_all_PhD.pdf", bbox_inches='tight')
	#plt.show()
	#clear figure and axis to avoid replotting 
	plt.clf()
	plt.cla()
	plt.close()  # Close the figure to free memory
	

	fig, ax = plt.subplots(figsize=global_figsize)
	x_values = np.arange(len(sorted_df))
	for col in columns_to_plot:
		ax.plot(x_values, sorted_df[col]/sorted_df["exp"], "x", label=col)
	#plot the exp column as a line
	#ax.plot(sorted_df["exp"], sorted_df["exp"], "k-")
	#ax.set_xlabel(r"literature [$10^{-30}$ esu]", usetex=True)
	#ax.xaxis.set_label_position('top')
	#ax.xaxis.set_label_coords(0.5, 1.05)

	ax.set_ylabel(r"prediction / literature ", usetex=True)
	#we want the xticks to be the name entries
	# Keep the x-axis scale as normal (exp values), but annotate each point with the index string below the x-axis
	for x, label in zip(sorted_df["exp"], sorted_df.index):
		ax.annotate(
			fr"\texttt{{{label}}}",  # Use LaTeX monospace for labels
			(x, ax.get_ylim()[0]),
			xytext=(0, -20),
			textcoords='offset points',
			ha='center',
			va='top',
			rotation=90,
			fontsize=7,
			usetex=True
		)
	#set x axis and y axis to be equal
	#ax.set_aspect('equal', adjustable='box')
	ax.legend()
	plt.savefig("example_data/data_sum/plot_all_PhD_ratio.pdf", bbox_inches='tight')
	#plt.show()
	#clear figure and axis to avoid replotting 
	plt.clf()
	plt.cla()
	plt.close()  # Close the figure to free memory
	
	#now also as a bar plot like the ones below


	fig, ax = plt.subplots(figsize=global_figsize)
	# grouped bar plot: narrow bars with offsets so columns don't overlap
	x_values = np.arange(len(sorted_df))
	n_cols = len(columns_to_plot)
	if n_cols == 0:
		n_cols = 1
	bar_width = 0.8 / n_cols  # total 80% width per group

	for idx, col in enumerate(columns_to_plot):
		offset = (idx - n_cols / 2) * bar_width + bar_width / 2
		ax.bar(x_values + offset, sorted_df[col] / sorted_df["exp"],
			   width=bar_width, label=col)

	#plot the exp column as a line

	# ax.set_xlabel(r"literature [$10^{-30}$ esu]", usetex=True)
	# ax.xaxis.set_label_position('top')
	# ax.xaxis.set_label_coords(0.5, 1.05)

	ax.set_ylabel(r"prediction / literature", usetex=True)
	#we want the xticks to be the name entries
	# Keep the x-axis as normal (exp values), but annotate each point with the index string below the x-axis
	for x, label in zip(sorted_df["exp"], sorted_df.index):
		ax.annotate(
			fr"\texttt{{{label}}}",  # Use LaTeX monospace for labels
			(x, ax.get_ylim()[0]),
			xytext=(0, -20),
			textcoords='offset points',
			ha='center',
			va='top',
			rotation=90,
			fontsize=7,
			usetex=True
		)
	
	# set xticks to index positions and label them via LaTeX
	ax.set_xticks(x_values)
	ax.set_xticklabels([fr"\texttt{{{label}}}" for label in sorted_df.index], rotation=90, usetex=True)
	ax.legend()
	plt.savefig("example_data/data_sum/plot_all_PhD_ratio_bar.pdf", bbox_inches='tight')
	#plt.show()
	#clear figure and axis to avoid replotting 
	plt.clf()
	plt.cla()
	plt.close()  # Close the figure to free memory


	#now we do the same again but only plot the part that is source i in the plot of plot_i.pdf
	max_sources= sorted_df["source"].max()
	min_sources= sorted_df["source"].min()
	#fig, ax = plt.subplots(figsize=global_figsize)
	for i in range(min_sources, max_sources+1):
		fig, ax = plt.subplots(figsize=global_figsize)
		sorted_df_i = sorted_df[sorted_df["source"] == i]
		for col in columns_to_plot:
			ax.plot(sorted_df_i["exp"], sorted_df_i[col], "x", label=col)
		ax.plot(sorted_df_i["exp"], sorted_df_i["exp"], "k-")
		ax.set_xlabel(r"literature [$10^{-30}$ esu]", usetex=True)
		ax.xaxis.set_label_position('top')
		ax.xaxis.set_label_coords(0.5, 1.05)
		ax.set_ylabel(r"prediction [$10^{-30}$ esu]")
			# Keep the x-axis scale as normal (exp values), but annotate each point with the index string below the x-axis
		for x, label in zip(sorted_df_i["exp"], sorted_df_i.index):
				ax.annotate(
					fr"\texttt{{{label}}}",  # Use LaTeX monospace for labels
					(x, ax.get_ylim()[0]),
					xytext=(0, -20),
					textcoords='offset points',
					ha='center',
					va='top',
					rotation=90,
					fontsize=7,
					usetex=True
				)
		ax.legend()
		plt.savefig(f"example_data/data_sum/plot_source_{i}.pdf", bbox_inches='tight')
		#plt.show()
		plt.clf()
		plt.cla()
		plt.close()  # Close the figure to free memory

	#now we still do it separately but plot the ratios. x axis is just equally spaced from 0 to N where N
	#is the number of entries in sorted_df_i
	
	for i in range(min_sources, max_sources+1):	
		fig, ax = plt.subplots(figsize=global_figsize)
		sorted_df_i = sorted_df[sorted_df["source"] == i]
		x_values = np.arange(len(sorted_df_i))
		for col in columns_to_plot:
			ax.plot(x_values, sorted_df_i[col] / sorted_df_i["exp"], "x", label=col)
		ax.plot(x_values, np.ones_like(x_values), "k-")
		#ax.set_xlabel("")
		
		ax.set_ylabel(r"prediction / literature value", usetex=True)
		ax.set_xticks(x_values)
		ax.set_xticklabels([fr"\texttt{{{label}}}" for label in sorted_df_i.index], rotation=90, usetex=True)
		ax.legend()
		plt.savefig(f"example_data/data_sum/plot_source_{i}_ratio.pdf", bbox_inches='tight')
		#plt.show()
		plt.clf()
		plt.cla()
		plt.close()  # Close the figure to free memory

	#jia likes bar diagrams so we do the bar diagrams for the ratios (same as obve just not point plots)
	
	for i in range(min_sources, max_sources+1):
		fig, ax = plt.subplots(figsize=global_figsize)
		sorted_df_i = sorted_df[sorted_df["source"] == i]
		x_values = np.arange(len(sorted_df_i))
		n_cols = len(columns_to_plot)
		bar_width = 0.8 / n_cols  # 80% of space per exp entry, divided among columns

		for idx, col in enumerate(columns_to_plot):
			offset = (idx - n_cols / 2) * bar_width + bar_width / 2
			ax.bar(x_values + offset, sorted_df_i[col] / sorted_df_i["exp"], 
				   width=bar_width, label=col)

		ax.axhline(y=1, color='k', linestyle='-')
		#ax.set_xlabel("")
		ax.set_ylabel(r"prediction / literature value", usetex=True)
		ax.set_xticks(x_values)
		ax.set_xticklabels([fr"\texttt{{{label}}}" for label in sorted_df_i.index], rotation=90, usetex=True)
		ax.legend()
		plt.savefig(f"example_data/data_sum/plot_source_{i}_ratio_bar.pdf", bbox_inches='tight')
		plt.clf()
		plt.cla()#plt.show()
		plt.close()  # Close the figure to free memory

if __name__ == "__main__":
	main()

'''
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path




def main():
	#first we need the dataframe
	file="example_data/data_sum/electroopitcal.xlsx"
	df = pd.read_excel(file, sheet_name="Tabelle1")
	print(df)
	#set the "name" column as index
	df.set_index("name", inplace=True)
	
	sorted_df = df.sort_values(by="exp", ascending=True)
	#plot values of sorted_df exp vs all columns that are not exp not source and not name
	columns_to_plot = sorted_df.columns.difference(["exp", "source", "name"])
	fig, ax = plt.subplots(figsize=(15,15))
	for col in columns_to_plot:
		ax.plot(sorted_df["exp"], sorted_df[col], "x", label=col)
	#plot the exp column as a line
	ax.plot(sorted_df["exp"], sorted_df["exp"], "k-")
	ax.set_xlabel(r"literature [$10^{-30}$ esu]")
	ax.set_ylabel(r"prediction [$10^{-30}$ esu]")
	#we want the xticks to be the name entries
	# Keep the x-axis scale as normal (exp values), but annotate each point with the index string below the x-axis
	for x, label in zip(sorted_df["exp"], sorted_df.index):
		ax.annotate(
			fr"\texttt{{{label}}}",  # Use LaTeX monospace for labels
			(x, ax.get_ylim()[0]),
			xytext=(0, -20),
			textcoords='offset points',
			ha='center',
			va='top',
			rotation=90,
			fontsize=7,
			usetex=True
		)
	#set x axis and y axis to be equal
	#ax.set_aspect('equal', adjustable='box')
	ax.legend()
	plt.savefig("example_data/data_sum/plot_all_PhD.pdf", bbox_inches='tight')
	#plt.show()
	#clear figure and axis to avoid replotting 
	plt.clf()
	plt.cla()
	

	#now we do the same again but only plot the part that is source i in the plot of plot_i.pdf
	max_sources= sorted_df["source"].max()
	min_sources= sorted_df["source"].min()
	for i in range(min_sources, max_sources+1):
		fig, ax = plt.subplots(figsize=global_figsize)
		sorted_df_i = sorted_df[sorted_df["source"] == i]
		for col in columns_to_plot:
			ax.plot(sorted_df_i["exp"], sorted_df_i[col], "x", label=col)
		ax.plot(sorted_df_i["exp"], sorted_df_i["exp"], "k-")
		ax.set_xlabel(r"literature [$10^{-30}$ esu]")
		ax.set_ylabel(r"prediction [$10^{-30}$ esu]")
		# Keep the x-axis scale as normal (exp values), but annotate each point with the index string below the x-axis
		for x, label in zip(sorted_df_i["exp"], sorted_df_i.index):
			ax.annotate(
				fr"\texttt{{{label}}}",  # Use LaTeX monospace for labels
				(x, ax.get_ylim()[0]),
				xytext=(0, -20),
				textcoords='offset points',
				ha='center',
				va='top',
				rotation=90,
				fontsize=7,
				usetex=True
			)
		ax.legend()
		plt.savefig(f"example_data/data_sum/plot_source_{i}.pdf", bbox_inches='tight')
		plt.clf()
		plt.cla()

	#now we still do it separately but plot the ratios. x axis is just equally spaced from 0 to N where N
	#is the number of entries in sorted_df_i
	for i in range(min_sources, max_sources+1):	
		fig, ax = plt.subplots(figsize=global_figsize)
		sorted_df_i = sorted_df[sorted_df["source"] == i]
		x_values = np.arange(len(sorted_df_i))
		for col in columns_to_plot:
			ax.plot(x_values, sorted_df_i[col] / sorted_df_i["exp"], "x", label=col)
		ax.plot(x_values, np.ones_like(x_values), "k-")
		#ax.set_xlabel("index")
		ax.set_ylabel(r"prediction / literature value")
		ax.set_xticks(x_values)
		ax.set_xticklabels(sorted_df_i.index, rotation=90)
		ax.legend()
		plt.savefig(f"example_data/data_sum/plot_source_{i}_ratio.pdf", bbox_inches='tight')
		#plt.show()
		plt.clf()
		plt.cla()

	#jia likes bar diagrams so we do the bar diagrams for the ratios (same as obve just not point plots)

	for i in range(min_sources, max_sources+1):
		fig, ax = plt.subplots(figsize=global_figsize)
		sorted_df_i = sorted_df[sorted_df["source"] == i]
		x_values = np.arange(len(sorted_df_i))
		n_cols = len(columns_to_plot)
		bar_width = 0.8 / n_cols  # 80% of space per exp entry, divided among columns

		for idx, col in enumerate(columns_to_plot):
			offset = (idx - n_cols / 2) * bar_width + bar_width / 2
			ax.bar(x_values + offset, sorted_df_i[col] / sorted_df_i["exp"], 
				   width=bar_width, label=col)

		ax.axhline(y=1, color='k', linestyle='-')
		#ax.set_xlabel("index")
		ax.set_ylabel("prediction / literature value")
		ax.set_xticks(x_values)
		ax.set_xticklabels(sorted_df_i.index, rotation=90)
		ax.legend()
		plt.savefig(f"example_data/data_sum/plot_source_{i}_ratio_bar.pdf", bbox_inches='tight')
		plt.clf()
		plt.cla()#plt.show()
'''
if __name__ == "__main__":
	main()
