# Monte Carlo Simulation for N model runs of option scoring and ranking
# Using the WEIGHTED SUMMATION decision rule and variable weights
#
# CRITERIA come from the input feature class
# criteria must be within the 0.0 - 1.0 range, otherwise an error is raised
# 
# WEIGHTS are randomly drawn from a uniform distribution
# with MIN and MAX given by the user, then rescaled so that they add-up to 1.0
# Weight vectors should be given as a space-delimited string
# e.g. "0.5 0.2 0.7" for 3 input criteria
# if too few/many weights are provided, an error occurs
#
# OUTPUT contains new appended fields:
# Average Score; Average Rank; Min Rank; Max Rank; StdDev of Ranks
#
# AUTHOR: Arika Ligmann-Zielinska
# LAST UPDATED: July 24 2011
#------------- IMPORTS ------------------------------------------------
import sys,arcpy,numpy,random
#------------- INPUTS -------------------------------------------------

inFC = sys.argv[1]
fields = sys.argv[2]
minweights = sys.argv[3]
maxweights = sys.argv[4]
simnum = sys.argv[5]
scoreavg = sys.argv[6]
rankavg = sys.argv[7]
rankmin = sys.argv[8]
rankmax = sys.argv[9]
rankstd = sys.argv[10]

# ----- function definitions -------------------------------------------

def loadStandardizedDecisionMatrix(fields):
    """ returns a decision matrix (numpy array) of
        floats in range [0.0, 1.0] """
    fields = fields.strip().split(";")
    matrix = []
    for field in fields:
        # put field values into a list
        attribute = []
        cur = arcpy.SearchCursor(inFC)
        for row in cur:
            val = row.getValue(field)
            attribute.append(val)
        del row, cur
        # check if values standardized
        minval = min(attribute)
        maxval = max(attribute)
        if not (minval >= 0 and maxval <= 1):
            arcpy.AddError(field+" is not standardized to [0.0,1.0] range")
            sys.exit(1)
        matrix.append(attribute)
    matrixArr = numpy.array(matrix)
    return numpy.transpose(matrixArr)

def drawWeights(mins,maxes,fields): 
    """ randomly draws weights from the input uniform distribution
        returns a list of weights
    """
    mins = map(float,mins.strip().split())
    maxes = map(float,maxes.strip().split())
    fieldnum = len(fields.strip().split(";"))
    if len(mins) != fieldnum:
        arcpy.AddError("the number of MIN weights does not match the number of criteria")
        sys.exit(1)
    if len(maxes) != fieldnum:
        arcpy.AddError("the number of MAX weights does not match the number of criteria")
        sys.exit(1)
    ranges = numpy.array(maxes) - numpy.array(mins)
    if numpy.any(ranges < 0):
        arcpy.AddError("MAX values for weights cannot be smaller than MIN values for weights")
        sys.exit(1)        
    # draw values
    raw_weights = []
    for i in range(fieldnum):
        val = random.uniform(mins[i],maxes[i])
        raw_weights.append(val)
    # rescale to [0,1]
    total = sum(raw_weights)
    weights = [float(w)/total for w in raw_weights]
    return weights
        

def weightedSum(matrix, weights):
    """ returns a list of scores """
    scores = []
    matrixlist = matrix.tolist()
    for row in matrixlist:
        i = 0
        score = 0.0
        for criteria in row:
            score = score + (criteria * weights[i])
            i = i + 1
        scores.append(score)
    return scores

def getRank(inscores):
    """ returns a list of ranks based on input scores """
    indx = range(len(inscores))
    scorespos = zip(inscores,indx)
    scorespos.sort()
    scorespos.reverse() # scores ordered from best to worst
    ranks = [-1]*len(inscores)
    for i,score in enumerate(scorespos):
        rank = i+1
        pos = score[1]
        ranks[pos] = rank
    return ranks

#-- EXECUTE -------------------------------------------------------------
table = loadStandardizedDecisionMatrix(fields)


# Monte Carlo
rows = int(str(arcpy.GetCount_management(inFC)))

sumscores = numpy.zeros(rows,dtype = float)
sumranks = numpy.zeros(rows,dtype = float)
minranks = numpy.ones(rows,dtype = long)*999999
maxranks = numpy.zeros(rows,dtype = long)

N = int(simnum)
stddata = []

for i in range(N):
    # generate weights
    thisweights = drawWeights(minweights,maxweights,fields)
    # calculate scores and ranks
    scores = numpy.array(weightedSum(table, thisweights))
    ranks = numpy.array(getRank(scores))

    # update data for summary stats
    sumscores = sumscores + scores
    sumranks = sumranks + ranks
    minranks = numpy.minimum(minranks,ranks)
    maxranks = numpy.maximum(maxranks,ranks)
    stddata.append(ranks)

    sofar = round((i/float(N))*100,1)
    if sofar%10 == 0:
        arcpy.AddMessage(str(sofar)+" % completed.")
   
# calculate summary stats
avgscores = sumscores/float(N)
avgranks = sumranks/float(N)
stdarray = numpy.array(stddata,dtype=float)
stdranks = numpy.std(stdarray,axis=0,dtype = numpy.float64)

avgscores = avgscores.tolist()
avgranks = avgranks.tolist()
avgranks = [round(i) for i in avgranks]

minranks = minranks.tolist()
maxranks = maxranks.tolist()
stdranks = stdranks.tolist()
stdranks = [round(i) for i in stdranks]


# add new fields to the input feature class
arcpy.AddField_management(inFC,scoreavg,"DOUBLE",10,7)
arcpy.AddField_management(inFC,rankavg,"LONG",10)
arcpy.AddField_management(inFC,rankmin,"LONG",10)
arcpy.AddField_management(inFC,rankmax,"LONG",10)
arcpy.AddField_management(inFC,rankstd,"LONG",10)

# populate the fields
rows = arcpy.UpdateCursor(inFC)
i = 0
for row in rows:
    row.setValue(scoreavg,avgscores[i])
    row.setValue(rankavg,avgranks[i])
    row.setValue(rankmin,minranks[i])
    row.setValue(rankmax,maxranks[i])
    row.setValue(rankstd,stdranks[i])
    rows.updateRow(row)
    i += 1
del row, rows
arcpy.AddMessage("Monte Carlo Uncertainty Analysis of weights for "+inFC+" finished\n\n")
