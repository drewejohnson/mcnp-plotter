# mcnp-plotter
Various utilities to plot MCNP results including convergence on eigenvalue and tally results. Also supports comparison plots

##Purpose
This project grew from a need to plot comparison between two different types of MCNP runs. The current version focuses on changes in eigenvalue, standard deviation, and run time in KCODE calculations. Plots of cell fluxes for 2D problems can also be generated, as contour plots or surface plots. These depend on a locations file, more on that in the *File Requirements* section.

## Software Requirements
This code was written to run on Python 3.5 or later, so you need that. Plus, all the plotting features are done natively through `matplotlib` 1.5, so all the required modules for `matplotlib` are required for this. See [Matplotlib Installation Instructions](http://matplotlib.org/users/installing.html) for more instructions.

## Installation/Run Instructions
- Fork or clone this repository or download the three `.py` files in the latest `master` branch
- Save the three files in the same folder, ideally in the same location as the directory containing the required files
- Run `mcplotter.py` however you usually go about running python files
- You will be dropped into a terminal-style menu that should describe how to get plotting data and how to plot the plotting data. 
- For more instructions, see the wiki

## File Requirements
Currently, the following file and folders are required. I intend to, at some point, make this process a bit easier by using the `python os` module and some fancy mcnp plot techniques, but for now, these files are required. 
For the example, `pydir` is the directory where you have saved the required python files. `runDir` is the directory where all of your runs and folders should be located:

- `pydir/runDir/locations.txt` - text file with cell locations for plotting cell tally values
- `pydir/runDir/outputs.txt` - file with the names of mcnp outputs you want analyzed
- `pydir/runDir/mcnp_o/` - directory with all the mcnp output files mentioned in `pydir/runDir/outputs.txt`
- `pydir/runDir/csv/` - directory that will hold .csv files with cell tally data for each run in `pydir/runDir/outputs.txt` and will contain `summar.csv` to show run name, number of particles/cycle used, final eigenvalue, standard deviation on final eigenvalue, and computer run time
- `pydir/runDir/figs/` - directory that will hold all figures created by all the plots your heart can handle

More references and instructions will be in the wiki page soon. Enjoy! And good luck!
