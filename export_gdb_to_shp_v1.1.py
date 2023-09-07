"""Exports all the feature classes and tables within a workspace that contain data"""

import arcpy
import sys
import os
import time
import logging
from static_tools import StaticTools


class ExportShapefiles:
    """Exports all the feature classes and tables within a workspace that contain data"""

    def __init__(self, workspace, output_folder, keep_temp):
        """Constructor"""
        self.workspace = workspace
        self.output_folder = output_folder

        self.keep_temp = keep_temp

        # Table and FC dictionaries
        self.fc_dict = {}
        self.table_dict = {}
        self.record_counts = {}
        self.domain_fields = {}

        self.exported = []

        # Set the workspace
        arcpy.env.workspace = self.workspace

    def format_input_values(self):

        # T/F String --> Bool
        for var_name in ['keep_temp']:
            var_value = getattr(self, var_name)
            if type(var_value) == str:
                if var_value in ["#", 'false', '']:
                    setattr(self, var_name, False)
                else:
                    setattr(self, var_name, True)

        # Paths from inputs
        for var_name in []:
            var_value = getattr(self, var_name)
            if var_value not in [None, '#', '']:
                if not os.path.split(var_value)[0]:
                    desc = arcpy.Describe(var_value)
                    base_path, name = desc.path, desc.name
                    new_path = os.path.join(base_path, name)
                    setattr(self, var_name, new_path)
                    arcpy.AddMessage(f'  Updated path for {var_value}:\n   {new_path}')
            else:
                setattr(self, var_name, None)

    def get_rootdir_get_runoptions(self):

        root_folder = os.path.split(self.workspace)[0]
        run_options = {'Input GDB': self.workspace, 'Output Folder': self.output_folder}

        return root_folder, run_options

    def find_feature_classes(self):
        """Exports the feature classes that have data to shapefiles"""
        # List of feature datasets
        datasets = arcpy.ListDatasets()

        # Dictionary of items to export
        export_dict = {}
        record_counts = {}

        # Walk through each in_dataset
        for dataset in datasets:
            fc_list = arcpy.ListFeatureClasses("", "", dataset)
            fc_list.sort()

            # Walk through the feature classes and store them
            for fc in fc_list:
                # Generate in/out paths
                inpath = os.path.join(self.workspace, dataset, fc)
                outpath = os.path.join(self.output_folder, f'{fc}.shp')

                # If not empty and not already in output, add to dictionary
                if os.path.exists(outpath):
                    arcpy.AddWarning(str(fc) + " already exists.  Skipping.")
                else:
                    count = sum(1 for row in arcpy.da.SearchCursor(inpath, ['OID@']))
                    if count != 0:
                        export_dict[inpath] = outpath
                        record_counts[inpath] = count

        self.fc_dict = export_dict
        self.record_counts = record_counts

    def find_tables(self):
        """Exports the tables that have data to shapefiles"""
        # List of tables
        table_list = arcpy.ListTables()
        table_list.sort()

        table_dict = {}

        for table in table_list:
            inpath = os.path.join(self.workspace, table)
            outpath = os.path.join(self.output_folder, f'{table}.dbf')

            # Add the table if it's not empty and doesn't already exist
            if os.path.exists(outpath):
                print(str(table) + " already exists.  Skipping.")
                arcpy.AddWarning(str(table) + " already exists.  Skipping.")
            else:
                count = sum(1 for row in arcpy.da.SearchCursor(inpath, ['OID@']))
                if count != 0:
                    table_dict[inpath] = outpath
                    self.record_counts[inpath] = count

        self.table_dict = table_dict

    def drop_fields(self):
        """Drop fields from the exported shapefiles"""
        arcpy.env.workspace = self.output_folder

        fc_list = arcpy.ListFeatureClasses()

        for fc in fc_list:
            field_list = arcpy.ListFields(fc)
            for field in field_list:
                if field.name in ['SHAPE_Leng', 'SHAPE_Area', 'OBJECTID']:
                    if not field.required:
                        arcpy.management.DeleteField(fc, field.name)

    def remove_extra_files(self):
        """Removes the cpg and xml files that ArcGIS creates"""
        # Delete cpg files
        arcpy.AddMessage(f'Removing extra files')
        StaticTools.setup_logging(function_name='remove_extra_files', output_folder=self.output_folder)
        ef_logger = logging.getLogger('remove_extra_files')
        ef_logger.info(f'\n\n -- NEW LOG --\n')
        ef_logger.info(f'Looking in {self.output_folder}')

        found_files = []
        deleted = []
        for filename in os.listdir(str(self.output_folder)):
            found_files.append(f'{os.path.split(filename)[1]}')
            if filename.endswith(".cpg"):
                logging.info(f' Deleting {os.path.split(filename)[1]}')
                deleted.append(os.path.split(filename)[1])
                os.remove(str(self.output_folder) + "\\" + filename)
            for ext_str in [".dbf.xml", ".shp.xml"]:
                if ext_str in filename:
                    # arcpy.AddMessage(f' Deleting {filename}')
                    logging.info(f' Deleting {os.path.split(filename)[1]}')
                    os.remove(str(self.output_folder) + "\\" + filename)
                    deleted.append(os.path.split(filename)[1])
        logging.info(f'Found {len(found_files)}')
        logging.info(f'Deleted {len(deleted)}:\n  {deleted}')

    def remove_fmd_compliance(self):
        """Removes the tables, feature classes and X_Scale from the export"""
        # Remove X_Scale from S_FIRM_PAN
        if arcpy.Exists(self.output_folder + os.sep + "S_FIRM_Pan.shp"):
            field_list = arcpy.ListFields(self.output_folder + os.sep + "S_FIRM_Pan.shp", 'X_SCALE')
            if field_list:
                arcpy.DeleteField_management(self.output_folder + os.sep + 'S_FIRM_PAN.shp', 'X_SCALE')

        # Remove X_ERRORSDOMAIN table
        if arcpy.Exists(self.output_folder + os.sep + 'X_ERRORSDOMAIN.dbf'):
            arcpy.Delete_management(self.output_folder + os.sep + 'X_ERRORSDOMAIN.dbf')

        # Remove X_ERRORS and X_MASK feature classes
        if arcpy.Exists(self.output_folder + os.sep + 'X_ERRORS.shp'):
            arcpy.Delete_management(self.output_folder + os.sep + 'X_ERRORS.shp')
        if arcpy.Exists(self.output_folder + os.sep + 'X_MASK.shp'):
            arcpy.Delete_management(self.output_folder + os.sep + 'X_MASK.shp')

    def export_files(self):

        exported = []

        for inpath, outpath in self.fc_dict.items():
            name = os.path.split(inpath)[1]
            arcpy.env.transferDomains = True
            arcpy.conversion.FeatureClassToFeatureClass(inpath, self.output_folder, name)
            arcpy.AddSpatialIndex_management(outpath)
            arcpy.management.RepairGeometry(outpath, validation_method='OGC')
            arcpy.AddMessage(f'  {name}\n   exported to  {self.output_folder}\n')
            exported.append(name)

        for inpath, outpath in self.table_dict.items():
            name = os.path.split(inpath)[1]
            arcpy.conversion.TableToDBASE(inpath, self.output_folder)
            arcpy.AddMessage(f'  {name}\n   exported to {self.output_folder}\n')
            exported.append(name)

        self.exported = exported

    def populate_domain_fields(self):

        arcpy.env.workspace = self.output_folder

        # Populate dictionary with: domain description fields AND their associated code fields
        domain_dict = {}

        fc_list = arcpy.ListFeatureClasses() + arcpy.ListTables()
        for fc in fc_list:
            fields_todelete = []
            field_pairs = []
            fc_path = os.path.join(self.output_folder, fc)
            domain_dict[fc_path] = {'Del Field List': fields_todelete, 'Field Pairs': field_pairs}

            field_list = [f.name for f in arcpy.ListFields(fc)]
            # arcpy.AddMessage(f'{fc}: {field_list}')
            for fname in field_list:

                if fname.startswith('d_'):
                    arcpy.AddMessage(f' |{fc}|\n  - Found {fname}')
                    domain_postfix = fname.split('d_')[1]
                    for fema_field in field_list:
                        if fema_field.startswith(domain_postfix):
                            field_pairs.append((fema_field, fname))
                            fields_todelete.append(fname)
            # arcpy.AddMessage(f'{fc} has {len(fields_todelete)} domain fields to delete...')

            # Add field pairs and fields to delete to dictionary
            domain_dict[fc_path]['Del Field List'] = fields_todelete
            domain_dict[fc_path]['Field Pairs'] = field_pairs

        self.domain_fields = domain_dict

    def create_temp_field(self):

        for shp_path, dictionary in self.domain_fields.items():
            shp_name = os.path.split(shp_path)[1]

            field_pair_list = dictionary['Field Pairs']
            field_pair_list_static = field_pair_list.copy()
            if len(field_pair_list) > 0:
                arcpy.AddMessage(f'  Populating {len(field_pair_list)} domain-sourced fields for {shp_name}')
                arcpy.AddMessage(f'Field Pairs: {field_pair_list}')
            for pair in field_pair_list_static:
                target_field = pair[0]
                source_field = pair[1]

                # Create new field to hold original field values
                new_field_name = target_field + "_t"
                arcpy.management.AddField(shp_path, new_field_name, "Text", field_length='500')

                # Update field "pairs" to include temp
                old_pair = pair
                add_pair = (new_field_name,)
                # arcpy.AddMessage(f'Type of old_pair: {type(old_pair)}, Type of add_pair: {type(add_pair)}')
                # arcpy.AddMessage(f'Old Pair: {old_pair}, New Pair: {add_pair}')
                new_pair = old_pair + add_pair
                field_pair_list.remove(pair)
                field_pair_list.append(new_pair)

                # Add delete field *if* not a mix of domains and values
                if not self.keep_temp:
                    del_fields = self.domain_fields[shp_path]['Del Field List']
                    del_fields.append(new_field_name)

    def update_domain_fields(self):

        # Update fields with domain descriptions found earlier
        for shp_path, dictionary in self.domain_fields.items():
            shp_name = os.path.split(shp_path)[1]

            field_pair_list = dictionary['Field Pairs']
            # arcpy.AddMessage(f'SHP: {shp_name}, Pairs: {field_pair_list}')
            if len(field_pair_list) > 0:
                arcpy.AddMessage(f'  Populating {len(field_pair_list)} domain-sourced fields for {shp_name}')
            for pair in field_pair_list:
                target_field = pair[0]
                source_field = pair[1]
                temp_field = pair[2]

                with arcpy.da.UpdateCursor(shp_path, [target_field, source_field, temp_field]) as u_cursor:
                    for urow in u_cursor:
                        urow[2] = urow[0]

                        target = urow[0]
                        source = urow[1]

                        for x in target:
                            if x.isdigit():
                                if source is not None and source != '':
                                    target = source
                                    break
                                break
                        if len(source) > len(target):
                            target = source
                        elif target in [None, '', ' '] and source in [None, '', ' ']:
                            target = 'NP'

                        urow[0] = target
                        u_cursor.updateRow(urow)
                del u_cursor

    def delete_domain_description_fields(self):

        arcpy.env.workspace = self.output_folder
        # Delete domain-description fields transferred to SHP files
        for shp_path, dictionary in self.domain_fields.items():
            f_del_list = dictionary['Del Field List']
            shp_name = os.path.split(shp_path)[1]
            if len(f_del_list) > 0:
                try:
                    arcpy.management.DeleteField(shp_path, f_del_list)
                    arcpy.AddMessage(f' Successfully deleted all "d_" fields from {shp_name}')
                except:
                    del_count = 0
                    for field in f_del_list:
                        arcpy.management.DeleteField(shp_path, [field])
                        del_count += 1
                        f_del_list.remove(field)
                    if del_count >= len(f_del_list):
                        arcpy.AddMessage(f' Individually deleted all "d_" fields from {shp_name}')
                    else:
                        arcpy.AddMessage(f' Was not able to delete: {f_del_list} in {shp_name}')

    def run_all(self):
        """Run all required methods"""

        # Start timer
        times_recorded = {'Start': time.time()}
        rootfolder, run_options = self.get_rootdir_get_runoptions()
        timer = TimeReports(workspace=rootfolder, options=run_options)

        self.find_feature_classes()
        self.find_tables()
        times_recorded['Found GDB files'] = time.time()

        self.export_files()
        times_recorded[f'Exported {len(self.exported)} files'] = time.time()
        timer.time_reporter(times=times_recorded, new_iter=True, class_name='ExportShapefiles')

        self.populate_domain_fields()
        self.create_temp_field()
        self.update_domain_fields()
        times_recorded['Populated fields with domain descriptions'] = time.time()
        timer.time_reporter(times=times_recorded, new_iter=False, class_name='ExportShapefiles')

        self.delete_domain_description_fields()
        times_recorded['Deleted "d_" fields'] = time.time()
        timer.time_reporter(times=times_recorded, new_iter=False, class_name='ExportShapefiles')

        # self.remove_fmd_compliance()
        self.remove_extra_files()
        self.drop_fields()
        times_recorded['Dropped extra fields and files'] = time.time()
        timer.time_reporter(times=times_recorded, new_iter=False, class_name='ExportShapefiles')


