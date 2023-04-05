# Estimations of first order, total order effects
# First order and total order indices are estimated according to the rule proposed in 
# Saltelli, A., P. Annoni, I. Azzini, F. Campolongo, M. Ratto, S. Tarantola, (2010)
#   Variance based sensitivity analysis of model output.
#   Design and estimator for the total sensitivity index", Computer Physics Communications, 181, 259–270
# Total cost = N(k+2)
# BASED ON: http://sensitivity-analysis.jrc.ec.europa.eu/software/first_total_seq.rar
# Author: Stefano Tarantola
# Joint Research Centre of the European Commission
# Last release: 27 September, 2010
#
# Adopted by Arika Ligmann-Zielinska, Michigan state University, Last Updated: Jul 22, 2010
#
# Function WEIGHTED SUMMATION, weights as factors, criteria as constants

import numpy, random, copy, arcpy, sys
#------------- INPUTS -------------------------------------------------

inFC = sys.argv[1]
fields = sys.argv[2]
minweights = sys.argv[3]
maxweights = sys.argv[4]
simnum = sys.argv[5]
bestID = sys.argv[6]
outfileUA = sys.argv[7]
outfile_S_ST = sys.argv[8]

# ----- function definitions -------------------------------------------


def loadStandardizedDecisionMatrix(fields,inFC):
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

