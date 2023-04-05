#------------- SPECIFICATION -----------------------------------------
# Pearson Correlation Coefficient for Two Attributes of Input Features
# AUTHOR: Arika Ligmann-Zielinska
# LAST UPDATED: July 22 2011
#------------- IMPORTS ------------------------------------------------
import sys, arcpy, os.path, math
#------------- INPUTS -------------------------------------------------

inFC = sys.argv[1]
field1 = sys.argv[2]
field2 = sys.argv[3]

#------------- APPLICATION --------------------------------------------
try:
    # Set the workspace
    arcpy.env.Workspace = os.path.dirname(inFC)
    # Check input fields - must be "numeric"
    fields = arcpy.ListFields(inFC, field1)
    for fld in fields:
        if fld.type not in ["SmallInteger","Integer","Single","Double"]:
            arcpy.AddError(field1+" is not numeric")
            sys.exit(1)
    del fields, fld
    fields = arcpy.ListFields(inFC, field2)
    for fld in fields:
        if fld.type not in ["SmallInteger","Integer","Single","Double"]:
            arcpy.AddError(field2+" is not numeric")
            sys.exit(1)
    # Calculate the means of the fields
    cur = arcpy.SearchCursor(inFC)   
    mean1 = 0
    mean2 = 0
    fcnum = 0
    for row in cur:        
        mean1 += row.getValue(field1)
        mean2 += row.getValue(field2)
        fcnum += 1
    del cur, row
    mean1 = float(mean1)/fcnum
    mean2 = float(mean2)/fcnum
    # Calculate sum of products of deviations (numerator of 'r')
    cur = arcpy.SearchCursor(inFC)
    sumpd = 0
    for row in cur:
        p1 = (row.getValue(field1)-mean1)
        p2 = (row.getValue(field2)-mean2)
        sumpd += p1*p2
    del row, cur
    # Calculate the product of standard deviations
    cur = arcpy.SearchCursor(inFC)
    std1 = 0
    std2 = 0
    for row in cur:
        std1 += pow(row.getValue(field1) - mean1, 2)
        std2 += pow(row.getValue(field2) - mean2, 2)
    del row, cur
    std1 = math.sqrt(std1/(fcnum - 1))
    std2 = math.sqrt(std2/(fcnum - 1))
    # Calculate denominator
    d = (fcnum - 1)*std1*std2
    # Correlation
    r = round(float(sumpd)/d,2)
    arcpy.AddMessage("Pearson correlation between "+field1+" and "+field2+" r = "+str(r))
    # Calculate the t-statistics
    if -1 < r < 1:
        t = r*math.sqrt(fcnum-2 /(1-r*r))
        arcpy.AddMessage("T-test score: "+str(t))
        # Check the significance if fcnum > 1001
        if fcnum > 1001:
            if abs(t) >= 2.3263:
                sig = "99%"
            elif abs(t) >= 1.6449:
                sig = "95%"
            else:
                sig = "not significant"
            arcpy.AddMessage("---> significance: "+sig+"\n")
        else:
            arcpy.AddMessage("Look t-score significance in a t-table\n")
except:
    arcpy.AddError("Script run error: f"+arcpy.GetMessages(2))
