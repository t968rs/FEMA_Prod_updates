"""This script is designed to find errors with BFE lines.  It will find errors where the BFE is
snapped to the wrong line type, if the BFE crosses a Static BFE polygon, or if the BFE is has
psuedo nodes."""

# Import system modules
import os
import sys
import arcpy

class BfeCheck:
    """This script is designed to find errors with BFE lines.  It will find errors where the BFE is
    snapped to the wrong line type, if the BFE crosses a Static BFE polygon, or if the BFE is has
    psuedo nodes."""

    def __init__(self, workspace, output_folder, linear_unit):
        """Constructor for the class"""
        self.workspace = workspace  # Data location
        self.output_folder = output_folder  # Output folder
        self.extension = ""  # Entension used if the input are shapefiles
        self.linear_unit = linear_unit  # Linear snap distance

        # Feature Layers
        self.bfe_layer = ''  # BFEs
        self.bfe_end_points = ''  # BFE end points
        self.flood_lines_layer = ''  # Flooding lines
        self.flood_lines_dissolve = ''  # Flooding lines for dissolved flood polygons
        self.flood_poly_layer = ''  # Flooding polygons
        self.static_flood_layer = ''  # Static flood polygons
        self.political_lines_dissolve = ''  # Political lines for dissolved political polygons
        self.political_poly_layer = ''  # Political polygons

        # Error file locations
        self.bfe_point_error_shapefile = self.output_folder + os.sep + 'BFE_Errors_Points.shp'
        self.bfe_static_error_shapefile = self.output_folder + os.sep + 'BFEs_in_Static_Zones.shp'

        # Check if the input is a workspace or a folder containing shapefiles
        if workspace.lower().endswith(".gdb") or \
           workspace.lower().endswith(".mdb") or \
           workspace.lower().endswith(".GDB"):
            self.dataset = '\\FIRM_Spatial_Layers\\'
        else:
            self.dataset = "\\"
            self.extension = ".shp"

        # Create the workspace
        arcpy.env.workspace = workspace

        # Check that the user has an advanced license
        if arcpy.CheckProduct("arcinfo").lower() != 'alreadyinitialized':
            arcpy.AddError("An Advanced License is need to run this tool.")
            sys.exit(1)

    def make_feature_layers(self):
        """Makes the required feature layers for processing"""
        # BFEs
        self.bfe_layer = arcpy.MakeFeatureLayer_management(
            self.dataset + 'S_BFE' + self.extension, 'bfe_layer')

        # Flood lines where the LN_TYP is 'SFHA / Flood Zone Boundary'
        ln_typ_field = """{}""".format(arcpy.AddFieldDelimiters(self.workspace, "LN_TYP"))
        query = ln_typ_field + " IN ('2034', 'SFHA / Flood Zone Boundary')"
        self.flood_lines_layer = arcpy.MakeFeatureLayer_management(
            self.dataset + 'S_FLD_HAZ_LN' + self.extension, 'flood_lines_layer', query)

        # Flood Polygons for Zones that can have BFEs
        fld_zone_field = """{}""".format(arcpy.AddFieldDelimiters(self.workspace, "FLD_ZONE"))
        static_bfe_field = """{}""".format(arcpy.AddFieldDelimiters(self.workspace, "STATIC_BFE"))
        query = fld_zone_field + " IN ('AE', 'AH', 'AR') AND " + static_bfe_field + "= -9999"
        self.flood_poly_layer = arcpy.MakeFeatureLayer_management(
            self.dataset + 'S_FLD_HAZ_AR' + self.extension, 'flood_poly_layer', query)

        # Static Flood Polygons
        static_bfe_field = """{}""".format(arcpy.AddFieldDelimiters(self.workspace, "STATIC_BFE"))
        query = static_bfe_field + "<> -9999"
        self.static_flood_layer = arcpy.MakeFeatureLayer_management(
            self.dataset + 'S_FLD_HAZ_AR' + self.extension, "static_flood_layer", query)

        # Political polygons
        self.political_poly_layer = arcpy.MakeFeatureLayer_management(
            self.dataset + 'S_POL_AR' + self.extension, 'political_poly_layer')

    def check_missing_empty_tables(self):
        """Check for empty or missing tables"""

        # Flag for an error found
        error = False

        # S_BFE
        if not arcpy.Exists(self.dataset + 'S_BFE' + self.extension):
            arcpy.AddError("S_BFE could not be found")
            error = True
        else:
            if int(arcpy.GetCount_management(self.dataset + 'S_BFE' + self.extension)[0]) == 0:
                arcpy.AddError("S_BFE is empty")
                error = True

        # S_Fld_Haz_Ar
        if not arcpy.Exists(self.dataset + 'S_FLD_HAZ_AR' + self.extension):
            arcpy.AddError("S_FLD_HAZ_AR could not be found")
            error = True
        else:
            if int(arcpy.GetCount_management(
                self.dataset + 'S_FLD_HAZ_AR' + self.extension)[0]) == 0:
                arcpy.AddError("S_FLD_HAZ_AR is empty")
                error = True

        # S_Fld_Haz_Ln
        if not arcpy.Exists(self.dataset + 'S_FLD_HAZ_LN' + self.extension):
            arcpy.AddError("S_FLD_HAZ_LN could not be found")
            error = True
        else:
            if int(arcpy.GetCount_management(
                self.dataset + 'S_FLD_HAZ_LN' + self.extension)[0]) == 0:
                arcpy.AddError("S_FLD_HAZ_LN is empty")
                error = True

        # S_Pol_Ar
        if not arcpy.Exists(self.dataset + 'S_POL_AR' + self.extension):
            arcpy.AddError("S_POL_AR could not be found")
            error = True
        else:
            if int(arcpy.GetCount_management(self.dataset + 'S_POL_AR' + self.extension)[0]) == 0:
                arcpy.AddError("S_POL_AR is empty")
                error = True

        # Exit if an error is found
        if error:
            sys.exit(1)

    def remove_temporary_layers(self):
        """Remove the feature layers that were created"""
        if self.bfe_layer:
            arcpy.Delete_management('bfe_layer')
        if self.flood_lines_layer:
            arcpy.Delete_management('flood_lines_layer')
        if self.bfe_end_points:
            arcpy.Delete_management(self.bfe_end_points)
        if self.flood_poly_layer:
            arcpy.Delete_management('flood_poly_layer')
        if self.flood_lines_dissolve:
            arcpy.Delete_management(self.flood_lines_dissolve)
        if self.political_poly_layer:
            arcpy.Delete_management('political_poly_layer')
        if self.political_lines_dissolve:
            arcpy.Delete_management(self.political_lines_dissolve)
        if self.static_flood_layer:
            arcpy.Delete_management('static_flood_layer')
        if arcpy.Exists(self.output_folder + os.sep + 'BFE_End_Points.shp'):
            arcpy.Delete_management(self.output_folder + os.sep + 'BFE_End_Points.shp')
        if arcpy.Exists(self.output_folder + os.sep + 'flood_lines_dissolved.shp'):
            arcpy.Delete_management(self.output_folder + os.sep + 'flood_lines_dissolved.shp')
        if arcpy.Exists(self.output_folder + os.sep + 'political_lines_dissolved.shp'):
            arcpy.Delete_management(self.output_folder + os.sep + 'political_lines_dissolved.shp')

    def bfe_endpoint_check(self):
        """Checks if the end points of the bfe are snapped to appropriate lines"""
        # Convert BFE vertices to points
        end_points = arcpy.FeatureVerticesToPoints_management(
            self.bfe_layer, self.output_folder + os.sep + 'BFE_End_Points.shp', 'BOTH_ENDS')

        # Feature layer is needed for the Select By Location tool
        self.bfe_end_points = arcpy.MakeFeatureLayer_management(end_points, 'bfe_end_points')

        # Dissolve the flooding polygons.
        self.__dissolve_flood_polygons()

        # Dissolve the political polygons.
        self.__dissolve_political_polygons()

        # Select the BFE's that intersect the flooding lines and political lines.
        # These are the BFEs that are snapped to the flood polygon lines or poltical boundary
        # extent of the appropriate polygons 0.00762 is the cluster tolerance of the FEMA Databases
        arcpy.SelectLayerByLocation_management(
            self.bfe_end_points, "INTERSECT", self.flood_lines_dissolve,
            self.linear_unit, selection_type="NEW_SELECTION")

        arcpy.SelectLayerByLocation_management(
            self.bfe_end_points, "INTERSECT", self.political_lines_dissolve,
            self.linear_unit, selection_type="ADD_TO_SELECTION")

        # Switch the selection.  These are the errors.
        arcpy.SelectLayerByAttribute_management(self.bfe_end_points, "SWITCH_SELECTION")

        # Create the output feature class with the errors
        if arcpy.Exists(self.bfe_point_error_shapefile):
            arcpy.Delete_management(self.bfe_point_error_shapefile)
        arcpy.CopyFeatures_management(self.bfe_end_points, self.bfe_point_error_shapefile)

        # Clear the selection
        arcpy.SelectLayerByAttribute_management(self.bfe_end_points, "CLEAR_SELECTION")

        # Check to see if BFE's are snapped to the wrong line type
        arcpy.SelectLayerByLocation_management(
            self.bfe_end_points, "INTERSECT", self.flood_lines_layer,
            self.linear_unit, "NEW_SELECTION")

        arcpy.SelectLayerByLocation_management(
            self.bfe_end_points, "INTERSECT", self.political_lines_dissolve,
            self.linear_unit, "ADD_TO_SELECTION")

        # Switch the selection.  These are the errors.
        arcpy.SelectLayerByAttribute_management(self.bfe_end_points, "SWITCH_SELECTION")

        # Append these errors to the existing bfe_point_error_shapefile
        arcpy.Append_management(self.bfe_end_points, self.bfe_point_error_shapefile)

        # Clear the selection
        arcpy.SelectLayerByAttribute_management(self.bfe_end_points, "CLEAR_SELECTION")

        # Update spatial index
        arcpy.AddSpatialIndex_management(self.bfe_point_error_shapefile)

    def bfe_static_area_check(self):
        """Checks to see if the bfe is crossing the wrong flood zone such as static flood zones"""
        arcpy.SelectLayerByLocation_management(
            self.bfe_layer, "WITHIN", self.static_flood_layer, "0", "NEW_SELECTION")

        # Create the output feature class with the errors
        if arcpy.Exists(self.bfe_static_error_shapefile):
            arcpy.Delete_management(self.bfe_static_error_shapefile)
        arcpy.CopyFeatures_management(self.bfe_layer, self.bfe_static_error_shapefile)

        # Update spatial index
        arcpy.AddSpatialIndex_management(self.bfe_static_error_shapefile)

    def __dissolve_flood_polygons(self):
        """Dissolves the flood polygons and creates the new bounding lines"""
        flood_polys_dissolved = arcpy.Dissolve_management(
            self.flood_poly_layer, 'in_memory\\flood_polys_dissolved', "", "", "SINGLE_PART")

        lines_dissolve = arcpy.FeatureToLine_management(
            flood_polys_dissolved, self.output_folder + os.sep + 'flood_lines_dissolved.shp')

        self.flood_lines_dissolve = arcpy.MakeFeatureLayer_management(
            lines_dissolve, 'flood_lines_dissolved')

        arcpy.Delete_management(flood_polys_dissolved)

    def __dissolve_political_polygons(self):
        """Dissolves the political polygons and creates the new bounding lines"""
        political_polys_dissolved = arcpy.Dissolve_management(
            self.political_poly_layer, 'in_memory\\political_polys_dissolved', "", "",
            "SINGLE_PART")

        arcpy.FeatureToLine_management(
            political_polys_dissolved,
            self.output_folder + os.sep + 'political_lines_dissolved.shp')

        self.political_lines_dissolve = arcpy.MakeFeatureLayer_management(
            political_polys_dissolved, 'political_lines_dissolved')

        arcpy.Delete_management(political_polys_dissolved)

    def delete_empty_error_files(self):
        """Removes the empty error files"""
        if arcpy.Exists(self.bfe_point_error_shapefile):
            result = arcpy.GetCount_management(self.bfe_point_error_shapefile)
            if int(result[0]) == 0:
                arcpy.Delete_management(self.bfe_point_error_shapefile)
                arcpy.AddMessage("No BFE endpoint errors found")
            else:
                arcpy.AddMessage("BFE endpoint errors found. See error shapefile.")

        if arcpy.Exists(self.bfe_static_error_shapefile):
            result = arcpy.GetCount_management(self.bfe_static_error_shapefile)
            if int(result[0]) == 0:
                arcpy.Delete_management(self.bfe_static_error_shapefile)
                arcpy.AddMessage("No BFE's in static areas errors found")
            else:
                arcpy.AddMessage("BFE's in static areas errors found. See error shapefile.")


if __name__ == "__main__":
    try:
        # Create the instance of the class
        arcpy.AddMessage('Starting BFE Checks...')
        bfe_check = BfeCheck(sys.argv[1], sys.argv[2], sys.argv[3])
                
        bfe_check.check_missing_empty_tables()
        bfe_check.make_feature_layers()
        bfe_check.bfe_endpoint_check()
        bfe_check.bfe_static_area_check()
        bfe_check.delete_empty_error_files()

        arcpy.AddMessage('...done BFE Checks')
        
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        print(arcpy.GetMessages(2))

    finally:
        bfe_check.remove_temporary_layers()



