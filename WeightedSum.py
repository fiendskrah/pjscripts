# Using the WEIGHTED SUMMATION decision rule, calculates option
# composite score for user-selected criteria (fields)
# in the input feature class
#
# CRITERIA must be within the 0.0 - 1.0 range, otherwise an error is raised
#
# WEIGHTS should be given as a space-delimited string
# e.g. "0.5 0.3 0.2" for 3 input criteria
# if weights do not add up to 1.0, they will be readjusted
# if too few/many weights are provided, an error occurs
#
# OUTPUT is saved in two new fields appended to the input feature class:
# Score_ID, and Rank_ID
#
# AUTHOR: Arika Ligmann-Zielinska
# LAST UPDATED: July 22 2011
#------------- IMPORTS ------------------------------------------------
import sys,arcpy,numpy,copy
#------------- INPUTS -------------------------------------------------

inFC = sys.argv[1]
fields = sys.argv[2]
weights = sys.argv[3]
scoreFieldName = sys.argv[4]
rankFieldName = sys.argv[5]

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


#-- EXECUTE -------------------------------------------------------------
table = loadStandardizedDecisionMatrix(fields)

# canculate scores and ranks
scores = weightedSum(table, weights)
ranks = getRank(scores)

# add new fields to the input feature class
arcpy.AddField_management(inFC,scoreFieldName,"DOUBLE",10,7)
arcpy.AddField_management(inFC,rankFieldName,"LONG",10)
# populate the fields
rows = arcpy.UpdateCursor(inFC)
i = 0
for row in rows:
    row.setValue(scoreFieldName,scores[i])
    row.setValue(rankFieldName,ranks[i])
    rows.updateRow(row)
    i += 1
del row, rows
arcpy.AddMessage(scoreFieldName+" and "+rankFieldName+" successfully added to "+inFC)    

