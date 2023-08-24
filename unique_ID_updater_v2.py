"""Sequentially numbers the unique ID fields"""
import arcpy
import os
import sys


class IDUpdater:
    def __init__(self, tables):
        """Constructor for the class"""
        self.tables = tables

    def get_paths(self):

        table_pathlist = []
        for table in self.tables:
            if table is not None:
                if not os.path.split(table)[0]:
                    desc = arcpy.Describe(table)
                    base_path, name = desc.path, desc.name
                    new_path = os.path.join(base_path, name)
                    table_pathlist.append(new_path)
                    arcpy.AddMessage(f'Table, {table}:\n   {new_path}')
        self.tables = table_pathlist

    def update_unique_id(self):
        # Start an edit session
        for table in self.tables:

            # Get a list of fields that have a type of 'DOUBLE'
            field_list = arcpy.ListFields(table.replace("'", ""), field_type='String')

            # List of fields with 'ID' in their name that should be skipped
            skip_fields = ['COM_NFO_ID', 'CST_MDL_ID', 'DFIRM_ID', 'FC_SEG_ID', 'FC_SYS_ID', 'GAGE_OWNID', 'MODEL_ID',
                           'MTG_ID', 'NODE_ID', 'START_ID', 'STRUCT_ID', 'SURVSTR_ID', 'TBASELN_ID', 'TRAN_LN_ID',
                           'VERSION_ID', 'XS_LN_ID']

            record_num = 1  # Record number

            # Iterate through the list of fields
            for field in field_list:
                field_name = str(field.name).upper()
                if field_name.endswith("_ID") and field_name not in skip_fields:
                    arcpy.AddMessage('\t' + field.name)

                    # Create an UpdateCursor
                    with arcpy.da.UpdateCursor(str(table).replace("'", ""), [field.name]) as cursor:
                        for row in cursor:
                            row[0] = str(record_num)
                            record_num += 1
                            # Update the row's value and move onto the next row
                            cursor.updateRow(row)

                    # Remove the current cursor and row
                    del cursor
                    del row

    def run_id_updater(self):

        self.update_unique_id()


if __name__ == '__main__':
    try:
        # Values for sys.argv that come from ArcToolbox are a single string with the input values separated
        # by a semicolon.  Therefore, they need to be split out to a list.  If the input value is empty, ArcToolbox uses
        # a '#', so skip the code if the value is empty (a #)
        if sys.argv[1] and sys.argv[1] != '#':
            table_list = sorted(sys.argv[1].split(";"))
            id_update = IDUpdater(table_list)
            id_update.run_id_updater()

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        print(arcpy.GetMessages(2))