class TimeReports:

    def __init__(self, workspace, options):

        self.times_dictionary = None
        self.start_time = None
        self.printed = []

        self.workspace = workspace
        self.options = options

    def get_start_time(self):

        start_time = 0
        for heading, a_time in self.times_dictionary.items():
            if 'start' in heading.lower():
                start_time = a_time
                break
        self.start_time = start_time

    def append_dictionary(self, times):

        if not self.times_dictionary:
            self.times_dictionary = times
        else:
            self.times_dictionary = self.times_dictionary.update(times)

    def time_reporter(self, times, new_iter, class_name):

        # Check for existing values
        self.append_dictionary(times)
        if not self.start_time:
            self.get_start_time()

        time_results = os.path.join(self.workspace, f"time_results_{class_name}.txt")
        time_printout = open(time_results, "a")
        if new_iter:
            time_printout.writelines(f"\n\n    ---- THIS IS A NEW ITERATION ----\n\n")
            for option_def, option in self.options.items():
                time_printout.writelines(f'\n{option_def}: {option}')
        time_printout.close()

        timenames = list(times.keys())
        elapsed_times = {}
        self.times_dictionary = self.times_dictionary.update(times)

        for timename in timenames:
            if timename not in self.printed:
                total_seconds = times[timename]
                elapsed = total_seconds - self.start_time
                hours = elapsed // 3600
                elapsed = elapsed - 3600 * hours
                minutes = elapsed // 60
                elapsed = elapsed - 60 * minutes
                seconds = round(elapsed, 2)
                elapsed_times[timename] = (hours, minutes, seconds)
                print(f"{timename} processing finished after: {hours} hours, {minutes} minutes, {seconds} seconds")
                time_printout = open(time_results, "a")
                time_printout.writelines(f"\n{timename}: \n{hours} hours, {minutes} minutes, {seconds} seconds\n")
                time_printout.close()
                self.printed.append(timename)


if __name__ == "__main__":
    try:
        export_shapefiles = ExportShapefiles(sys.argv[1], sys.argv[2], sys.argv[3])
        export_shapefiles.run_all()

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        print(arcpy.GetMessages(2))
