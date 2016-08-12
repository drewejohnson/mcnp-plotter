#-------------------------------------------------------------------------------
#               PLOTTING TOOLS FOR MCPLOTTER
#
#   Plots a whole lot of things including:
#       - change in keff over 1 or 2 mcnp runs
#       - tally data
#           - requires data be in csv folder
#       - comparisons for how changing the number of particles per cycle affects
#           run time, eigenvalue, and standard deviation
#           - requires processed outputs be in csv folder in summary.csv
#
#               Author: Andrew Johnson
#-------------------------------------------------------------------------------
#--------
# Imports
#--------
import csv
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D     # 3D plotter
from matplotlib import cm                   # color maps
#----------
# Constants
#----------
pInput = "Save figure(s)? [y/n]\n:  "
#--------
# Classes
#--------
class RunType:

    def __init__(self):
        self.eig = []
        self.stdv = []
        self.run = []
        self.nps = []

    def addRow(self,row):
        self.eig.append(float(row[2]))
        self.stdv.append(float(row[3]))
        self.run.append(float(row[4]))
        self.nps.append(int(row[1]))

#----------
# Functions
#----------
def getRunName(fStr):
    """Return the run name from an mcnp_o found at fStr"""
    if fStr[-2:] =="_o":
        return fStr.split("/")[-1][:-2]
    else:
        return fStr.split("/")[-1][:-1]

def getPrintName(printCheck):
    if len(printCheck.split()) > 1:
        rList = printCheck.split()[-1].split(".")
        # if one element: target name was given without extension
        # if multiple elements: target name was given with extension as last item
        if len(rList) == 1:
            # default to save file as .pdf
            return rList[0],".pdf"
        else:
            return rList[0],"."+rList[-1]
    else:
        return "",""

def getRunSummary(fObj):
    """Return two RunType instances for forward and adjoint run summaries"""
    cr = csv.reader(fObj,delimiter=',')
    f = RunType()
    a = RunType()
    for row in cr:
        if row[0][0] == 'f':
            f.addRow(row)
        elif row[0][0] == 'a':
            a.addRow(row)
        else:
            print("Bad data found in {0}".format(tFile))
            print(row)
    return f,a

def plotter(f,a):
    """Plot the various summary comparisons"""
    # Eigenvalue
    eigFig = plt.figure()
    plt.plot(f.nps,f.eig,'ro',label='forward')
    plt.plot(a.nps,a.eig,'bo',label='adjoint')
    plt.legend(numpoints=1)
    plt.xlabel('Number of particles/cycle')
    plt.ylabel('Eigenvalue')
    plt.show()
    # Standard Deviation
    stdvFig = plt.figure()
    plt.plot(f.nps,f.stdv,'ro',label='foward')
    plt.plot(a.nps,a.stdv,'bo',label='adjoint')
    plt.legend(numpoints=1)
    plt.xlabel("Number of Particles/cycle")
    plt.ylabel("Relative Standard Deviation on Eigenvalue")
    plt.show()
    # Run Times
    runFig = plt.figure()
    plt.plot(f.nps,f.run,'ro',label='foward')
    plt.plot(a.nps,a.run,'bo',label='adjoint')
    plt.legend(numpoints=1)
    plt.xlabel("Number of Particles/cycle")
    plt.ylabel("Run Time (minutes)")
    plt.show()
    return eigFig,runFig,stdvFig

def saveFig(fName,figObj):
    if len(fName.split(".")) == 1:
        fName += ".pdf"     # default to saving as pdf
    if fName[-4:] == '.pdf':
        with PdfPages(fName) as pdf:
            pdf.savefig(figObj)
    elif fName[-4:] == '.png':
        figObj.savefig(fName,format="png")
    else:
        return "File extension for {0} not supported at this time\n".format(fName)
    return "Saved figure to {0}\n".format(fName)

def plotCycleK(runDir,fpath,t1,t2=None):
    """Plot the convergance of eigenvalue for one or two files t1 and t2"""
    t1 = runDir + t1
    try:
        f1 = open(t1,'r')
    except IOError:
        return "  Could not open file {0}\n".format(t1)

    cycles1,keff1,stdv1 = getK(f1)
    if cycles1 == []:                   # no keff data in file 1
        return "  No keff cycle data found in file {0}\n".format(t1)
    t1R = getRunName(t1)

    f1.close()
    if t2 != None:
        t2 = runDir + t2
        try:
            f2 = open(t2,'r')
        except IOError:
            return "  Could not open file {0}\n".format(t2)
        cycles2,keff2,stdv2 = getK(f2)
        f2.close()
        if cycles2 == []:                   # no keff data in file 2
            return "  No keff cycle data found in file {0}\n".format(t2)
        t2R = getRunName(t2)

    kFig = plt.figure()
    plt.plot(cycles1,keff1,'bo',label=t1R)
    if t2 != None:
        plt.plot(cycles2,keff2,'ro',label=t2R)
    plt.legend(numpoints=1)#,loc=4)
    plt.xlabel("MCNP Active Cycle Number")
    plt.ylabel("Eigenvalue")
    plt.show()

    printCheck = input(pInput)
    if printCheck[0] == 'y':
        runN,runExt = getPrintName(printCheck)
        return saveFig(runDir+fpath+runN+"keff"+runExt,kFig)
    return ""

