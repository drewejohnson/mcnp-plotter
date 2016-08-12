#------------------------------------------------------------------------------
#
#               MCNP OUTPUT PROCESSING TOOLS
#
#   This code will
#       - read in an mcnp output file
#       - store various tally data
#       - save the cell data to a separate file
#
#   Cell Data supported:
#       - F4 tally data for each cell
#           - will be working to improve/expand upon this feature in future
#       - cell location if location.txt file is included in same directory
#
#               Author: Andrew Johnson
#-------------------------------------------------------------------------------

#--------
# Imports
#--------
import re
import csv
#----------
# Constants
#----------
reCellFlux = r'( *tally type 4 * track length estimate of particle flux\. *units *1/cm\*\*2)'
reCellMat = r'( *cell *mat * *density)'
reEOB = r' ([\*=]+)'     # end of data block will have either * or = as the first characters
reKCODE = r'.+[kcode]{5}|[KCODE]{5} (\d+) '         # match kcode line and store nps/cycle
reFinalR = r'.+final result +([\d\.]+) +([\d\.]+)'  # match final eigenvalue result and stdv
reRunT = r' +computer time = +(\d+\.\d{2})'            # match run time
#--------
# Classes
#--------
class Cell:
    cells = {}      # holds all the cells and their classes
# Each instance of Cell will be given the following attributes:
#       - cell number   (num)
#       - cell tally    (flux)  - currently only track length estimate of flux
#       - standard deviation on cell tally   (fluxsd)
#       - location of center of cell
    def __init__(self,num):
        self.num = num
        Cell.cells[num] = self
#----------
# Functions
#----------
    def valStr(self):
        s = "Cell number: {0:3d}\n".format(self.num)
        try:
            s += "  Center of cell: ({0:11.5E},{1:11.5E},{2:11.5E})\n".format(self.loc[0],self.loc[1],self.loc[2])
        except AttributeError:
            print("  Cell {0:3d} does not have attribute loc".format(self.num))
        try:
            s += "  Cell Flux: {0:11.5E} +/- {1:6.4f}\n".format(self.flux,self.fluxsd)
        except AttributeError:
            print("  Cell {0:3d} does not have attribute flux".format(self.num))
        try:
            s += "  Material : {0:<4d}\n".format(self.mat)
        except AttributeError:
            print("  Cell {0:3d} does not have attribute mat".format(self.num))
        return s


    def writeCells(outObj):
        """Write all cell data to output file referenced by outObj"""
        for n in sorted(list(Cell.cells.keys())):
            c = Cell.cells[n]
            outObj.write(c.valStr())

    def writeCSV(outObj):
        sci = "{0:11.5E}"
        """Write the cell number, material, x,y,z center, flux, and standard deviation in csv form"""
        cw = csv.writer(outObj)
        cw.writerow("Cell Number,X,Y,Z,Cell Flux,Standard Deviation".split(","))
        for n,c in Cell.cells.items():
            try:
                x = sci.format(c.loc[0])
                y = sci.format(c.loc[1])
                z = sci.format(c.loc[2])
                lCheck = 1
            except AttributeError:
                lCheck = 0
                print("  Cell {0:3d} does not have location data".format(n))
            try:
                f = sci.format(c.flux)
                fsd = sci.format(c.fluxsd)
                fCheck = 1
            except AttributeError:
                fCheck = 0
                print("  Cell {0:3d} does not have flux data".format(n))
            if fCheck and lCheck:       # both location and flux data is present for cell n
                cw.writerow([n,x,y,z,f,fsd])
            else:
                print("  Did not write cell {0} due to missing data".format(n))


def getBlock(dataList,indx):
    cellBlock = []
    while indx < len(dataList):
        line = dataList[indx]
        if len(line)>0:
            if re.match(reEOB,line) != None:        # end of tally block
                break
            else:
                cellBlock.append(line.strip().split())
                indx += 1
    # do some cleaning on the data by removing empty lines and
    i = 0
    while i < len(cellBlock):
        if cellBlock[i] == []:
            del cellBlock[i]
        else:
            i += 1
    return cellBlock

def getCellTally(data):
    """data: list of lists for the flux tally data block"""
    i = 0
    while i < len(data):
        if data[i][0] == 'cell:':
            c = 1
            while c < len(data[i]):
                thisCell = Cell(int(data[i][c]))
                thisCell.vol = float(data[i+1][c-1])
                c += 1
        elif data[i][0] == 'cell':
            n = int(data[i][1])
            Cell.cells[n].flux = float(data[i+1][0])
            Cell.cells[n].fluxsd = float(data[i+1][1])
        i += 1

def getCellMat(data):
    """data: list of lists for cell material data block"""
    i = 0
    while i < len(data):
        try:
            int(data[i][0])
        except ValueError:
            break
        cellnum = int(data[i][1])
        if cellnum not in Cell.cells and int(data[i][2]) != 0:
            Cell(cellnum)       # create an instance of the class
        if int(data[i][2]) != 0:
            Cell.cells[cellnum].mat = int(data[i][2])
        i += 1

def getCellLoc(runDir,mpath):
    """If "locations.txt" is in the current directory, the cell locations will be added to each object"""
    try:
        lFile = open(runDir+"locations.txt",'r')
    except IOError:
        try:
            lFile = open(runDir+mpath+"locations.txt","r")
        except IOError:
            return -1

    lines = lFile.readlines()
    lFile.close()
    i = 0
    miss = 0
    while i in range(0,len(lines)):
        line = lines[i].split()
        if len(line) < 4:
            miss += 1
        else:
# data is formatted as: cell #, x,y,z
            line[0] = int(line[0])
            line[1] = float(line[1])
            line[2] = float(line[2])
            line[3] = float(line[3])
            if line[0] in Cell.cells:
                Cell.cells[line[0]].loc = (line[1],line[2],line[3])
        i += 1
    return miss
#-----------------
# Main Code
#----------------
def main(infile,runDir,cpath,mpath):
    mcnpopath = runDir + mpath
    csvpath = runDir + cpath

    try:
        f = open(mcnpopath+infile,'r')
    except IOError:
        return 0,""

    eigM = None
    runM = None
    npsM = None
    stdv = None
    tallydata = None
    # if one of these is still none at the end, that means the output is
    #   missing something and don't add run to summary.csv
    print("Processing: "+infile)
    lines = f.readlines()
    l = 0
    for line in lines:
        if re.match(reCellFlux,line) != None:
            tallydata = getBlock(lines,l)
            getCellTally(tallydata)
        elif re.match(reCellMat,line) != None:
            matData = getBlock(lines,l)
            getCellMat(matData)
        elif re.findall(reRunT,line) != []:
            runM = re.findall(reRunT,line)[0]
        elif re.findall(reKCODE,line) != [] and npsM == None:
            npsM = re.findall(reKCODE,line)[0]
        elif re.findall(reFinalR,line) != []:
            eigM = re.findall(reFinalR,line)[0][0]
            stdv = re.findall(reFinalR,line)[0][1]
        l += 1
    f.close()
    if tallydata == None:       # could not find tally data in file
        return -1,""
    lStat = getCellLoc(runDir,mpath)
    if lStat == -1:
        print("  No location file found in {0} or {0}{1}".format(runDir,mpath))
    else:
        if lStat > 0:
            print("  Obtained location data with {0} cells missing location data".format(lStat))
    #----------------
    # Write Flux Data
    #----------------
    ofile = csvpath+infile+".csv"
    outObj = open(ofile,'w',newline="")
    Cell.writeCSV(outObj)       # write the data in csv form
    outObj.close()
    return 1,[npsM,eigM,stdv,runM]
