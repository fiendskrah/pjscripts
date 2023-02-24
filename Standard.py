# Adds a standardized version of the input field
# to the input feature attribute table
# standardization scale [0.0, 1.0]
# AUTHOR: Arika Ligmann-Zielinska
# LAST UPDATED: July 21 2011
#--- IMPORTS ----------------------------------------------------------
import sys, arcpy
#------------- INPUTS -------------------------------------------------

inFC = sys.argv[1]
infield = sys.argv[2]
outfield = sys.argv[3]  # output field name
benefit = sys.argv[4]   # treat as benefit or cost?
method = sys.argv[5]    # standardization method

#------------- APPLICATION --------------------------------------------
try:
    # [1] Check input field - must be "numeric"
    fields = arcpy.ListFields(inFC, infield)
    for fld in fields:
        if fld.type not in ["SmallInteger","Integer","Single","Double"]:
            arcpy.AddError(infield+" is not numeric.")
            sys.exit(1)
    # [2] add field
    arcpy.AddField_management(inFC, outfield, "FLOAT", 6, 3)
    arcpy.AddMessage("Field "+outfield+" created.")
    # [3] Get a list of input field values to standardize
    rows = arcpy.SearchCursor(inFC)   
    fieldVals = []
    for row in rows:
        aval = row.getValue(infield)
        fieldVals.append(aval)
    del row; del rows
    # Get min & max
    minVal = min(fieldVals)
    maxVal = max(fieldVals)
    # [4] standardize
    if benefit == "BENEFIT":
        if method == "RATIO (LINEAR SCALE)":
            rows = arcpy.UpdateCursor(inFC)
            for row in rows:
                sval = float(row.getValue(infield))/maxVal
                row.setValue(outfield,sval)
                rows.updateRow(row)
            del row; del rows
        else: # 'SCORE RANGE' selected
            arange = float(maxVal - minVal)
            rows = arcpy.UpdateCursor(inFC)
            for row in rows:
                sval = float(row.getValue(infield)) - minVal
                sval = sval/arange
                row.setValue(outfield,sval)
                rows.updateRow(row)                
            del row; del rows
    else: # 'COST'
        if method == "RATIO (LINEAR SCALE)":
            rows = arcpy.UpdateCursor(inFC)
            for row in rows:
                sval = minVal/float(row.getValue(infield))
                row.setValue(outfield,sval)
                rows.updateRow(row) 
            del row; del rows
        else: # 'SCORE RANGE' selected
            arange = float(maxVal - minVal)
            rows = arcpy.UpdateCursor(inFC)
            for row in rows:
                sval = maxVal - float(row.getValue(infield))
                sval = sval/arange
                row.setValue(outfield,sval)
                rows.updateRow(row)
            del row; del rows
    # display the information
    info = infield+ " of "+inFC+" standardized to "+outfield
    arcpy.AddMessage(info)
except:
    arcpy.AddError("Script run error: "+arcpy.GetMessages(2))
