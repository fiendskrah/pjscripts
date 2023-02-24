# -*- coding: utf-8 -*-

import arcpy

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "th4"
        self.alias = "th4"

        # List of tool classes associated with this toolbox
        self.tools = [StandardizeRatiosScore, WeightedSumScore]

        #  NEXT: IdealPointScore, OATForWeights, OATForCriteria, MonteCarloWeightedSum, VarianceDecomposition

class StandardizeRatiosScore(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Standardize Ratios/Score"
        self.description = "Takes numerical data from a user-provided field in a data layer in the current ArcGIS Pro project, as well as a user-provided cost/benefit binary value, and returns the data as a standardized ratio or score."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        data_layer = arcpy.Parameter(
            displayName="Data Layer",
            name="data_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        field_with_numerical_data = arcpy.Parameter(
            displayName="Field with Numerical Data",
            name="field_with_numerical_data",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True,
            enabled=False)

        cost_benefit = arcpy.Parameter(
            displayName="Cost/Benefit",
            name="cost_benefit",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        cost_benefit.filter.type = "ValueList"
        cost_benefit.filter.list = ['Cost', 'Benefit']

        parameters = [data_layer, field_with_numerical_data, cost_benefit]
        return parameters

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""
        if parameters[0].value:
            data_layer = parameters[0].valueAsText
            field_info = arcpy.Describe(data_layer).fieldInfo
            fields = [field_info.getFieldName(i) for i in range(field_info.count)]
            parameters[1].filter.list = fields
            parameters[1].enabled = True
        else:
            parameters[1].enabled = False
        return


    def execute(self, parameters, messages):
        """The source code of the tool."""
        data_layer = parameters[0].valueAsText
        field_with_numerical_data = parameters[1].valueAsText
        cost_benefit = parameters[2].value

        # Get the minimum and maximum values of the user-provided field
        result = arcpy.GetRasterProperties_management(data_layer, "MINIMUM", field_with_numerical_data)
        min_value = float(result.getOutput(0))
        result = arcpy.GetRasterProperties_management(data_layer, "MAXIMUM", field_with_numerical_data)
        max_value = float(result.getOutput(0))

        # Create a list to store the standardized ratio or score
        standardized_ratios = []

        # Calculate the standardized ratio or score for each feature
        with arcpy.da.SearchCursor(data_layer, field_with_numerical_data) as cursor:
            for row in cursor:
                value = row[0]
                standardized_ratio = (value - min_value) / (max_value - min_value)
                if cost_benefit == 'Cost':
                    standardized_ratio = 1 - standardized_ratio
                standardized_ratios.append(standardized_ratio)

        # Return the standardized ratio or score
        return standardized_ratios


class WeightedSumScore(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Weighted Sum Score"
        self.description = "Takes standardized data from a site attribute table and user-provided weights, performs a weighted-sum operation, and returns a score for each site, as well as a numerical ranking of each site by its score."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        site_attribute_table = arcpy.Parameter(
            displayName="Site Attribute Table",
            name="site_attribute_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        fields = arcpy.Parameter(
            displayName="Fields",
            name="fields",
            datatype="GPValueTable",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        weights = arcpy.Parameter(
            displayName="Weights",
            name="weights",
            datatype="Double",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        parameters = [site_attribute_table, fields, weights]
        return parameters

    def execute(self, parameters, messages):
        """The source code of the tool."""
        site_attribute_table = parameters[0].valueAsText
        fields = parameters[1].values
        weights = parameters[2].values

        # Create a list to store the weighted sum score for each site
        weighted_sum_scores = []

        # Calculate the weighted sum score for each site
        with arcpy.da.SearchCursor(site_attribute_table, fields) as cursor:
            for row in cursor:
                weighted_sum_score = 0
                for i, value in enumerate(row):
                    weighted_sum_score += value * weights[i]
                weighted_sum_scores.append(weighted_sum_score)

        # Sort the weighted sum scores and create a list of rankings
        rankings = [i+1 for i in sorted(range(len(weighted_sum_scores)), key=lambda x: weighted_sum_scores[x], reverse=True)]

        # Return the weighted sum scores and rankings
        return weighted_sum_scores, rankings
