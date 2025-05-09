
        # Plotting bar chart
        plt.figure(figsize=(8, 6))
        plt.bar(df['Class'].astype(str), df['Area_km2'], color='skyblue')
        plt.xlabel("LULC Class")
        plt.ylabel("Area (km²)")
        plt.title("LULC Class Area Distribution")
        plt.tight_layout()
        plt.savefig(chart_output)
        plt.close()
        messages.addMessage(f"📊 Area chart saved to: {chart_output}")

        # Convert raster to polygon and dissolve
        messages.addMessage("Converting clipped raster to polygon...")
        arcpy.RasterToPolygon_conversion(clipped_raster, vector_output, "NO_SIMPLIFY", "Value")

        messages.addMessage("Dissolving polygons by class value...")
        arcpy.Dissolve_management(vector_output, dissolved_output, "gridcode")

        messages.addMessage("Calculating area per class polygon...")
        arcpy.AddField_management(dissolved_output, "Area_km2", "DOUBLE")
        with arcpy.da.UpdateCursor(dissolved_output, ["SHAPE@", "Area_km2"]) as cursor:
            for row in cursor:
                row[1] = round(row[0].getArea("PLANAR", "SQUAREKILOMETERS"), 4)
                cursor.updateRow(row)

        # Add to map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_view = aprx.activeMap
        map_view.addDataFromPath(dissolved_output)

        messages.addMessage("🎉 Done! Vector layer and class area chart have been generated and added.")
 
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
