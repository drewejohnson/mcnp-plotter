#-------------------------------------------------------------------------------
#                        MCNP OUTPUT PLOTTING TERMINAL
#
#       This code drops the user into a terminal where they can plot various
#           results from a number of mcnp outputs stored in various directories
#
#           Author: Andrew Johnson
#-------------------------------------------------------------------------------
#--------
# Imports
#--------
import csv
import processOuts as pouts
import mcplottools as mpt
#----------
# Constants
#----------
fpath = "figs/"
cpath = "csv/"
mpath = 'mcnp_o/'
#----------
# Functions
#----------
def showCommands():
    """Print the various commands the user can enter in the mcplot window"""
    print("-------------------Commands for obtaining and plotting data-------------------")
    print("get summary - read in all mcnp outputs and store summarized data in csv/summary.csv")
    print("plot summary - plot data from csv/summary.csv (effect of changing nps/cycle)")
    print("keff <out1> <out2> - plot convergence of eigenvalue for 1 or 2 MCNP outputs")
    print("celltally <mode> <out1> - plot cell tally data for 1 MCNP output.\n  Mode: cont or surf")
    print("runDir <working directory> - set the working directory to be cd/runDir")
    print("quit - leave this terminal")
    print("help - show this menu")
    print("-"*50)


def setRunDir():
    print("Enter the path from here to the folder containing mcnp_o directory.")
    check = input("Enter '.' if the directory is this directory: ")

    if check == ".":
        return ""
    if check[-1] != "/":
        print("  Adding '/' to the end of directory to make it work")
        check += '/'
    return check


def getSummary(runDir):
    """
    Read through all files in runDir/outputs.txt found in runDir/mcnp_o/ and
    generate summary.csv in runDir/csv with the following data per line:
    mcnp output name, number of particles/cycle, eigenvalue, standard deviation
    on eigenvalue, and run time

    Calls pouts.main which generates csv file in runDir/csv/ under the files name
    containing cell number, position, tally value, and standard deviation on
    that tally value
    """

    mcnpoutputs = "outputs.txt"     # change this is there is another listing of outputs
    # note - program is set up to read in file that consists of ONLY mcnp output names
    # on an individual line

    print("Searching for outputs.txt in "+runDir)
    while True:
        try:
            f = open(runDir+mcnpoutputs,'r')
            break
        except IOError:
            mcnpoutputs = input("MCNP Directory {0} not found.\nPlease enter name of MCNP Directory: ".format(mcnpoutputs))

    files = f.readlines()
    f.close()
    nps = []
    passL = []
    noCell = []
    badFiles = []
    try:
        sumObj = open(runDir+cpath+"summary.csv","w",newline="")
    except IOError:
        return "Could not access {0}{1}summary.csv\n  Likely that folder doesn't exist. Be a dear and make one please :D\n".\
            format(runDir,cpath)
    sumW = csv.writer(sumObj)
    # summary csv - run name, nps/cycle, eigenvalue, std devation, run time
    for line in files:
        mco = line.split()[0]
        status,vals = pouts.main(mco,runDir,cpath,mpath)           # status
        if status == 1:           # file was processed sucessfully
            passL.append(mco)
            vals.insert(0,mco)
            sumW.writerow(vals)
        elif status == -1:          # could not find tally data mcnp output
            noCell.append(mco)
        elif status == 0:
            badFiles.append(mco)    # could not access file
    sumObj.close()
    print("-+-"*20)
    if noCell != []:
        print("Cell data was not found in the following files:")
        for f in noCell:
            print(f)
        print("  The file(s) could be the wrong type or not complete")
    if badFiles != []:
        print("Could not access the following files:")
        for f in badFiles:
            print(f)
        print("Any file not listed above ran successfullly")
    return "All completed cell csv files are listed in {0}{1}\n".format(runDir,cpath)

#--------------------------
# Main Function - mcplotter
#--------------------------

def mcplotter():
    print("-"*25+"MCNP PLOTTING TERMINAL"+"-"*25)
    showCommands()
    print("NOTE: All plotting requires working versions of numpy and matplotlib")
    runDir = setRunDir()      # working directory
    while True:
        uIn = input("mcplotter@{0}:  ".format(runDir))
        uInS = uIn.split()
        # plot data from csv/summary.csv
        if uIn == "plot summary":
            print(mpt.main("summary.csv",runDir,cpath,fpath),end="")
        # obtain summary data from mcnp outputs
        elif uIn == "get summary":
            print(getSummary(runDir),end="")
        # plot convergence of keff
        elif uIn[:4] == 'keff':
            if len(uInS) == 2:
                print(mpt.plotCycleK(runDir,fpath,mpath+uInS[1]),end="")
            elif len(uInS) == 3:
                print(mpt.plotCycleK(runDir,fpath,mpath+uInS[1],mpath+uInS[2]),end="")
            else:
                print("Bad number of files for keff plot. One or two mcnp outputs \n  {0}".format(uIn))
        # plot cell tally data
        elif uIn[:9] == "celltally":
            if len(uIn.split()) != 3:
                print("Bad input for cell tally. celltally <mode> <out1>")
            else:
                print(mpt.plotCellTally(runDir,cpath,fpath,uIn.split()[2],uIn.split()[1]),end="")
        # leave this cursed terminal
        elif uIn == "quit":
            break
        elif uIn == "help":
            showCommands()
        elif uInS[0] == "runDir":
            runDir = uInS[-1]
            if runDir[-1] != "/":
                runDir += "/"
        else:
            print("Bad input.")

mcplotter()