def getK(fObj):
    """Returns three lists from file object fObj: cycle number, keff, and std dev"""
    cyc = []
    keff = []
    stdv = []
    activeKeffRgx = r'.+begin active keff cycles'
    keffRgx = r' *(\d+).+\|.+\|.+\| +([\d\.]+) +([\d\.]+)'
    line = fObj.readline()
    while line != "":
        line = fObj.readline()
        activeMatch = re.match(activeKeffRgx,line)
        if activeMatch != None:
            while line != "\n":
                line = fObj.readline()
                kMatch = re.findall(keffRgx,line)
                if kMatch != []:
                    cyc.append(int(kMatch[0][0]))
                    keff.append(float(kMatch[0][1]))
                    stdv.append(float(kMatch[0][2]))
            break
    return cyc,keff,stdv

def plotCellTally(runDir,cpath,fpath,mcOut,pMode):
    """Plot cell tallies from runDir/csv/mcOut as contours"""

    if mcOut[-4:] != ".csv":
        print("  Adding .csv to {0}".format(mcOut))
        mcOut += ".csv"

    try:
        fObj = open(runDir+cpath+mcOut,'r')
    except IOError:
        return "Could not access file {0}\n".format(runDir+cpath+mcOut)

    cr = csv.reader(fObj,delimiter=",")
    r = 0
    x = []
    y = []
    t = []
    xG = []
    yG = []
    for row in cr:
        if r > 0:       # header lines
            x.append(float(row[1]))
            if x[-1] not in xG:
                xG.append(x[-1])    # unique x coordinates for plotting
            y.append(float(row[2]))
            if y[-1] not in yG:
                yG.append(y[-1])
            t.append(float(row[4]))     # tally data
        else:
            r += 1
    fObj.close()
    # Prepare to plot by making axes
    xG.sort()       # put the unique values in descending order
    yG.sort()
    xL = len(xG)
    yL = len(yG)
    cells = len(x)
    X,Y = np.meshgrid(xG,yG)        # create matrices of x and y grid vectors for plotting
    tmat = np.empty([yL,xL])        # tally matrix
    for jj in range(yL):
        for ii in  range(xL):
            for r in range(cells):
                if X[jj,ii] == x[r] and Y[jj,ii] == y[r]:
                    tmat[yL-jj-1,ii] = t[r]
    # Plot tally data
    tallyFig = plt.figure()
    if pMode[:4] == 'cont':
        plt.contour(X,Y,tmat)
        plt.xlabel("Cell X Location (cm)")
        plt.ylabel("Cell Y Location (cm)")
    elif pMode[:4] == 'surf':
        ax = tallyFig.gca(projection='3d')
        ax.plot_surface(X,Y,tmat,rstride=1,cstride=1,cmap = cm.coolwarm)
        ax.set_xlabel("Cell X Location (cm)")
        ax.set_ylabel("Cell Y Location (cm)")
        ax.set_zlabel("Tally Value")
    else:
        return "Plot mode {0} not supported.".format(pMode)
    plt.show()
    printCheck = input(pInput)
    if printCheck[0] == 'y':
        runN,runExt = getPrintName(printCheck)
        if runN != "":
            return(saveFig(runDir+fpath+runN+pMode+"tally"+runExt,tallyFig))
    return ""

def main(sumFile,runDir,cpath,fpath):
    """Main function to plot the summary data from sumFile"""

    if sumFile == None:
        sumFile = input("Enter the .csv with the summary data: ")
    tFile = runDir+cpath+sumFile

    while True:
        try:
            fObj = open(tFile,'r')
            break
        except IOError:
            print("--File not accessible--")
            sumFile = input("Enter the .csv with the summary data: ")

    f,a = getRunSummary(fObj)
    fObj.close()
    eigFig,runFig,stdvFig = plotter(f,a)     # tuple with eigenvalue, runtime, and stdv figures
    printCheck = input(pInput)
    if printCheck[0] == 'y':
        runN,runExt = getPrintName(printCheck)
        print("  "+saveFig(runDir+fpath+runN+"eig"+runExt,eigFig),end="")
        print("  "+saveFig(runDir+fpath+runN+"run"+runExt,runFig),end="")
        print("  "+saveFig(runDir+fpath+runN+"stdv"+runExt,stdvFig),end="")
    return ""
