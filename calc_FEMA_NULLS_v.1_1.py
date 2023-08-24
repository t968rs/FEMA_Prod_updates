"""Updates the NULL values to match FEMA specs"""
import arcpy
import os
import sys


class CalculateNull:
    def __init__(self, tables=None):
        """Constructor.  Expects a workspace."""
        self.tables = tables  # List of tables to update

        # A list of fields the script can skip because they can't be updated
        self.skip_fields = ["OBJECTID", "SHAPE", "SHAPE_Length", "SHAPE_Area", "X_SCALE"]

        self.table_records = {}
        self.table_types = {}

        # Dictionary of 'applicable' fields
        self.app_Dict = {"S_Alluvial_Fan": ["FAN_VEL_MN", "FAN_VEL_MX", "VEL_UNIT", "DEPTH", "DEPTH_UNIT", "METH_DESC"],
                         "S_Base_Index": [],
                         "S_BFE": [],
                         "S_CBRS": [],
                         "S_Cst_Gage": ["CST_MDL_ID", "REC_INTVL", "TIME_UNIT", "START_TIME", "END_TIME", "DATUM_CONV",
                                        "TIDE_EPOCH", "TIDE_VBM", "WDSTN_HT"],
                         "S_Cst_Tsct_Ln": ["METHOD", "DATUM_CONV", "BEACH_SET", "SHORE_TYP", "CST_MDL_ID", "SIG_HT",
                                           "SIG_PD", "CON_HT", "CON_PD", "MEAN_HT", "MEAN_PD", "FETCH_LEN",
                                           "FTCHLNUNIT", "EROS_METH", "LU_SOURCE", "VZONE_EXT", "SETUP_DPTH",
                                           "LEN_UNIT", "TIME_UNIT"],
                         "S_Datum_Conv_Pt": ["QUAD_NM", "QUAD_COR", "WTR_NM"],
                         "S_FIRM_Pan": ["PRE_DATE", "EFF_DATE", "PNP_REASON"],
                         "S_Fld_Haz_Ar": ["ZONE_SUBTY", "STATIC_BFE", "V_DATUM", "DEPTH", "LEN_UNIT", "VELOCITY",
                                          "VEL_UNIT", "AR_REVERT", "AR_SUBTRV", "BFE_REVERT", "DEP_REVERT",
                                          "DUAL_ZONE"],
                         "S_Fld_Haz_Ln": [],
                         "S_Gage": ["GAGE_OWNID", "DTA_ACCESS", "REC_INTRVL", "TIME_UNIT"],
                         "S_Gen_Struct": ["CST_STRUCT", "STRUCT_NM", "LOC_DESC", "STRUC_DESC", "S_HWM"],
                         "S_Hydro_Reach": ["UP_NODE", "DN_NODE", "ROUTE_METH"],
                         "S_Label_Ld": [],
                         "S_Label_Pt": ["LABEL2"],
                         "S_Levee": ["DISTRICT", "CONST_DATE", "DGN_FREQ", "FREEBOARD", "PAL_DATE", "LVDBASE_ID"],
                         "S_LiMWA": [],
                         "S_LOMR": [],
                         "S_Nodes": ["NODE_TYP"],
                         "S_PFD_Ln": [],
                         "S_PLSS_Ar": ["RANGE", "TWP", "NAME"],
                         "S_Pol_Ar": ["POL_NAME2", "POL_NAME3", "ANI_FIRM", "COM_NFO_ID"],
                         "S_Profil_Basln": ["SEGMT_NAME", "V_DATM_OFF", "DATUM_UNIT", "FLD_PROB1", "FLD_PROB2",
                                            "FLD_PROB3", "SPEC_CONS1", "SPEC_CONS2"],
                         "S_Riv_Mrk": [],
                         "S_Stn_Start": [],
                         "S_Subbasins": ["NODE_ID"],
                         "S_Submittal_Info": ["HUC8", "HYDRO_MDL", "HYDRA_MDL", "CST_MDL_ID", "TOPO_SRC", "TOPO_SCALE",
                                              "CONT_INTVL"],
                         "S_Topo_Confidence": ["DATESTAMP"],
                         "S_Trnsport_Ln": ["ALTNAME1", "ALTNAME2", "ROUTENUM"],
                         "S_Tsct_Basln": ["CST_MDL_ID"],
                         "S_Wtr_Ar": ["SHOWN_FIRM", "SHOWN_INDX"],
                         "S_Wtr_Ln": ["SHOWN_FIRM", "SHOWN_INDX"],
                         "S_XS": ["XS_LTR", "PROFXS_TXT", "SEQ"],
                         "Study_Info": ["STUDY_PRE", "JURIS_TYP", "PROJ_ZONE", "PROJ_SECND", "PROJ_SUNIT", "PROJ_SZONE",
                                        "AVG_CFACTR"],
                         "L_Comm_Info": ["REPOS_ADR2", "REPOS_ADR3", "RECENT_DAT"],
                         "L_Comm_Revis": [],
                         "L_Cst_Model": ["SURGE_MDL", "SURGE_DATE", "SURGE_EFF", "STRM_PRM", "STM_PRM_DT", "TDESTAT_MT",
                                         "TDESTAT_DT", "WAVEHT_MDL", "WAVEHT_DT", "RUNUP_MDL", "RUNUP_DATE",
                                         "SETUP_METH", "SETUP_DATE", "R_FETCH_MT", "R_FETCH_DT", "EROS_METH",
                                         "EROS_DATE", "WAVE_EFFDT"],
                         "L_Cst_Struct": ["CERT_DOC", "SURVEY_DT", "SURVEY_TM"],
                         "L_Cst_Tsct_Elev": ["WSEL_START", "WSEL_MIN", "WSEL_MAX"],
                         "L_ManningsN": [],
                         "L_Meetings": [],
                         "L_MT2_LOMR": [],
                         "L_Mtg_POC": ["CNT_TITLE", "AGY_ROLE", "ADDRESS", "ADDRESS_2", "CITY", "STATE", "ZIP", "PHONE",
                                       "PHONE_EXT", "EMAIL", "COMMENTS"],
                         "L_Pan_Revis": [],
                         "L_Pol_FHBM": [],
                         "L_Profil_Bkwtr_El": ["BKWTR_WSEL"],
                         "L_Profil_Label": [],
                         "L_Profil_Panel": [],
                         "L_Source_Cit": ["CITATION", "AUTHOR", "PUB_PLACE", "WEBLINK", "SRC_SCALE", "SRC_DATE",
                                          "DATE_REF", "CONTRIB", "NOTES"],
                         "L_Summary_Discharges": ["WSEL", "WSEL_UNIT", "V_DATUM"],
                         "L_Summary_Elevations": [],
                         "L_Survey_Pt": ["PROJ_ZONE"],
                         "L_XS_Elev": ["FW_WIDTH", "FW_WIDTHIN", "NE_WIDTH_L", "NE_WIDTH_R", "XS_AREA", "AREA_UNIT",
                                       "VELOCITY", "VEL_UNIT", "WSEL", "WSEL_WOFWY", "WSEL_FLDWY", "WSEL_INCRS",
                                       "LVSCENARIO", "WSELREG_LL", "WSELREG_RL", "FREEBRD_LL", "FREEBRD_RL"],
                         "L_XS_Struct": []
                         }

        # List of tables to iterate through
        self.iter_tables = ["S_Alluvial_Fan", "S_Base_Index", "S_BFE", "S_CBRS", "S_Cst_Gage", "S_Cst_Tsct_Ln",
                            "S_Datum_Conv_Pt", "S_FIRM_Pan", "S_Fld_Haz_Ar", "S_Fld_Haz_Ln", "S_Gage", "S_Gen_Struct",
                            "S_Hydro_Reach", "S_Label_Ld", "S_Label_Pt", "S_Levee", "S_LiMWA", "S_LOMR", "S_Nodes",
                            "S_PFD_Ln", "S_PLSS_Ar", "S_Pol_Ar", "S_Profil_Basln", "S_Riv_Mrk", "S_Stn_Start",
                            "S_Subbasins", "S_Submittal_Info", "S_Topo_Confidence", "S_Trnsport_Ln", "S_Tsct_Basln",
                            "S_Wtr_Ar", "S_Wtr_Ln", "S_XS", "Study_Info", "L_Comm_Info", "L_Comm_Revis", "L_Cst_Model",
                            "L_Cst_Struct", "L_Cst_Tsct_Elev", "L_ManningsN", "L_Meetings", "L_MT2_LOMR", "L_Mtg_POC",
                            "L_Pan_Revis", "L_Pol_FHBM", "L_Profil_Bkwtr_El", "L_Profil_Label", "L_Profil_Panel",
                            "L_Source_Cit", "L_Summary_Discharges", "L_Summary_Elevations", "L_Survey_Pt", "L_XS_Elev",
                            "L_XS_Struct"]

    def input_type(self):

        table_types = {}
        for table in self.tables:
            fname_list = [f.name for f in arcpy.ListFields(table)]
            if 'OBJECTID' not in fname_list:
                table_types[table] = "SHP"
            else:
                table_types[table] = "GDB"

        self.table_types = table_types

    def find_tables_fields_values(self):

        table_records_temp = {}
        # Go through each table entered
        for table in self.tables:
            desc = arcpy.Describe(str(table).replace("'", ""))  # Name of the table
            arcpy.AddMessage(desc.baseName)

            # If the name of the table is one of the tables in the iter_tables list
            if desc.baseName in self.iter_tables:
                record_count = 0
                record_updates = 0
                relevant_fields = 0
                non_fema_fields = 0

                # Get a list of fields
                field_list = arcpy.ListFields(str(table).replace("'", ""))
                f_str_list = [f.name for f in field_list]
                existing_fields_dict = {}
                for i, fname in enumerate(f_str_list):
                    existing_fields_dict[fname] = i
                arcpy.AddMessage(f' Existing Fields: {existing_fields_dict}')

                # Go through each row in the table
                # Create an update cursor
                cursor = arcpy.da.SearchCursor(str(table).replace("'", ""), f_str_list)
                for row in cursor:
                    record_count += 1
                    if self.table_types[table] == "GDB":
                        oid = row[existing_fields_dict['OBJECTID']]
                    else:
                        oid = row[existing_fields_dict['FID']]
                    for field in field_list:
                        update = True
                        value = row[existing_fields_dict[field.name]]  # Value of the current field in the current row
                        # If it's an applicable field and not in the skip fields list
                        if field.name in self.app_Dict[desc.baseName] and field.name not in self.skip_fields:
                            relevant_fields += 1
                            correct_nulls = (None, "9/9/9999", '-9999')
                            if field.type == 'String' and value in ["", " ", None]:
                                if value not in correct_nulls:
                                    record_updates += 1
                                    new_value = None
                                else:
                                    new_value = value
                            elif field.type == 'Date' and value in ["", " ", None]:
                                if value not in correct_nulls:
                                    record_updates += 1
                                    new_value = "9/9/9999"
                                else:
                                    new_value = value
                            elif field.type == 'Double' and value in ["", " ", None]:
                                if value not in correct_nulls:
                                    record_updates += 1
                                    new_value = '-9999'
                                else:
                                    new_value = value
                            else:
                                new_value = value
                                update = False
                        # If it's a required field and not in the skip fields list
                        elif field.name not in self.skip_fields:
                            non_fema_fields += 1
                            correct_nulls = ('U', "8/8/8888", '-8888', "NP", -8888)
                            if field.type == 'String' and value in ["", " ", None]:
                                if value not in correct_nulls:
                                    record_updates += 1
                                    if field.length == 1:  # True/false fields
                                        new_value = "U"
                                    else:
                                        new_value = "NP"
                                else:
                                    new_value = value
                            elif field.type == 'Date' and value in ["", " ", None]:
                                if value not in correct_nulls:
                                    record_updates += 1
                                    new_value = "8/8/8888"
                                else:
                                    new_value = value
                            elif field.type == 'Double' and value in ["", " ", None]:
                                if value not in correct_nulls:
                                    record_updates += 1
                                    new_value = '-8888'
                                else:
                                    new_value = value
                            else:
                                new_value = value
                                update = False
                        else:
                            update = False
                            new_value = value

                        if table not in table_records_temp:
                            table_records_temp[table] = {}
                        if field.name not in table_records_temp[table]:
                            table_records_temp[table][field.name] = {}
                        if oid not in table_records_temp[table][field.name]:
                            table_records_temp[table][field.name][oid] = {}
                        table_records_temp[table][field.name][oid] = {'Update': update,
                                                                      'Old Value': value, 'New Value': new_value}
                del cursor
                if table not in table_records_temp:
                    table_records_temp[table] = {}
                table_records_temp[table]['Update Features'] = record_updates
                arcpy.AddMessage(f'{table}:\n  - {record_updates}')
                table_records_temp[table]['Input Features'] = record_count
                table_records_temp[table]['FEMA Field Count'] = relevant_fields
                table_records_temp[table]['Other Fields'] = non_fema_fields
        self.table_records = table_records_temp

    def update_nulls(self):

        non_field_entries = ['Update Features', 'Input Features', 'FEMA Field Count', 'Other Fields']
        for table in self.tables:
            number_updates = self.table_records[table]['Update Features']
            if number_updates > 0:
                desc = arcpy.Describe(str(table).replace("'", ""))  # Name of the table
                # Start an edit session
                # with arcpy.da.Editor(CalculateNull.get_geodatabase_path(desc.path)):
                table_dictionary = self.table_records[table]
                update_fields = []
                for key, dict_values in table_dictionary.items():
                    if key not in non_field_entries:
                        update_fields.append(key)

                row_dict = {}
                field_lookup = {}
                for i, fname in enumerate(update_fields):
                    row_dict[i] = fname
                    field_lookup[fname] = i
                arcpy.AddMessage(f'Row Dict: {row_dict}')
                arcpy.AddMessage(f'Field Lookup: {field_lookup}')
                with arcpy.da.UpdateCursor(table, update_fields) as update_cursor:
                    for i in range(len(update_fields)):
                        fname = row_dict[i]
                        for urow in update_cursor:
                            if self.table_types[table] == "GDB":
                                oid = urow[field_lookup['OBJECTID']]
                            else:
                                oid = urow[field_lookup['FID']]
                            if self.table_records[table][fname][oid]['Update']:
                                new_value = self.table_records[table][oid]['New Value']

                                row.setValue(fname, new_value)

                            # Update the row
                            update_cursor.updateRow(urow)
                del update_cursor

    @staticmethod
    def get_geodatabase_path(input_table):
        """Return the Geodatabase path from the input table or feature class.
      :param input_table: path to the input table or feature class
      """
        workspace = os.path.dirname(input_table)
        if [any(ext) for ext in ('.gdb', '.mdb', '.sde') if ext in os.path.splitext(workspace)]:
            return workspace
        else:
            return os.path.dirname(workspace)

    def run_calcnull(self):

        arcpy.AddMessage('Starting to iterate through tables...')
        self.input_type()
        self.find_tables_fields_values()
        arcpy.AddMessage(f'Finished finding stuff in {len(self.tables)} tables')

        for table, dictionaries in self.table_records.items():
            if dictionaries['Update Features'] > 0:
                arcpy.AddMessage(f"{table}:\n  - Updates: {dictionaries['Update Features']}")

        self.update_nulls()
        arcpy.AddMessage(f'Finished updating tables')


if __name__ == '__main__':
    if sys.argv[1] and sys.argv[1] != '#':
        table_list = sorted(sys.argv[1].split(";"))
        calc_null = CalculateNull(table_list)
        calc_null.run_calcnull()
