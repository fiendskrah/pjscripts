# -*- coding: utf-8 -*-

import arcpy

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "th4"
        self.alias = "th4"

        # List of tool classes associated with this toolbox
        self.tools = [StandardizeRatiosScore, WeightedSumScore, IdealPointScore, OATForWeights, OATForCriteria, MonteCarloWeightedSum]
    
        #  NEXT: VarianceDecomposition 

class StandardizeRatiosScore(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Standardize Ratios/Score"
        self.description = "Takes numerical data from a user-provided field in a data layer in the current ArcGIS Pro project, as well as a user-provided cost/benefit binary value, and returns the data as a standardized ratio or score."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        fields_to_standardize = arcpy.Parameter(
            displayName="Field with Numerical Data",
            name="fields_to_standardize",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            enabled=False,
            multiValue=True)
        fields_to_standardize.parameterDependencies = [input_table.name]

        standardization_method = arcpy.Parameter(
            displayName="Standardization Method",
            name="standardization_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        standardization_method.filter.type = "ValueList"
        standardization_method.filter.list = ['Score Range', 'Ratio (Linear Scale)']

        cost_benefit = arcpy.Parameter(
            displayName="Cost/Benefit",
            name="cost_benefit",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        cost_benefit.filter.type = "ValueList"
        cost_benefit.filter.list = ['Cost', 'Benefit']

        # define the derived output parameter
        outfield_name = arcpy.Parameter(
            displayName="Output Field Name",
            name="outfield_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            enabled=True)
        cost_benefit.filter.type = "Value"
        
        outfield = arcpy.Parameter(
            displayName="Output Field",
            name="outfield",
            datatype="Field",
            parameterType="Derived",
            direction="Output")



        parameters = [input_table, fields_to_standardize, standardization_method, cost_benefit, outfield, outfield_name]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            parameters[1].enabled = True

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_table = arcpy.GetParameterAsText(0)
        fields_to_standardize = arcpy.GetParameterAsText(1)
        

        # Get the minimum and maximum values of the user-provided field
        with arcpy.da.SearchCursor(input_table, [fields_to_standardize]) as cursor:
            max_value = None
            min_value = None
            for row in cursor:
                if max_value is None or row[0] > max_value:
                    max_value = row[0]
                if min_value is None or row[0] < min_value:
                    min_value = row[0]
        # create a dictionary to store the max and min values
        result_dict = {'maximum': max_value, 'minimum': min_value}

        outfield_name = parameters[5].valueAsText
        # Add the new field to the input layer
        arcpy.AddField_management(input_table, outfield_name, "DOUBLE") 

        # set parameters for standardization loop
        result_dict = eval(parameters[4].valueAsText)
        method = parameters[2].valueAsText
        benefit = parameters[3].valueAsText
        maxVal = result_dict['maximum']
        minVal = result_dict['minimum']
        outfield = parameters[5]
        
        # standardize the score of each row using the min and max values
        if benefit == "Benefit":
            if method == "Ratio (Linear Scale)":
                rows = arcpy.UpdateCursor(input_table)
                for row in rows:
                    sval = float(row.getValue(row))/maxVal
                    row.setValue(outfield,sval)
                    rows.updateRow(row)
                del row; del rows
            else: # 'Score Range' selected
                arange = float(maxVal - minVal)
                rows = arcpy.UpdateCursor(input_table)
                for row in rows:
                    sval = float(row.getValue(row)) - minVal
                    sval = sval/arange
                    row.setValue(outfield,sval)
                    rows.updateRow(row)                
                del row; del rows
        else: # 'Cost'
            if method == "Ratio (Linear Scale)":
                rows = arcpy.UpdateCursor(input_table)
                for row in rows:
                    sval = minVal/float(row.getValue(row))
                    row.setValue(outfield,sval)
                    rows.updateRow(row) 
                del row; del rows
            else: # 'Score Range' selected
                arange = float(maxVal - minVal)

class WeightedSumScore(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Weighted Sum Score"
        self.description = "Takes standardized data from a site attribute table and user-provided weights, performs a weighted-sum operation, and returns a score and a numerical ranking for each site."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        fields = arcpy.Parameter(
            displayName="Fields",
            name="fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True,
            enabled=False)
        fields.parameterDependencies = [input_table.name]

        weights = arcpy.Parameter(
            displayName="Weights",
            name="weights",
            datatype="Double",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        score_field_name = arcpy.Parameter(
            displayName="Score Field Name",
            name="score_field_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        rank_field_name = arcpy.Parameter(
            displayName="Rank Field Name",
            name="rank_field_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        parameters = [input_table, fields, weights, score_field_name, rank_field_name]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            parameters[1].enabled = True

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_table = parameters[0].valueAsText
        fields = parameters[1].valueAsText
        weights = parameters[2].values

        # Create a list to store the weighted sum score for each site
        weighted_sum_scores = []
        arcpy.AddMessage(f"Fields = {fields}")

        # Calculate the weighted sum score for each site
        with arcpy.da.SearchCursor(input_table, fields) as cursor:
            for row in cursor:
                weighted_sum_score = 0
                for i, value in enumerate(row):
                    weighted_sum_score += value * weights[i]
                    weighted_sum_scores.append(weighted_sum_score)

        # Sort the weighted sum scores and create a list of rankings
        rankings = [i+1 for i in sorted(range(len(weighted_sum_scores)), key=lambda x: weighted_sum_scores[x], reverse=True)]

        # Return the weighted sum scores and rankings
        return weighted_sum_scores, rankings

class IdealPointScore(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Ideal Point Score"
        self.description = "Takes standardized data from a site attribute table and user-provided weights, performs an ideal point operation, and returns a score and a numerical ranking for each site."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        fields = arcpy.Parameter(
            displayName="Fields",
            name="fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True,
            enabled=False)
        fields.parameterDependencies = [input_table.name]

        weights = arcpy.Parameter(
            displayName="Weights",
            name="weights",
            datatype="Double",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        score_field_name = arcpy.Parameter(
            displayName="Score Field Name",
            name="score_field_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        rank_field_name = arcpy.Parameter(
            displayName="Rank Field Name",
            name="rank_field_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        parameters = [input_table, fields, weights, score_field_name, rank_field_name]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            parameters[1].enabled = True

    def execute(self, parameters, messages):
        """The source code of the tool."""

class OATForWeights(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "OAT For Weights"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        fields = arcpy.Parameter(
            displayName="Fields",
            name="fields",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        fields.parameterDependencies = [input_table.name]

        base_weights = arcpy.Parameter(
            displayName="Base Weights",
            name="base_weights",
            datatype="Double",
            parameterType="Required",
            direction="Input")

        reference_weights = arcpy.Parameter(
            displayName="Reference Weights",
            name="reference_weights",
            datatype="Double",
            parameterType="Required",
            direction="Input")

        parameters = [input_table, fields, base_weights, reference_weights]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            parameters[1].enabled = True

    def execute(self, parameters, messages):
        """The source code of the tool."""
    
class OATForCriteria(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "OAT For Criteria"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        base_fields = arcpy.Parameter(
            displayName="Base Fields",
            name="base_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        base_fields.parameterDependencies = [input_table.name]

        reference_fields = arcpy.Parameter(
            displayName="Reference Fields",
            name="reference_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        reference_fields.parameterDependencies = [input_table.name]

        weights = arcpy.Parameter(
            displayName="Weights",
            name="weights",
            datatype="Double",
            parameterType="Required",
            direction="Input")

        parameters = [input_table, base_fields, reference_fields, weights]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            parameters[1].enabled = True

    def execute(self, parameters, messages):
        """The source code of the tool."""

class MonteCarloWeightedSum(object):
    def __init__(self):
            """Define the tool (tool name is the name of the class)."""
            self.label = "Monte Carlo Simulation"
            self.description = ""
            self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        fields = arcpy.Parameter(
            displayName="Base Fields",
            name="fields",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        fields.parameterDependencies = [input_table.name]

        # parameters to add
        # minweights = sys.argv[3]
        # maxweights = sys.argv[4]
        # simnum = sys.argv[5]
        # scoreavg = sys.argv[6]
        # rankavg = sys.argv[7]
        # rankmin = sys.argv[8]
        # rankmax = sys.argv[9]
        # rankstd = sys.argv[10]

        parameters = [input_table, fields]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            parameters[1].enabled = True

    def execute(self, parameters, messages):
        """The source code of the tool."""