def checkWeights(mins,maxes,fields): 
    """ checks if the number of weights equals the number of criteria
        checks if min_weight <= max_weight
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
        
def first_total_asr(minweights,maxweights,dtable,N):
    """
        in: minimum for weight ranges (list),  maximum for weight ranges (list),
            decision matrix (list of lists), N number of base samples (int)
        out: (ASR,S,ST) where
                    ASR average shift in ranks
                    S is a  list of first order indices for ASR
                    ST is a list of total indices for ASR
    """
    y4var = []
    asrUA = [] # ASR scores for uncertainty analysis (should be drawn from sample A - S.Tarantola personal communication)
    k = len(minweights) # number of factors to evaluate in SA
    Vi = numpy.empty((N,k),float)
    VT = numpy.empty((N,k),float)
    S = numpy.empty((k),float)
    ST = numpy.empty((k),float)
    equalranks = getEqualWeight(dtable)
    arcpy.AddMessage("Calculating for Average Shift in Ranks...")
    for i in range(N):
        # [1] GENERATING samples with plain Monte Carlo
        A = [] # independent sample vector A
        B = [] # independent sample vector B
        for j in range(k):
            valA = random.uniform(minweights[j],maxweights[j])
            valB = random.uniform(minweights[j],maxweights[j])
            A.append(valA)
            B.append(valB)
        # radial sample matrix X(k+2,k) - "the block sample"
        # e.g. table 3 p. 262 in the paper above
        X = [A,B]
        for j in range(k):
            Ab = copy.deepcopy(A)
            Ab[j] = B[j]
            X.append(Ab)        
        # [2] Monte Carlo calculations for Average Shift in Ranks of WEIGHTED SUMMATION
        # ****** sample A
        scoresA = []
        for altrow in dtable:
            score = 0 
            for j in range(k):
                score += A[j]*altrow[j]
            scoresA.append(score)
        ranksA = getRank(scoresA)
        yA = getAverageShiftRanks(equalranks, ranksA)
        asrUA.append(yA)
        # ****** sample B
        scoresB = []
        for altrow in dtable:
            score = 0 
            for j in range(k):
                score += B[j]*altrow[j]
            scoresB.append(score)
        ranksB = getRank(scoresB)
        yB = getAverageShiftRanks(equalranks, ranksB)
        # ****** radial samples Ab
        yAb = []
        for sample in X[2:]:
            scoresAb = []
            for altrow in dtable:
                score = 0
                for j in range(k):
                    score += sample[j]*altrow[j]
                scoresAb.append(score)
            ranksAb = getRank(scoresAb)
            yAb.append(getAverageShiftRanks(equalranks, ranksAb))
        # [3] VARIANCE calculations
        # vector for calculation of total variance
        y4var.append(yA); y4var.append(yB) 
        # compute nominators for first and totals
        for j in range(k):
            Vi[i,j] = yB*(yAb[j]-yA)
            VT[i,j] =(yA-yAb[j])**2
        # calculation of total variance
        ay4var = numpy.array(y4var)
        Vtot = ay4var.var()
    # calculation of SENSITIVITY INDICES   
    for j in range(k):
        S[j] =numpy.mean(Vi[:,j])/Vtot
        ST[j]=numpy.mean(VT[:,j])/2/Vtot        
    return (asrUA,(S,ST))

def first_total_best(minweights,maxweights,dtable,N,bestIndex):
    """
        in: minimum for weight ranges (list),  maximum for weight ranges (list),
            decision matrix (list of lists), N number of base samples (int)
        out: (RankSeq,S,ST) where
                    RankSeq is a list of rank of best option in each simulation run
                    S is a list of first order indices for ASR
                    ST is a list of total indices for ASR
    """
    y4var = []
    bestSeqUA = [] # ranks of the winner for uncertainty analysis (should be drawn from sample A - S.Tarantola personal communication)
    k = len(minweights) # number of factors to evaluate in SA
    Vi = numpy.empty((N,k),float)
    VT = numpy.empty((N,k),float)
    S = numpy.empty((k),float)
    ST = numpy.empty((k),float)
    arcpy.AddMessage("Calculating for Selected Option (Winner)...")
    for i in range(N):
        # [1] GENERATING samples with plain Monte Carlo
        A = [] # independent sample vector A
        B = [] # independent sample vector B
        for j in range(k):
            valA = random.uniform(minweights[j],maxweights[j])
            valB = random.uniform(minweights[j],maxweights[j])
            A.append(valA)
            B.append(valB)
        # radial sample matrix X(k+2,k) - "the block sample"
        # e.g. table 3 p. 262 in the paper above
        X = [A,B]
        for j in range(k):
            Ab = copy.deepcopy(A)
            Ab[j] = B[j]
            X.append(Ab)        
        # [2] Monte Carlo calculations for Winner Ranks of WEIGHTED SUMMATION
        # ****** sample A
        scoresA = []
        for altrow in dtable:
            score = 0 
            for j in range(k):
                score += A[j]*altrow[j]
            scoresA.append(score)
        ranksA = getRank(scoresA)
        yA = ranksA[bestIndex]
        bestSeqUA.append(yA)
        # ****** sample B
        scoresB = []
        for altrow in dtable:
            score = 0 
            for j in range(k):
                score += B[j]*altrow[j]
            scoresB.append(score)
        ranksB = getRank(scoresB)
        yB = ranksB[bestIndex]
        # ****** radial samples Ab
        yAb = []
        for sample in X[2:]:
            scoresAb = []
            for altrow in dtable:
                score = 0
                for j in range(k):
                    score += sample[j]*altrow[j]
                scoresAb.append(score)
            ranksAb = getRank(scoresAb)
            yAb.append(ranksAb[bestIndex])
        # [3] VARIANCE calculations
        # vector for calculation of total variance
        y4var.append(yA); y4var.append(yB) 
        # compute nominators for first and totals
        for j in range(k):
            Vi[i,j] = yB*(yAb[j]-yA)
            VT[i,j] =(yA-yAb[j])**2
        # calculation of total variance
        ay4var = numpy.array(y4var)
        Vtot = ay4var.var()
    # calculation of SENSITIVITY INDICES   
    for j in range(k):
        S[j] =numpy.mean(Vi[:,j])/Vtot
        ST[j]=numpy.mean(VT[:,j])/2/Vtot      
    return (bestSeqUA,(S,ST))

def getEqualWeight(dtable):
    """ returns a list of ranks for the equal weight case """
    k = len(dtable[0])
    scores_for_equals = []
    for altrow in dtable:
        score = sum(altrow)/float(k)
        scores_for_equals.append(score)
    # ranks
    ranks_for_equal = getRank(scores_for_equals)
    return ranks_for_equal
    
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

#-- MAIN -------------------------------------------------------------
table = loadStandardizedDecisionMatrix(fields, inFC)
checkWeights(minweights,maxweights,fields)

# Global Sensitivity Analysis - ASR
mins = map(float,minweights.strip().split())
maxes = map(float,maxweights.strip().split())
N = int(simnum)

GSA = first_total_asr(mins,maxes,table,N)

GSAB = None
# Global Sensitivity Analysis - Winner
if int(bestID)> -1: # we perform this GSA only if 0 or higher 
    mins = map(float,minweights.strip().split())
    maxes = map(float,maxweights.strip().split())
    N = int(simnum)
    best = int(bestID)-1 # Note: ObjectID in a feature class starts from 1
    GSAB = first_total_best(mins,maxes,table,N,best)

# RESULTS
arcpy.AddMessage("Simulation Completed\n\n"+"-------------------------")
field_names = fields.strip().split(";")
result = "GSA: Average Shift in Ranks\nFactor\tS\tST\n"
for j in range(len(field_names)):
    row = field_names[j]+"\t"+str(round(GSA[1][0][j],3))+\
          "\t"+str(round(GSA[1][1][j],3))+"\n"
    result += row
result += "\n\nFactor\t%S\t%ST\n"
Ssum = sum(GSA[1][0])
STsum = sum(GSA[1][1])
for j in range(len(field_names)):
    row = field_names[j]+"\t"+str(round(GSA[1][0][j]*100,1))+\
          "\t"+str(round((GSA[1][1][j]/STsum)*100,1))+"\n"
    result += row
result += "NONL\t"+str(round((1-Ssum)*100,1))+"\n\n\n"

if int(bestID) > -1:
    result += "GSA: Best Option\nFactor\tS\tST\n"
    for j in range(len(field_names)):
        row = field_names[j]+"\t"+str(round(GSAB[1][0][j],3))+\
              "\t"+str(round(GSAB[1][1][j],3))+"\n"
        result += row
    result += "\n\nFactor\t%S\t%ST\n"
    Ssum = sum(GSAB[1][0])
    STsum = sum(GSAB[1][1])
    for j in range(len(field_names)):
        row = field_names[j]+"\t"+str(round(GSAB[1][0][j]*100,1))+\
              "\t"+str(round((GSAB[1][1][j]/STsum)*100,1))+"\n"
        result += row
    result += "NONL\t"+str(round((1-Ssum)*100,1))+"\n\n\n"
arcpy.AddMessage(result)

# save results
f = open(outfileUA, 'w')
uadata = [round(i,2) for i in GSA[0]]
uadata = map(str,uadata)
uadata = "Average Shift in Rank\n"+" ".join(uadata)+"\n"

if int(bestID) > -1:
    uadataB = [int(i) for i in GSAB[0]]
    uadataB = map(str,uadataB)
    uadataB = "\nWinner Rank Robustness\n"+" ".join(uadataB)+"\n"
    uadata += uadataB
f.write(uadata)
f.close()
arcpy.AddMessage(outfileUA+" saved")
f= open(outfile_S_ST, 'w')
f.write(result)
f.close()
arcpy.AddMessage(outfile_S_ST+" saved")
