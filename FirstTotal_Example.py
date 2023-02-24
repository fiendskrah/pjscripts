# Estimations of first order, total order effects
# First order and total order indices are estimated according to the rule proposed in 
# Saltelli, A., P. Annoni, I. Azzini, F. Campolongo, M. Ratto, S. Tarantola, (2010)
#   Variance based sensitivity analysis of model output.
#   Design and estimator for the total sensitivity index", Computer Physics Communications, 181, 259�270
# Total cost = N(k+2)

# BASED ON: http://sensitivity-analysis.jrc.ec.europa.eu/software/first_total_seq.rar
# Author: Stefano Tarantola
# Joint Research Centre of the European Commission
# Last release: 27 September, 2010

# Adopted by Arika Ligmann-Zielinska, Michigan state University, Last Updated: Jul 22, 2010

import arcpy
import numpy
import random
import copy

Class Toolbox(object):
def __init__(self):
    self.label = "First Total Estimates"
    self.alias = "firsttotal"
    self.tools = [first_total_seq]

    def first_total_seq(k,N):
        """
            in: k number of factors, N number of base samples
            out: (S,ST) where
                        S is a list of first order indices
                        ST is a list of total indices
        """
        y4var = []
        Vi = numpy.empty((N,k),float)
        VT = numpy.empty((N,k),float)
        S = numpy.empty((k),float)
        ST = numpy.empty((k),float)
        for i in range(N):

            # EXAMPLE FUNCTION
            # Y_portf = Cs*Ps + Ct*Pt + Cj*Pj (source: "Sensitivity Analysis in Practice"
            # Saltelli et al. 2004, Wiley, p.1 (eq.1.1), results: p.21 (table 1.6)
            # Ps ~N(0,4)        Pt ~N(0,2)      Pj ~N(0,1)
            # Cs ~N(250,200)    Ct ~N(400,300)  Cj ~N(500,400)
            #
            # generate samples with plain Monte Carlo
            ps1 = random.gauss(0,4); ps2 = random.gauss(0,4) 
            pt1 = random.gauss(0,2); pt2 = random.gauss(0,2)
            pj1 = random.gauss(0,1); pj2 = random.gauss(0,1)
            cs1 = random.gauss(250,200); cs2 = random.gauss(250,200)
            ct1 = random.gauss(400,300); ct2 = random.gauss(400,300)
            cj1 = random.gauss(500,400); cj2 = random.gauss(500,400)

            # sample vectors
            A = [cs1,ps1,ct1,pt1,cj1,pj1]
            B = [cs2,ps2,ct2,pt2,cj2,pj2]

            # radial sample matrix X(k+2,k) - "the block sample"
            # e.g. table 3 p. 262 in the paper above
            X = [A,B]
            for j in range(k):
                Ab = copy.deepcopy(A)
                Ab[j] = B[j]
                X.append(Ab)

            # Calculations for the sample function
            yA = A[0]*A[1] + A[2]*A[3] + A[4]*A[5]
            yB = B[0]*B[1] + B[2]*B[3] + B[4]*B[5]
            yAb = []
            for v in X[2:]:
                yAb.append(v[0]*v[1] + v[2]*v[3] + v[4]*v[5])

            # vector for calculation of total variance
            y4var.append(yA); y4var.append(yB) 

            # compute nominators for first and totals
            for j in range(k):
                Vi[i,j] = yB*(yAb[j]-yA)
                VT[i,j] =(yA-yAb[j])**2

            # calculation of total variance
            ay4var = numpy.array(y4var)
            Vtot = ay4var.var()

        # calculation of sensitivity indices   
        for j in range(k):
            S[j] =numpy.mean(Vi[:,j])/Vtot
            ST[j]=numpy.mean(VT[:,j])/2/Vtot        
        return (S,ST)


if __name__ == "__main__":
    N = 2500 # input
    #---------------
    print "ORIGINAL"
    print "\tcs\tps\tct\tpt\tcj\tpj"
    print "S\t","\t".join(["0.0","0.36","0.0","0.22","0.0","0.08","sum: 0.66"])
    print "ST\t","\t".join(["0.19","0.57","0.12","0.35","0.06","0.14","sum: 1.43"])

    result = first_total_seq(6,N)
    
    print "\nN =",N
    print "\tcs\tps\tct\tpt\tcj\tpj"
    Si = [str(round(i,2)) for i in result[0] ]
    STi = [str(round(i,2)) for i in result[1] ]
    
    print "S\t","\t".join(Si),"\tsum:",sum([float(i) for i in Si])
    print "ST\t","\t".join(STi),"\tsum:",sum([float(i) for i in STi])
