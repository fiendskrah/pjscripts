#------------- SPECIFICATION -----------------------------------------
# Assigns a value of input raster to input feature class (FC)
# The assigned value is the value at the centroid of input FC
# AUTHOR: Arika Ligmann-Zielinska
# LAST UPDATED: July 22 2011
#------------- IMPORTS ------------------------------------------------
import sys, arcpy, os.path, string, os, random
#------------- INPUTS -------------------------------------------------

inVector = sys.argv[1]
raster = sys.argv[2]
rasterField = 'VALUE' #sys.argv[3]
outVector = sys.argv[3]
outFieldName = sys.argv[4]  # default 'grid_code'

#------------- APPLICATION --------------------------------------------
try:
    # Check input vector
    dscfc = arcpy.Describe(inVector)
    if not (dscfc.shapeType == "Polygon" or dscfc.ShapeType == "Point"):
        arcpy.AddError("Input feature class must be POINT or POLYGON")
        sys.exit(1)
    # Set the Workspace
    workspace = os.path.dirname(outVector)
    # Convert input raster to polygon FC
    myid = str(random.randint(1,100))
    poly = workspace+"\poly"+myid
    arcpy.RasterToPolygon_conversion(raster,poly,"NO_SIMPLIFY",rasterField)
    # Get input vector centroids
    features = arcpy.SearchCursor(inVector)
    XYdata = "centroidX,centroidY\n"
    shapefieldname = arcpy.Describe(inVector).ShapeFieldName
    for feature in features:
        fgeom = feature.getValue(shapefieldname)
        centroid = fgeom.trueCentroid
        XY = str(centroid.X)+","+str(centroid.Y)
        XYdata = XYdata+XY+"\n"
    del feature, features
    # Save the data to file (flat file table of XY coordinates)
    XYfile = workspace+"\\XYtable.txt"
    f = open(XYfile,'w')
    f.write(XYdata)
    f.close()
    # Convert centroid data to point feature class
    layer = "layer"
    arcpy.MakeXYEventLayer_management(XYfile,"centroidX","centroidY",layer)
    centroidFC = "centr"+myid
    arcpy.FeatureClassToFeatureClass_conversion(layer,workspace,centroidFC)
    # Intersect raster poly & centroid
    intersectFeatures = [workspace+"\\"+centroidFC,poly]
    rasterAndCentroid = workspace+"\\rasterCentroid"+myid
    arcpy.Intersect_analysis(intersectFeatures, rasterAndCentroid)
    # delete 2 FID_ fields from rasterAndCentroid
    arcpy.DeleteField_management(rasterAndCentroid,"FID_centro")
    arcpy.DeleteField_management(rasterAndCentroid,"FID_temppo")
    # Spatially Join rasterAndCentroid & input vector feature class
    #   -> Map grid_code to out Raster Field Name
    fieldmappings = arcpy.CreateObject("FieldMappings")
    fieldmappings.addTable(inVector)
    fieldmappings.addTable(rasterAndCentroid)
    fieldmap = fieldmappings.getFieldMap(fieldmappings.findFieldMapIndex("grid_code"))
    field = fieldmap.outputField
    field.name = outFieldName
    field.aliasName = outFieldName
    fieldmap.outputField = field
    fieldmappings.replaceFieldMap(fieldmappings.findFieldMapIndex("grid_code"), fieldmap)
    #   -> Run the Spatial Join tool
    arcpy.SpatialJoin_analysis(inVector,rasterAndCentroid,outVector,"#","#",fieldmappings)
    arcpy.AddMessage(outVector+" created")
    # Delete temp datasets & fields
    arcpy.DeleteField_management(outVector,"Join_Count")
    arcpy.DeleteField_management(outVector,"centroidX")
    arcpy.DeleteField_management(outVector,"centroidY")
    arcpy.DeleteField_management(outVector,"FID_"+centroidFC)
    arcpy.DeleteField_management(outVector,"FID_"+poly)
    arcpy.Delete_management(workspace+"\\"+centroidFC)
    arcpy.Delete_management(rasterAndCentroid)
    arcpy.Delete_management(poly)
    os.remove(XYfile)
except:
    arcpy.AddError("Script run error: "+arcpy.GetMessages(2))
