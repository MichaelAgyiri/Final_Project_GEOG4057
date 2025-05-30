# -*- coding: utf-8 -*-

import arcpy
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "LULC Area Calculator"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(
                displayName="LULC Raster Layer",
                name="lulc_raster",
                datatype="GPRasterLayer",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Boundary Shapefile",
                name="boundary_shapefile",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Number of Classes",
                name="num_classes",
                datatype="GPLong",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Class Values (comma-separated)",
                name="class_values",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Pixel Resolution (meters)",
                name="pixel_size",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Folder",
                name="output_folder",
                datatype="DEFolder",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Name (no extension)",
                name="output_name",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Coordinate System for Projection",
                name="projection_coord_system",
                datatype="GPCoordinateSystem",
                parameterType="Required",
                direction="Input"
            )
        ]
        return params


    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        # Get user inputs
        raster_layer = parameters[0].valueAsText
        boundary_shapefile = parameters[1].valueAsText
        num_classes = int(parameters[2].valueAsText)
        class_values_str = parameters[3].valueAsText
        pixel_size = float(parameters[4].valueAsText)
        output_folder = parameters[5].valueAsText
        output_name = parameters[6].valueAsText
        projection_coord_system = parameters[7].valueAsText

        class_values = [int(x.strip()) for x in class_values_str.split(',') if x.strip()]
        if len(class_values) != num_classes:
            raise ValueError("Number of class values must match the specified number of classes.")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        raster = arcpy.Raster(raster_layer)
        projected_raster_path = os.path.join(output_folder, f"{output_name}_projected.tif")
        clipped_raster_path = os.path.join(output_folder, f"{output_name}_clipped.tif")
        vector_output = os.path.join(output_folder, f"{output_name}.shp")
        dissolved_output = os.path.join(output_folder, f"{output_name}_dissolved.shp")
        csv_output = os.path.join(output_folder, f"{output_name}.csv")
        chart_output = os.path.join(output_folder, f"{output_name}_chart.png")

        # Project raster
        messages.addMessage("Projecting raster to selected coordinate system...")
        arcpy.ProjectRaster_management(raster, projected_raster_path, projection_coord_system)

        # Clip raster to boundary
        messages.addMessage("Clipping raster to specified boundary shapefile...")
        arcpy.Clip_management(
            in_raster=projected_raster_path,
            out_raster=clipped_raster_path,
            in_template_dataset=boundary_shapefile,
            nodata_value="0",
            clipping_geometry="ClippingGeometry"
        )

        clipped_raster = arcpy.Raster(clipped_raster_path)
        raster_array = arcpy.RasterToNumPyArray(clipped_raster)

        messages.addMessage("Calculating area statistics by class...")
        result = []
        for class_val in class_values:
            pixel_count = np.sum(raster_array == class_val)
            area_m2 = pixel_count * (pixel_size ** 2)
            area_km2 = area_m2 / 1e6
            result.append({
                "Class": class_val,
                "Pixel_Count": int(pixel_count),
                "Area_km2": round(area_km2, 4)
            })

        df = pd.DataFrame(result)
        df.to_csv(csv_output, index=False)
        messages.addMessage(f"✅ Area stats saved to: {csv_output}")
