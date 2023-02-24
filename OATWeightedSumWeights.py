# Using the WEIGHTED SUMMATION decision rule, calculates option
# composite scores for user-selected criteria (fields)
# in the input feature class for two input weight vectors
# then compares the changes in ranks
#
# CRITERIA must be within the 0.0 - 1.0 range, otherwise an error is raised
#
# WEIGHTS should be given as a space-delimited string
# e.g. "0.5 0.3 0.2" for 3 input criteria
# if weights do not add up to 1.0, they will be readjusted
# if too few/many weights are provided, an error occurs
#
# OUTPUT contains new appended fields:
# SCORE1,RANK1,SCORE2,RANK2,RANK_CHANGE
# Additionally, an average shift in ranks stats is displayed in the output window
#
# AUTHOR: Arika Ligmann-Zielinska
# LAST UPDATED: July 22 2011
#------------- IMPORTS ------------------------------------------------
import sys,arcpy,numpy,copy
#------------- INPUTS -------------------------------------------------

inFC = sys.argv[1]
fields = sys.argv[2]
baseweights = sys.argv[3]
refweights = sys.argv[4]

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


def weightedSum(matrix, weights):
    """ returns a list of scores """
    scores = []
    weights = map(float,weights.strip().split())
    matrixlist = matrix.tolist()
    if len(weights) != len(matrixlist[0]):
        arcpy.AddError("the number of weights does not match the number of criteria")
        sys.exit(1)
    if sum(weights) != 1.0:
        arcpy.AddWarning("weights do not add up to 1.0; recalculating...")
        total = float(sum(weights))
        weight_copy = copy.deepcopy(weights)
        for i,w in enumerate(weight_copy):
            w = w/total
            weights[i] = w
        arcpy.AddWarning("Old weights: "+",".join(map(str,weight_copy))+
                         "  New weights: "+",".join(map(str,weights)))
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

def getAverageShiftRanks(baseranks, refranks):
    """ returns the average shift in ranks between the base scenario and the reference scenario """
    n = len(baseranks) # number of options
    basearray = numpy.array(baseranks)
    refarray = numpy.array(refranks)
    abs_shift = numpy.abs(basearray-refarray)
    ASR = float(abs_shift.sum())/n
    return ASR

#-- EXECUTE -------------------------------------------------------------
table = loadStandardizedDecisionMatrix(fields)

# calculate scores and ranks - BASE
basescores = weightedSum(table, baseweights)
baseranks = getRank(basescores)

# calculate scores and ranks - REFERENCE
refscores = weightedSum(table, refweights)
refranks = getRank(refscores)

# calculate rank change
rank_change = numpy.array(baseranks)-numpy.array(refranks)
rank_change = rank_change.tolist()

# add new fields to the input feature class
arcpy.AddField_management(inFC,"SCORE1","DOUBLE",10,7)
arcpy.AddField_management(inFC,"SCORE2","DOUBLE",10,7)
arcpy.AddField_management(inFC,"RANK1","LONG",10)
arcpy.AddField_management(inFC,"RANK2","LONG",10)
arcpy.AddField_management(inFC,"RANK_CHANGE","LONG",10)
# populate the fields
rows = arcpy.UpdateCursor(inFC)
i = 0
for row in rows:
    row.setValue("SCORE1",basescores[i])
    row.setValue("SCORE2",refscores[i])
    row.setValue("RANK1",baseranks[i])
    row.setValue("RANK2",refranks[i])
    row.setValue("RANK_CHANGE",rank_change[i])
    rows.updateRow(row)
    i += 1
del row, rows
arcpy.AddMessage("OAT analysis of weights for "+inFC+" finished")
# Average Shift in Ranks
asr = getAverageShiftRanks(baseranks, refranks)
arcpy.AddMessage("\nThe Average Shift in Ranks ASR="+str(asr)+"\n")

