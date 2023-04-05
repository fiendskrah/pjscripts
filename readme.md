# Take home 4

Creating a python toolbox (.pyt) for use in ArcGis Pro:

Multi-criterion decision analysis with sensitivity analysis. Based on an assignment in Piotr Jankowski's GEOG 594 course at San Diego State University. Specific tools each have an issue ticket in the github repository. 

#### ESRI pages

These contain the list of possible options in defining parameters in .pyt

[Defining parameters](https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/defining-parameters-in-a-python-toolbox.htm)

[Parameter data types](https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm)


# Tracking Files
## Post-standardization
The student should begin the exercise at part-3 in the hand out PDF. This is after the raw site data has been standardized
This file is called `pjscript_update_student_start.aprx`

## Toolbox
The python toolbox (.pyt) is located in `toolbox/take_home_4.pyt`

# Steps
## Step 1: Standardize Field
Using the Weighted sum step below failed due to the features not being standardized. Therefore, we standardize the raw data first

### Inputs required
- Input features (raw data file)
- Field to be standardized (rbuildens)
- output field name (buildens)
- value (binary; cost or benefit)
- standardization method (binary; ratio (linear scale) or score range)

### Assignment context
See the take home 4 handout for a screenshot of the batch mode inputs
Once we standardize, we save the data as a new layer (sites_data.lyr), reimport and delete the raw fields

## Step 2: weighted sum for feature class
This tool creates weights for feature classes.  

### inputs required
- select the feature classes that are open 
- input the weights of each class selected as strings (space delimited)
- 'score output field'
- 'rank output field'

### Assignment context
- This creates the 'baseline' scenario for our analysis against which we do sensitivity analysis
