"""
cti_bca.py

This is the primary module of the benefit cost analysis tool. This module reads input files, calls other modules and generates output files.

"""
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from datetime import datetime
from itertools import product
import time
import project_code
from project_code.fuel_prices_aeo import GetFuelPrices
from project_code.fleet import Fleet
from project_code.vehicle import Vehicle, regClassID, fuelTypeID
from project_code.direct_cost import DirectCost
from project_code.indirect_cost import IndirectCost, IndirectCostScalers, markup_factors
from project_code.operating_cost import DEFCost, ORVRadjust, FuelCost, RepairAndMaintenanceCost
from project_code.discounting import DiscountValues
from project_code.group_metrics import GroupMetrics
from project_code.calc_deltas import CalcDeltas
from project_code.emission_cost import EmissionCost
from project_code.weighted_results import WeightedResult
from project_code.doc_tables import DocTables
from project_code.estimated_age import EstimatedAge, EstimatedAge2
from project_code.figures import CreateFigures
from project_code.data_table import DataTable
import project_code.general_functions as gen_fxns


# def inputs_filenames(input_files_pathlist):
#     """
#     :param input_files_pathlist: A list of those input files that are not modified in code.
#     :type input_files_pathlist: List - currently hardcoded.
#     :return: A list of input file paths - these will be copied directly to the output folder so that inputs and outputs end up bundled together in the output folder.
#     """
#     _filename_list = [PurePath(path).name for path in input_files_pathlist]
#     return _filename_list
# 
# 
# def reshape_df(df, value_variable_list, cols_to_melt, melted_header, new_column_name):
#     """
# 
#     :param df: Data to melt.
#     :type df: DataFrame
#     :param value_variable_list: Column(s) to use as identifier variables.
#     :type value_variable_list: List
#     :param cols_to_melt: Column(s) to unpivot (melt).
#     :type cols_to_melt: List - this is a list of columns determined in code that are to be melted.
#     :param melted_header: The header for the column to be populated with the cols_to_melt list.
#     :type melted_header: String
#     :param new_column_name: Name to use for the ‘Value’ column.
#     :type new_column_name: String
#     :return: A new DataFrame in long and narrow shape rather than the passed short and wide shape.
#     """
#     df = df.melt(id_vars=value_variable_list,
#                  value_vars=cols_to_melt, var_name=melted_header,
#                  value_name=new_column_name)
#     return df
# 
# 
# def convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args):
#     """
# 
#     This function converts dollars into a consistent dollar basis as set in the Inputs workbook.
#     :param df: The passed DataFrame containing costs to convert.
#     :param deflators: A dictionary of gdp price deflators and adjustments to be multiplied by costs.
#     :param dollar_basis: The dollar basis of the analysis.
#     :param args: Metrics to be converted to dollar_basis dollars.
#     :return: The passed DataFrame with metric dollar values converted to dollar_basis dollars.
#     """
#     dollar_years = pd.Series(pd.DataFrame(df.loc[df['DollarBasis'] > 1])['DollarBasis'].unique())
#     for year in dollar_years:
#         for arg in args:
#             df.loc[df['DollarBasis'] == year, arg] = df[arg] * deflators[year]['adjustment']
#         df.loc[df['DollarBasis'] == year, 'DollarBasis'] = dollar_basis
#     return df
# #
# #
# # def weighted_result(df, metric, weightby_metric, veh, year_metric, year_list, max_age_included):
# #     """
# #
# #     :param df: DataFrame containing values to be weighted.
# #     :param metric: The specific metric (or series) of data to be weighted.
# #     :param weightby_metric:  The metric by which the data is being weighted.
# #     :param veh: The specific vehicle (tuple) for which weighting is requested.
# #     :param year_metric:  "yearID" or "modelYearID"
# #     :param year_list: List of years for which weighted results are requested.
# #     :param max_age_included: The age through which data is to be weighted (i.e., can be less than full life)
# #     :return: DataFrame containing weighted results for the passed vehicle.
# #     """
# #     if len(veh) == 3:
# #         veh_id = 'alt_rc_ft'
# #     else:
# #         veh_id = 'alt_st_rc_ft'
# #     weighted_results = dict()
# #     for year in year_list:
# #         df_temp = pd.DataFrame(df.loc[(df[veh_id] == veh) & (df[year_metric] == year) & (df['ageID'] <= max_age_included), :])
# #         weighted_value = (df_temp[metric] * df_temp[weightby_metric]).sum() / df_temp[weightby_metric].sum()
# #         weighted_results[year] = weighted_value
# #     return weighted_results
# 
# 
# def round_metrics(df, metrics, round_by):
#     """
# 
#     :param df: DataFrame containing data to be rounded.
#     :param metrics: List of metrics within the passed DataFrame for which rounding is requested.
#     :param round_by: A value entered via the BCA_Inputs sheet contained in the inputs folder that sets the level of rounding.
#     :return: The passed DataFrame with 'metrics' rounded by 'round_by'
#     """
#     df[metrics] = df[metrics].round(round_by)
#     return df
# 
# 
# def get_file_datetime(list_of_files):
#     file_datetime = pd.DataFrame()
#     file_datetime.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
#     file_datetime.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])
#     return file_datetime
# 
# 
# def cols_for_df(source_df, metrics):
#     return_df = pd.DataFrame(source_df, columns=metrics)
#     return return_df
# 
# 
# def read_input_files(path_inputs, input_file, col_list, idx_col=None):
#     try:
#         pd.read_csv(path_inputs / f'{input_file}', usecols=col_list, index_col=idx_col)
#         print(f'File {input_file}.......FOUND.')
#         df_return = pd.read_csv(path_inputs / f'{input_file}', usecols=col_list, index_col=idx_col)
#     except FileNotFoundError:
#         print(f'File {input_file}......NOT FOUND in {path_inputs} folder.')
#         sys.exit()
#     return df_return
# 
# 
# def get_common_metrics(df_left, df_right):
#     cols_left = [col for col in df_left.columns if col in df_right.columns]
#     cols_right = [col for col in df_right.columns if col in df_left.columns]
#     try:
#         cols_left != []
#         cols_right != []
#         return cols_left
#     except:
#         print(f'column misalighnment in {df_left} - {df_right} merge.')
#         return


def main():
    """The main script."""
    # path_code = Path(__file__).parent
    path_project = Path.cwd()

    # TODO generate some test of input files - are they present, are inputs in the right formats, etc.?
    # TODO update introduction/other documentation per recent changes (0.22.0 thru 0.22.2)
    # first, set the output files desired for QA/QC work
    test_run = input('Use full CTI BCA inputs (<ENTER>) or use test inputs (t)?\n')
    if test_run == 't':
        path_inputs = path_project / 'test/inputs'
        path_outputs = path_project / 'test/outputs'
    else:
        path_inputs = path_project / 'inputs'
        path_outputs = path_project / 'outputs'
    run_folder_identifier = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
    run_folder_identifier = run_folder_identifier if run_folder_identifier != '' else 'BCA-Results'
    create_all_files = input('Create all output files? (y)es or (n)o?\n')
    start_time = time.time()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    print(f'\nStart date and time:  {start_time_readable}')
    print(f'\nCTI BCA tool version: {project_code.__version__}')

    print("\nReading input files....")
    start_time_read = time.time()
    input_files_df = pd.read_csv(path_inputs / 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    input_files_dict = input_files_df.to_dict('index')

    bca_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['bca_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)
    regclass_costs = gen_fxns.read_input_files(path_inputs, input_files_dict['regclass_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
    regclass_learningscalers = gen_fxns.read_input_files(path_inputs, input_files_dict['regclass_learningscalers']['UserEntry.csv'], lambda x: 'Notes' not in x)
    markups = gen_fxns.read_input_files(path_inputs, input_files_dict['markups']['UserEntry.csv'], lambda x: 'Notes' not in x)
    warranty_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['warranty_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
    usefullife_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['usefullife_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
    moves = gen_fxns.read_input_files(path_inputs, input_files_dict['moves']['UserEntry.csv'], lambda x: 'Notes' not in x)
    moves_adjustments = gen_fxns.read_input_files(path_inputs, input_files_dict['moves_adjustments']['UserEntry.csv'], lambda x: 'Notes' not in x)
    options = gen_fxns.read_input_files(path_inputs, input_files_dict['options']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)
    options_dict = options.to_dict('index')
    def_doserate_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['def_doserate_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
    def_prices = gen_fxns.read_input_files(path_inputs, input_files_dict['def_prices']['UserEntry.csv'], lambda x: 'Notes' not in x)
    orvr_fuelchanges = gen_fxns.read_input_files(path_inputs, input_files_dict['orvr_fuelchanges']['UserEntry.csv'], lambda x: 'Notes' not in x)
    repair_and_maintenance = gen_fxns.read_input_files(path_inputs, input_files_dict['repair_and_maintenance']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)
    gdp_deflators = gen_fxns.read_input_files(path_inputs, input_files_dict['gdp_deflators']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)
    gdp_deflators.insert(len(gdp_deflators.columns), 'adjustment', 0)  # adjustment values are filled below

    input_files_pathlist = [path_inputs / item for item in pd.Series(input_files_df['UserEntry.csv'])]
    input_files_pathlist.append(path_inputs / 'Input_Files.csv')

    elapsed_time_read = time.time() - start_time_read

    # get necessary inputs from the bca_inputs_file
    print("\nDoing the work....")
    start_time_calcs = time.time()
    aeo_case = bca_inputs.at['aeo_fuel_price_case', 'UserEntry']
    discrate_social_low = pd.to_numeric(bca_inputs.at['discrate_social_low', 'UserEntry'])
    discrate_social_high = pd.to_numeric(bca_inputs.at['discrate_social_high', 'UserEntry'])
    discount_to_yearID = pd.to_numeric(bca_inputs.at['discount_to_yearID', 'UserEntry'])
    costs_start = bca_inputs.at['costs_start', 'UserEntry']
    learning_rate = pd.to_numeric(bca_inputs.at['learning_rate', 'UserEntry'])
    dollar_basis_analysis = int(bca_inputs.at['dollar_basis_analysis', 'UserEntry'])
    warranty_vmt_share = pd.to_numeric(bca_inputs.at['warranty_vmt_share', 'UserEntry'])
    r_and_d_vmt_share = pd.to_numeric(bca_inputs.at['r_and_d_vmt_share', 'UserEntry'])
    indirect_cost_scaling_metric = bca_inputs.at['scale_indirect_costs_by', 'UserEntry']
    calc_pollution_effects = bca_inputs.at['calculate_pollution_effects', 'UserEntry']
    round_costs_by = pd.to_numeric(bca_inputs.at['round_costs_by', 'UserEntry'])
    def_gallons_perTonNOxReduction = pd.to_numeric(bca_inputs.at['def_gallons_per_ton_nox_reduction', 'UserEntry'])
    weighted_operating_cost_years = bca_inputs.at['weighted_operating_cost_years', 'UserEntry']
    weighted_operating_cost_years = weighted_operating_cost_years.split(',')
    for i, v in enumerate(weighted_operating_cost_years):
        weighted_operating_cost_years[i] = pd.to_numeric(weighted_operating_cost_years[i])
    max_age_included = pd.to_numeric(bca_inputs.at['weighted_operating_cost_thru_ageID', 'UserEntry'])
    techcost_summary_years = bca_inputs.at['techcost_summary_years', 'UserEntry']
    techcost_summary_years = techcost_summary_years.split(',')
    for i, v in enumerate(techcost_summary_years):
        techcost_summary_years[i] = pd.to_numeric(techcost_summary_years[i])
    bca_summary_years = bca_inputs.at['bca_summary_years', 'UserEntry']
    bca_summary_years = bca_summary_years.split(',')
    for i, v in enumerate(bca_summary_years):
        bca_summary_years[i] = pd.to_numeric(bca_summary_years[i])
    generate_emissionrepair_cpm_figures = bca_inputs.at['generate_emissionrepair_cpm_figures', 'UserEntry']
    generate_BCA_ArgsByOption_figures = bca_inputs.at['generate_BCA_ArgsByOption_figures', 'UserEntry']
    generate_BCA_ArgByOptions_figures = bca_inputs.at['generate_BCA_ArgByOptions_figures', 'UserEntry']

    # how many alternatives are there? But first, be sure that optionID is the header for optionID.
    if 'Alternative' in moves.columns.tolist():
        moves.rename(columns={'Alternative': 'optionID'}, inplace=True)
    number_alts = len(moves['optionID'].unique())

    # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
    gdp_deflators = gdp_deflators.to_dict('index')
    for key in gdp_deflators:
        gdp_deflators[key]['adjustment'] = gdp_deflators[dollar_basis_analysis]['factor'] / gdp_deflators[key]['factor']
    cost_steps = [col for col in regclass_costs.columns if '20' in col]
    gen_fxns.convert_dollars_to_analysis_basis(regclass_costs, gdp_deflators, dollar_basis_analysis, [step for step in cost_steps])
    gen_fxns.convert_dollars_to_analysis_basis(def_prices, gdp_deflators, dollar_basis_analysis, 'DEF_USDperGal')
    gen_fxns.convert_dollars_to_analysis_basis(repair_and_maintenance, gdp_deflators, dollar_basis_analysis, 'Value')

    # now get specific inputs from repair_and_maintenance
    inwarranty_repair_and_maintenance_owner_cpm = repair_and_maintenance.at['in-warranty_R&M_Owner_CPM', 'Value']
    atusefullife_repair_and_maintenance_owner_cpm = repair_and_maintenance.at['at-usefullife_R&M_Owner_CPM', 'Value']
    mile_increase_beyond_usefullife = repair_and_maintenance.at['mile_increase_beyond_usefullife', 'Value']
    max_repair_and_maintenance_CPM = repair_and_maintenance.at['max_R&M_Owner_CPM', 'Value']
    typical_vmt_thru_age = repair_and_maintenance.at['typical_vmt_thru_ageID', 'Value']
    emission_repair_share = repair_and_maintenance.at['emission_repair_share', 'Value']
    metrics_repair_and_maint_dict = {'inwarranty_repair_and_maintenance_owner_cpm': inwarranty_repair_and_maintenance_owner_cpm,
                                     'atusefullife_repair_and_maintenance_owner_cpm': atusefullife_repair_and_maintenance_owner_cpm,
                                     'mile_increase_beyond_usefullife': mile_increase_beyond_usefullife,
                                     'max_repair_and_maintenance_cpm': max_repair_and_maintenance_CPM,
                                     'typical_vmt_thru_ageID': typical_vmt_thru_age,
                                     'emission_repair_share': emission_repair_share}

    # get the fuel price inputs
    fuel_prices_obj = GetFuelPrices(path_project, aeo_case, 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()

    # Calculate the Indirect Cost scalers based on the warranty_inputs and usefullife_inputs
    warranty_scalers = IndirectCostScalers(warranty_inputs, 'Warranty', indirect_cost_scaling_metric)
    warranty_scalers = warranty_scalers.calc_scalers_absolute()
    usefullife_scalers = IndirectCostScalers(usefullife_inputs, 'RnD', indirect_cost_scaling_metric)
    usefullife_scalers = usefullife_scalers.calc_scalers_relative()
    markup_scalers = pd.concat([warranty_scalers, usefullife_scalers], ignore_index=True, axis=0)
    markup_scalers.reset_index(drop=True, inplace=True)

    # Now, reshape some of the inputs for easier use
    warranty_miles_reshaped = gen_fxns.reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                  [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Miles')
    warranty_age_reshaped = gen_fxns.reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Age')
    usefullife_miles_reshaped = gen_fxns.reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                    [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Miles')
    usefullife_age_reshaped = gen_fxns.reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                  [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Age')
    markup_scalers_reshaped = gen_fxns.reshape_df(markup_scalers, ['optionID', 'regClassID', 'fuelTypeID', 'Markup_Factor'],
                                                  [col for col in markup_scalers.columns if '20' in col], 'yearID', 'Value')
    for df in [warranty_miles_reshaped, warranty_age_reshaped, usefullife_miles_reshaped, usefullife_age_reshaped]:
        df['modelYearID'] = pd.to_numeric(df['modelYearID'])
        df.insert(0, 'alt_rc_ft', pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID'])))
    # warranty_miles_reshaped['modelYearID'] = pd.to_numeric(warranty_miles_reshaped['modelYearID'])
    # warranty_age_reshaped['modelYearID'] = pd.to_numeric(warranty_age_reshaped['modelYearID'])
    # usefullife_miles_reshaped['modelYearID'] = pd.to_numeric(usefullife_miles_reshaped['modelYearID'])
    # usefullife_age_reshaped['modelYearID'] = pd.to_numeric(usefullife_age_reshaped['modelYearID'])
    markup_scalers_reshaped['yearID'] = pd.to_numeric(markup_scalers_reshaped['yearID'])

    # read and reshape criteria costs if pollution effects are being calculated
    if calc_pollution_effects == 'Y':
        criteria_emission_costs = gen_fxns.read_input_files(path_inputs, input_files_dict['criteria_emission_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
        tailpipe_pollutant_costs_list = [col for col in criteria_emission_costs.columns if 'onroad' in col]
        criteria_emission_costs_reshaped = gen_fxns.reshape_df(criteria_emission_costs, ['yearID', 'MortalityEstimate', 'DR', 'fuelTypeID', 'DollarBasis'],
                                                               tailpipe_pollutant_costs_list, 'Pollutant_source', 'USDpUSton')
        criteria_emission_costs_reshaped.insert(1, 'Key', '')
        criteria_emission_costs_reshaped['Key'] = criteria_emission_costs_reshaped['Pollutant_source'] + '_' \
                                                  + criteria_emission_costs_reshaped['MortalityEstimate'] + '_' \
                                                  + criteria_emission_costs_reshaped['DR'].map(str)

    # add the identifier metrics, alt_rc_ft and alt_st_rc_ft, to specific DataFrames
    for df in [regclass_costs, regclass_learningscalers, moves, moves_adjustments]:
        df = Fleet(df).define_bca_regclass()
    moves = Fleet(moves).define_bca_sourcetype()

    # adjust MOVES VPOP/VMT/Gallons to reflect what's included in CTI (excluding what's not in CTI)
    moves_adjusted = Fleet(moves).adjust_moves(moves_adjustments)  # adjust (41, 2) to be engine cert only
    moves_adjusted = moves_adjusted.loc[(moves_adjusted['regClassID'] != 41) | (moves_adjusted['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
    moves_adjusted = moves_adjusted.loc[moves_adjusted['regClassID'] != 49, :]  # eliminate Gliders
    moves_adjusted = moves_adjusted.loc[moves_adjusted['fuelTypeID'] != 5, :]  # eliminate E85
    moves_adjusted = moves_adjusted.loc[moves_adjusted['regClassID'] >= 41, :]  # eliminate non-CTI regclasses
    cols = [col for col in moves_adjusted.columns if 'PM25' in col]
    moves_adjusted.insert(len(moves_adjusted.columns), 'PM25_onroad', moves_adjusted[cols].sum(axis=1))  # sum PM25 metrics
    moves_adjusted.insert(len(moves_adjusted.columns), 'ageID', moves_adjusted['yearID'] - moves_adjusted['modelYearID'])
    moves_adjusted.rename(columns={'NOx_UStons': 'NOx_onroad'}, inplace=True)
    # determine the earliest model year for which MOVES runs have ageID=0 data (i.e., where does BCA start?)
    year_min = moves_adjusted.loc[moves_adjusted['ageID'] == 0, 'yearID'].min()
    moves_adjusted = pd.DataFrame(moves_adjusted.loc[moves_adjusted['modelYearID'] >= year_min, :])
    moves_adjusted.reset_index(drop=True, inplace=True)
    moves_adjusted.insert(0, 'static_id', range(0, len(moves_adjusted)))

    # create some specific data tables
    # regclass_header = ['static_id', 'optionID', 'yearID', 'modelYearID', 'ageID', 'alt_rc_ft']
    # sourcetype_header = ['static_id', 'optionID', 'yearID', 'modelYearID', 'ageID', 'alt_st_rc_ft', 'alt_rc_ft']

    regclass_vpop = DataTable(moves_adjusted, 'static_id', 'optionID', 'yearID', 'modelYearID', 'ageID', 'alt_rc_ft', 'VPOP').data_table()
    sourcetype_vpop = DataTable(moves_adjusted, 'static_id', 'optionID', 'yearID', 'modelYearID', 'ageID',
                                'sourceTypeID', 'regClassID', 'fuelTypeID', 'alt_st_rc_ft', 'alt_rc_ft', 'VPOP').data_table()
    sourcetype_criteria = DataTable(moves_adjusted, 'static_id', 'optionID', 'yearID', 'modelYearID', 'ageID',
                                    'alt_st_rc_ft', 'fuelTypeID', 'THC_UStons', 'PM25_onroad', 'NOx_onroad').data_table()
    sourcetype_gallons = DataTable(moves_adjusted, 'static_id', 'optionID', 'yearID', 'modelYearID', 'ageID', 'alt_st_rc_ft', 'Gallons').data_table()
    sourcetype_vmt = DataTable(moves_adjusted, 'static_id', 'optionID', 'yearID', 'modelYearID', 'ageID', 'alt_st_rc_ft', 'alt_rc_ft', 'VMT').data_table()
    sourcetype_per_veh = DataTable(moves_adjusted, 'static_id', 'optionID', 'yearID', 'modelYearID', 'ageID', 'alt_st_rc_ft', 'alt_rc_ft').data_table()

    regclass_sales = regclass_vpop.loc[regclass_vpop['ageID'] == 0, :].groupby(by=['optionID', 'yearID', 'modelYearID', 'ageID', 'alt_rc_ft'],
                                                                               as_index=False).sum()
    regclass_sales.drop(columns='static_id', inplace=True) # static_id is tied to sourcetype-level info, once summed in regclass_sales, it is no longer relevant
    reductions = CalcDeltas(
        sourcetype_criteria, len(sourcetype_criteria['optionID'].unique()), ['THC_UStons', 'PM25_onroad', 'NOx_onroad']) \
        .calc_delta_and_keep_alt_id()
    sourcetype_criteria = sourcetype_criteria.merge(reductions, on=gen_fxns.get_common_metrics(sourcetype_criteria, reductions), how='left')
    # on=['optionID', 'yearID', 'modelYearID', 'ageID', 'alt_st_rc_ft', 'fuelTypeID'], how='left')
    sourcetype_per_veh.insert(len(sourcetype_per_veh.columns), 'VMT_AvgPerVeh', sourcetype_vmt['VMT'] / sourcetype_vpop['VPOP'])
    sourcetype_per_veh = sourcetype_per_veh.join(GroupMetrics(sourcetype_per_veh, ['alt_st_rc_ft', 'modelYearID']).group_cumsum(['VMT_AvgPerVeh']))
    sourcetype_per_veh.insert(len(sourcetype_per_veh.columns), 'MPG_AvgPerVeh', sourcetype_vmt['VMT'] / sourcetype_gallons['Gallons'])

    # cols_to_drop = [col for col in moves_adjusted.columns if 'CO_UStons' in col or 'exhaust' in col or 'brakewear' in col
    #                 or 'tirewear' in col or 'VOC' in col or 'CO2' in col or 'Energy' in col]
    # moves_adjusted = moves_adjusted.drop(columns=cols_to_drop)
    # moves_adjusted.reset_index(drop=True, inplace=True)
    #
    # # add VMT/vehicle & Gallons/mile metrics to moves dataframe
    # moves_adjusted.insert(len(moves_adjusted.columns), 'VMT_AvgPerVeh', moves_adjusted['VMT'] / moves_adjusted['VPOP'])
    # moves_adjusted = moves_adjusted.join(GroupMetrics(moves_adjusted,
    #                                                   ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'])
    #                                      .group_cumsum(['VMT_AvgPerVeh']))
    # # moves_adjusted.rename({'VPOP_CumSum': 'VPOP_CumSum_by_alt_rc_ft'}, inplace=True, axis=1)
    # moves_adjusted.insert(len(moves_adjusted.columns), 'MPG_AvgPerVeh', moves_adjusted['VMT'] / moves_adjusted['Gallons'])
    # moves_adjusted_cols = moves_adjusted.columns.tolist()

    # pass moves thru Fleet.sales to get sales (population ageID=0) of everything in the moves runs by both sourcetype and by regclass
    # sales_moves = Fleet(moves_adjusted).sales()

    # # determine the earliest model year for which MOVES runs have ageID=0 data (i.e., where does BCA start?)
    # year_min = sales_moves.loc[sales_moves['ageID'] == 0, 'yearID'].min()

    # calculate the direct mfg costs by passing vehicles, package costs/pens, sales and learning metrics thru the DirectCost class
    print('\nWorking on tech package costs....')
    regclass_costs_dict = dict()
    regclass_sales_dict = dict()  # this will provide sales by regclass-fueltype (rather than sourcetype-regclass-fueltype) which is needed for learning effects
    alt_rc_ft_vehicles = dict()
    for step in cost_steps:
        # regclass_sales[step] = Fleet(moves_adjusted.loc[moves_adjusted['modelYearID'] >= pd.to_numeric(step)]).sales_by_alt_rc_ft()
        regclass_sales_dict[step] = pd.DataFrame(regclass_sales.loc[regclass_sales['modelYearID'] >= pd.to_numeric(step), :])
        alt_rc_ft_vehicles[step] = pd.Series(regclass_sales_dict[step]['alt_rc_ft'].unique())
    # Apply learning to direct costs
    for step, veh in product(cost_steps, alt_rc_ft_vehicles[step]):
        direct_costs_obj = DirectCost(veh, step, regclass_costs, regclass_learningscalers, regclass_sales_dict[step])
        print(direct_costs_obj)
        regclass_costs_dict[veh, step] = direct_costs_obj.pkg_cost_regclass_withlearning(learning_rate)

    # Now merge the steps into a single DataFrame so that the costs can be summed into a single cost series. An outer merge is used in case there are different vehicles (unlikely).
    alt_rc_ft_vehicles = pd.Series(regclass_sales['alt_rc_ft'].unique())
    for veh in alt_rc_ft_vehicles:
        regclass_costs_dict[veh] = regclass_costs_dict[veh, cost_steps[0]].copy()
        regclass_costs_dict[veh][f'DirectCost_AvgPerVeh_{cost_steps[0]}'].fillna(0, inplace=True)
        for step_number in range(1, len(cost_steps)):  # this brings in costs from subsequent steps
            step = cost_steps[step_number]
            # cols_on_which_to_merge = [col for col in regclass_costs_dict[veh, step] if f'{step}' not in col]
            regclass_costs_dict[veh] = regclass_costs_dict[veh]\
                .merge(regclass_costs_dict[veh, step],
                       on=gen_fxns.get_common_metrics(regclass_costs_dict[veh], regclass_costs_dict[veh, step], ignore=['static_id']),
                       how='outer')
            regclass_costs_dict[veh][f'DirectCost_AvgPerVeh_{step}'].fillna(0, inplace=True)
            # regclass_costs_dict[veh].insert(1, 'Vehicle_Name_RC', Vehicle(veh).name_regclass())
    # Since subsequent steps are incremental to prior steps, now sum the steps.
    for veh in alt_rc_ft_vehicles:
        regclass_costs_dict[veh].insert(len(regclass_costs_dict[veh].columns), 'DirectCost_AvgPerVeh', 0)
        # regclass_costs_dict[veh].insert(len(regclass_costs_dict[veh].columns), 'DirectCost_TotalCost', 0)
        for step in cost_steps:
            regclass_costs_dict[veh]['DirectCost_AvgPerVeh'] += regclass_costs_dict[veh][f'DirectCost_AvgPerVeh_{step}']

    # Since package costs for NoAction are absolute and for other options they are incremental to NoAction, add in NoAction costs
    alt_rc_ft_vehicles_actions = pd.Series(regclass_sales.loc[regclass_sales['optionID'] > 0, 'alt_rc_ft'].unique())
    for veh in alt_rc_ft_vehicles_actions:
        regclass_costs_dict[veh]['DirectCost_AvgPerVeh'] = regclass_costs_dict[veh]['DirectCost_AvgPerVeh'] + \
                                                           regclass_costs_dict[(0, veh[1], veh[2])]['DirectCost_AvgPerVeh']

    # merge markups and scalers into direct costs and calculate indirect costs
    regclass_costs_df = pd.DataFrame()
    for veh in alt_rc_ft_vehicles:
        merge_object = IndirectCost(regclass_costs_dict[veh])
        regclass_costs_dict[veh] = merge_object.get_markups(markups.loc[markups['fuelTypeID'] == veh[2], :])
        regclass_costs_dict[veh] = merge_object.merge_markup_scalers(markup_scalers_reshaped.loc[(markup_scalers_reshaped['optionID'] == veh[0])
                                                                                                 & (markup_scalers_reshaped['regClassID'] == veh[1])
                                                                                                 & (markup_scalers_reshaped['fuelTypeID'] == veh[2]), :],
                                                                     'yearID')
        # regclass_costs_dict[veh] = merge_object.merge_markups_and_directcosts(markups, 'fuelTypeID')
        # regclass_costs_dict[veh] = merge_object.merge_markup_scalers(markup_scalers_reshaped, 'optionID', 'regClassID', 'fuelTypeID', 'yearID')
        regclass_costs_dict[veh].ffill(inplace=True)
        regclass_costs_dict[veh].reset_index(drop=True, inplace=True)
        indirect_cost_obj = IndirectCost(regclass_costs_dict[veh])
        print(f'IndirectCost: Vehicle {veh}')
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_scaled(regclass_costs_dict[veh], 'Warranty', warranty_vmt_share)
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_scaled(regclass_costs_dict[veh], 'RnD', r_and_d_vmt_share)
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_unscaled(regclass_costs_dict[veh])
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_sum()
        regclass_costs_dict[veh].insert(len(regclass_costs_dict[veh].columns),
                                        'TechCost_AvgPerVeh',
                                        regclass_costs_dict[veh]['DirectCost_AvgPerVeh'] + regclass_costs_dict[veh]['IndirectCost_AvgPerVeh'])
        # regclass_costs_dict[veh].insert(len(regclass_costs_dict[veh].columns),
        #                                 'TechCost_TotalCost',
        #                                 regclass_costs_dict[veh]['DirectCost_TotalCost'] + regclass_costs_dict[veh]['IndirectCost_TotalCost'])
        # drop VPOP from regclass_costs since it's VPOP by regclass
        regclass_costs_dict[veh].drop(columns=['VPOP'], inplace=True)
        regclass_costs_df = pd.concat([regclass_costs_df, regclass_costs_dict[veh]], axis=0, ignore_index=True)

    # To get costs on a sourcetype basis, create a sourcetype_tech_costs DataFrame into which to merge the regclass_costs
    sourcetype_tech_costs = sourcetype_vpop.merge(regclass_costs_df, on=gen_fxns.get_common_metrics(sourcetype_vpop, regclass_costs_df), how='left', sort='False')
    # sourcetype_tech_costs = pd.DataFrame(moves_adjusted.loc[moves_adjusted['modelYearID'] >= year_min])
    # sourcetype_tech_costs.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    # sourcetype_tech_costs.reset_index(drop=True, inplace=True)
    # # sourcetype_sales = Fleet(sourcetype_tech_costs).sales()
    #
    # sourcetype_tech_costs = sourcetype_tech_costs.merge(regclass_costs_df,
    #                                           on=['optionID', 'regClassID', 'fuelTypeID', 'alt_rc_ft', 'yearID', 'modelYearID', 'ageID'],
    #                                           how='left', sort='False')
    sourcetype_tech_costs.loc[sourcetype_tech_costs['VPOP'] == 0, 'DirectCost_AvgPerVeh'] = 0
    for metric in [item for item in sourcetype_tech_costs.columns if 'Cost_AvgPerVeh' in item]:
        sourcetype_tech_costs[f'{metric}'].fillna(0, inplace=True)
    for metric in markup_factors + ['Direct', 'Indirect', 'Tech']:
        sourcetype_tech_costs.insert(len(sourcetype_tech_costs.columns),
                                f'{metric}Cost_TotalCost',
                                sourcetype_tech_costs[[f'{metric}Cost_AvgPerVeh', 'VPOP']].product(axis=1))
    # sourcetype_tech_costs['DirectCost_AvgPerVeh'].fillna(0, inplace=True)
    # sourcetype_tech_costs['DirectCost_TotalCost'] = sourcetype_tech_costs[['DirectCost_AvgPerVeh', 'VPOP']].product(axis=1)
    sourcetype_tech_costs.reset_index(drop=True, inplace=True)
    techcost_metrics_to_discount = [col for col in sourcetype_tech_costs.columns if 'Cost' in col]

    # create DataFrame into which the individual DataFrames in the above dictionaries can be appended
    # directcost_regclass = pd.DataFrame()
    # for veh in alt_rc_ft_vehicles:
    #     directcost_regclass = pd.concat([directcost_regclass, regclass_costs_dict[veh]], axis=0, ignore_index=True)

    # fleet_bca created here - the fleet of relevance to the bca, so >= starting MY
    # fleet_bca = moves_adjusted.copy()
    # fleet_bca = pd.DataFrame(fleet_bca.loc[fleet_bca['modelYearID'] >= year_min])
    # fleet_bca.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    # fleet_bca.reset_index(drop=True, inplace=True)
    # sales_bca = Fleet(fleet_bca).sales()

    # create some metric lists for DataFrames that follow
    # metrics_directcost_bca = ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'alt_st_rc_ft', 'alt_rc_ft', 'yearID', 'modelYearID', 'ageID', 'VPOP']
    # # merge the DataFrames into a new DataFrame, create and calculate some new metrics, drop some metrics
    # directcost_regclass.drop(columns=['VPOP'], inplace=True) # this VPOP is now summed by regclass but we want sourcetype VPOP
    # directcost_bca = cols_for_df(sales_bca, metrics_directcost_bca)
    # directcost_bca = directcost_bca.merge(directcost_regclass, on=['optionID', 'regClassID', 'fuelTypeID', 'alt_rc_ft', 'yearID', 'modelYearID', 'ageID'], how='left', sort='False')
    # directcost_bca.loc[directcost_bca['VPOP'] == 0, 'DirectCost_AvgPerVeh'] = 0
    # directcost_bca['DirectCost_TotalCost'] = directcost_bca[['DirectCost_AvgPerVeh', 'VPOP']].product(axis=1)
    # directcost_bca.reset_index(drop=True, inplace=True)

    # # merge markups and direct costs
    # markups_merged = IndirectCost(directcost_bca).merge_markups_and_directcosts(markups, ['optionID', 'regClassID', 'fuelTypeID', 'yearID'])
    # markups_merged = IndirectCost(markups_merged).merge_markup_scalers(markup_scalers_reshaped, ['optionID', 'regClassID', 'fuelTypeID', 'yearID'])
    # markups_merged.ffill(inplace=True)
    # markups_merged.reset_index(drop=True, inplace=True)

    # pass directcosts_bca thru the IndirectCost class and apply the markups to get new dataframe that includes indirect costs
    # techcost = IndirectCost(directcost_bca).indirect_cost_scaled(markups_merged, 'Warranty', warranty_vmt_share)
    # techcost = IndirectCost(techcost).indirect_cost_scaled(markups_merged, 'RnD', r_and_d_vmt_share)
    # techcost = IndirectCost(techcost).indirect_cost_unscaled(markups_merged)
    # techcost = IndirectCost(techcost).indirect_cost_sum()
    # techcost.insert(len(techcost.columns), 'TechCost_AvgPerVeh', techcost['DirectCost_AvgPerVeh'] + techcost['IndirectCost_AvgPerVeh'])
    # techcost.insert(len(techcost.columns), 'TechCost_TotalCost', techcost['DirectCost_TotalCost'] + techcost['IndirectCost_TotalCost'])
    # techcost_metrics_to_discount = [col for col in techcost.columns if 'Cost' in col]

    # create a calcs DataFrame to house costs that occur over time such as pollution/emission costs, and
    # operating costs which include fuel, DEF, repair and maintenance as appropriate, i.e., anything that's not an upfront cost
    if calc_pollution_effects == 'Y':
        print('\nWorking on pollution costs....')
        # emission_costs_calcs = pd.DataFrame(moves_adjusted.loc[moves_adjusted['modelYearID'] >= year_min])
        # emission_cost_obj = EmissionCost(sourcetype_tech_costs, criteria_emission_costs_reshaped)
        # emission_costs_calcs = emission_cost_obj.calc_emission_costs_df()
        emission_cost_obj = EmissionCost(sourcetype_criteria, criteria_emission_costs_reshaped)
        sourcetype_emission_costs = emission_cost_obj.calc_emission_costs_df()
        sourcetype_emission_costs = EmissionCost(sourcetype_emission_costs, criteria_emission_costs_reshaped).calc_criteria_costs_df()
        # sourcetype_tech_costs = emission_cost_obj.calc_emission_costs_df()
        # emission_costs_calcs = EmissionCost(emission_costs_calcs, criteria_emission_costs_reshaped).calc_criteria_costs_df()
        # sourcetype_tech_costs = EmissionCost(sourcetype_tech_costs, criteria_emission_costs_reshaped).calc_criteria_costs_df()
        criteria_costs_list = [col for col in sourcetype_emission_costs.columns if 'CriteriaCost' in col]
        criteria_costs_list_3 = [col for col in sourcetype_emission_costs.columns if 'CriteriaCost' in col and '0.03' in col]
        criteria_costs_list_7 = [col for col in sourcetype_emission_costs.columns if 'CriteriaCost' in col and '0.07' in col]
        tailpipe_pollutant_costs_list = [col for col in sourcetype_emission_costs.columns if 'Cost_onroad' in col]
        tailpipe_pollutant_costs_list_3 = [col for col in sourcetype_emission_costs.columns if 'Cost_onroad' in col and '0.03' in col]
        tailpipe_pollutant_costs_list_7 = [col for col in sourcetype_emission_costs.columns if 'Cost_onroad' in col and '0.07' in col]
        # criteria_costs_list = [col for col in emission_costs_calcs.columns if 'CriteriaCost' in col]
        # criteria_costs_list_3 = [col for col in emission_costs_calcs.columns if 'CriteriaCost' in col and '0.03' in col]
        # criteria_costs_list_7 = [col for col in emission_costs_calcs.columns if 'CriteriaCost' in col and '0.07' in col]
        # tailpipe_pollutant_costs_list = [col for col in emission_costs_calcs.columns if 'Cost_onroad' in col]
        # tailpipe_pollutant_costs_list_3 = [col for col in emission_costs_calcs.columns if 'Cost_onroad' in col and '0.03' in col]
        # tailpipe_pollutant_costs_list_7 = [col for col in emission_costs_calcs.columns if 'Cost_onroad' in col and '0.07' in col]
        criteria_and_tailpipe_pollutant_costs_list = criteria_costs_list + tailpipe_pollutant_costs_list

    # work now on operating costs which include repair, DEF, fuel costs
    print('\nWorking on operating costs....')
    # repair_warranty_ages = EstimatedAge(sourcetype_tech_costs).ages_by_identifier(warranty_miles_reshaped, warranty_age_reshaped, typical_vmt_thru_age, 'Warranty')
    # repair_usefullife_ages = EstimatedAge(sourcetype_tech_costs).ages_by_identifier(usefullife_miles_reshaped, usefullife_age_reshaped, typical_vmt_thru_age, 'UsefulLife')
    # # merge in the estimated warranty and useful life ages for estimating repair costs
    # for df in [repair_warranty_ages, repair_usefullife_ages]:
    #     sourcetype_tech_costs = sourcetype_tech_costs.merge(df, on=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'], how='left')
    # # for those MYs without ageID data within the range specified in BCA_Inputs, we'll do a forward fill to fill their data with the last MY having ageID data within the range
    # sourcetype_tech_costs.loc[sourcetype_tech_costs['modelYearID'] >= sourcetype_tech_costs['modelYearID'].max() - typical_vmt_thru_age] \
    #     = sourcetype_tech_costs.loc[sourcetype_tech_costs['modelYearID'] >= sourcetype_tech_costs['modelYearID'].max() - typical_vmt_thru_age].ffill(axis=0)
    # emission_repair_cost_calcs = RepairAndMaintenanceCost(sourcetype_tech_costs, metrics_repair_and_maint_dict, regclass_costs_dict)
    # sourcetype_tech_costs = emission_repair_cost_calcs.emission_repair_costs()
    # sourcetype_tech_costs.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    # # For what metrics do we want reductions? NOx_onroad - insert new col next to NOx_onroad
    # sourcetype_tech_costs.insert(sourcetype_tech_costs.columns.get_loc('NOx_onroad') + 1, 'NOx_onroad_Reductions', sourcetype_tech_costs['NOx_onroad'])
    # get_nox_reductions = CalcDeltas(sourcetype_tech_costs, number_alts, ['NOx_onroad_Reductions'])
    # sourcetype_tech_costs = get_nox_reductions.calc_delta_and_keep_alt_id()
    # sourcetype_tech_costs = DEFandFuelCost(sourcetype_tech_costs).orvr_fuel_impacts_mlpergram(orvr_fuelchanges)

    # calc the DEF costs
    def_costs_dict = dict()
    sourcetype_def_costs = pd.DataFrame()
    # st_rc_2_vehs = pd.Series(sourcetype_tech_costs.loc[sourcetype_tech_costs['fuelTypeID'] == 2, 'st_rc_ft'].unique())
    # for veh in st_rc_2_vehs:
    alt_st_rc_ft_vehicles = pd.Series(sourcetype_tech_costs['alt_st_rc_ft'].unique())
    for veh in alt_st_rc_ft_vehicles:
        if veh[3] == 2:
            def_costs_dict[veh] = pd.DataFrame(sourcetype_criteria.loc[sourcetype_criteria['alt_st_rc_ft'] == veh,
                                                                       ['alt_st_rc_ft', 'yearID', 'modelYearID', 'ageID',
                                                                        'NOx_onroad_Reductions']]).reset_index(drop=True)
            def_costs_obj = DEFCost(veh, cost_steps, def_costs_dict[veh], def_doserate_inputs, def_gallons_perTonNOxReduction, def_prices)
            print(def_costs_obj)
            veh_gallons = pd.DataFrame(sourcetype_gallons.loc[sourcetype_gallons['alt_st_rc_ft'] == veh, :]).reset_index(drop=True)
            veh_vmt = pd.DataFrame(sourcetype_vmt.loc[sourcetype_vmt['alt_st_rc_ft'] == veh, :]).reset_index(drop=True)
            per_veh = pd.DataFrame(sourcetype_per_veh.loc[sourcetype_per_veh['alt_st_rc_ft'] == veh,
                                                          ['alt_st_rc_ft', 'yearID', 'modelYearID', 'ageID', 'VMT_AvgPerVeh']]).reset_index(drop=True)
            def_costs_dict[veh] = def_costs_obj.calc_def_costs(veh_gallons, veh_vmt, per_veh)
            sourcetype_def_costs = pd.concat([sourcetype_def_costs, def_costs_dict[veh][['alt_st_rc_ft', 'yearID', 'modelYearID', 'ageID']
                                                                                        + [col for col in def_costs_dict[veh].columns if 'DEF' in col]]],
                                             ignore_index=True, axis=0)
        else:
            pass

    # make ORVR adjustments to gasoline THC inventories and gallons
    orvr_adjust_obj = ORVRadjust(alt_st_rc_ft_vehicles, orvr_fuelchanges, sourcetype_gallons,
                                 sourcetype_criteria[['THC_UStons_Reductions']], sourcetype_vmt)
    sourcetype_gallons = orvr_adjust_obj.adjust_gallons()
    sourcetype_per_veh = orvr_adjust_obj.adjust_mpg(sourcetype_per_veh)  # must adjust MPG prior to calc of fuel costs
    sourcetype_fuel_costs = FuelCost(alt_st_rc_ft_vehicles, sourcetype_gallons, sourcetype_vmt, sourcetype_per_veh, fuel_prices).calc_fuel_costs()
    # TODO note that fuel costs have gone down slightly due to correction in CNG fuel prices (diesel) and resultant costs (prior versions had 2045 diesel cost by accident
    # sourcetype_fuel_costs = FuelCost(sourcetype_gallons, fuel_prices).calc_fuel_costs()

    # TODO merge sourcetype_gallons and sourcetype_per_veh into sourcetype_tech_costs here? later?
    # st_rc_ft_vehs = pd.Series(moves_adjusted['st_rc_ft'].unique())
    # sourcetype_tech_costs.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    # sourcetype_tech_costs = ORVRadjust(st_rc_ft_vehs, orvr_fuelchanges, sourcetype_tech_costs).adjust_gallons()

    # calculate fuel costs
    # sourcetype_tech_costs = FuelCost(sourcetype_tech_costs, fuel_prices).calc_fuel_costs()
    # merge in the DEF costs
    # sourcetype_tech_costs = sourcetype_tech_costs.merge(sourcetype_def_costs, on=['alt_st_rc_ft', 'yearID', 'ageID'], how='left')

    # calculate emission repair costs # TODO rewrite estimated age class...repair costs? Ugh
    # estimated_ages = dict()
    # estimated_ages_df = pd.DataFrame()
    # for veh in alt_st_rc_ft_vehicles:
    #     for model_year in range(sourcetype_per_veh['modelYearID'].min(), sourcetype_per_veh['modelYearID'].max() + 1):
    #         if model_year <= sourcetype_per_veh['modelYearID'].max() - typical_vmt_thru_age:
    #             veh_year_df = pd.DataFrame(sourcetype_per_veh.loc[(sourcetype_per_veh['alt_st_rc_ft'] == veh) &
    #                                                               (sourcetype_per_veh['modelYearID'] == model_year), :].reset_index(drop=True))
    #             estimated_age_obj = EstimatedAge2(veh, veh_year_df, typical_vmt_thru_age)
    #             print(estimated_age_obj)
    #             warranty_age_veh = estimated_age_obj.return_df(warranty_miles_reshaped, warranty_age_reshaped, 'Warranty', model_year)
    #             useful_life_age_veh = estimated_age_obj.return_df(usefullife_miles_reshaped, usefullife_age_reshaped, 'UsefulLife', model_year)
    #             estimated_ages[veh, model_year] = warranty_age_veh.merge(useful_life_age_veh,
    #                                                                      on=gen_fxns.get_common_metrics(warranty_age_veh, useful_life_age_veh), how='left')
    #         else:
    #             veh_year_df = pd.DataFrame(sourcetype_per_veh.loc[(sourcetype_per_veh['alt_st_rc_ft'] == veh) &
    #                                                               (sourcetype_per_veh['modelYearID'] == model_year), 'static_id'].reset_index(drop=True))
    #             estimated_ages[veh, model_year] = pd.concat([veh_year_df,
    #                                                          estimated_ages[veh, model_year - 1]
    #                                                         .iloc[:-1, estimated_ages[veh, model_year - 1].columns != 'static_id']], ignore_index=False, axis=1)
    #         estimated_ages_df = pd.concat([estimated_ages_df, estimated_ages[veh, model_year]], ignore_index=True, axis=0)
# TODO double check workings of estimated ages given new structure
    # estimated_warranty_age_obj = EstimatedAge(sourcetype_tech_costs, typical_vmt_thru_age, warranty_miles_reshaped, warranty_age_reshaped)
    # sourcetype_tech_costs = estimated_warranty_age_obj.ages_by_identifier('Warranty')
    # estimated_usefullife_age_obj = EstimatedAge(sourcetype_tech_costs, typical_vmt_thru_age, usefullife_miles_reshaped, usefullife_age_reshaped)
    # sourcetype_tech_costs = estimated_usefullife_age_obj.ages_by_identifier('UsefulLife')

    estimated_warranty_age_obj = EstimatedAge(sourcetype_per_veh, typical_vmt_thru_age,
                                              warranty_miles_reshaped, warranty_age_reshaped)
    warranty_ages = estimated_warranty_age_obj.ages_by_identifier('Warranty')
    estimated_usefullife_age_obj = EstimatedAge(sourcetype_per_veh, typical_vmt_thru_age,
                                                usefullife_miles_reshaped, usefullife_age_reshaped)
    usefullife_ages = estimated_usefullife_age_obj.ages_by_identifier('UsefulLife')
    estimated_ages_df = warranty_ages.merge(usefullife_ages, on=gen_fxns.get_common_metrics(warranty_ages, usefullife_ages), how='left')

    emission_repair_costs_dict = dict()
    sourcetype_repair_costs = pd.DataFrame()
    scaling_frame_of_reference_df = pd.DataFrame(sourcetype_tech_costs.loc[(sourcetype_tech_costs['alt_rc_ft'] == (0, 47, 2)) &
                                                                           (sourcetype_tech_costs['ageID'] == 0),
                                                                           ['modelYearID', 'DirectCost_AvgPerVeh']]).reset_index(drop=True)
    for veh in alt_st_rc_ft_vehicles:
        emission_repair_cost_obj = RepairAndMaintenanceCost(sourcetype_tech_costs, metrics_repair_and_maint_dict, scaling_frame_of_reference_df,
                                                            estimated_ages_df, sourcetype_per_veh, sourcetype_vmt)
        emission_repair_costs_dict[veh] = emission_repair_cost_obj.emission_repair_costs(veh)
        sourcetype_repair_costs = pd.concat([sourcetype_repair_costs, emission_repair_costs_dict[veh]], ignore_index=True, axis=0)

    # merge into a single sourcetype_all_costs dataframe
    sourcetype_all_costs = sourcetype_vpop.copy()
    df_merge_list = [sourcetype_vmt, sourcetype_per_veh, sourcetype_tech_costs,
                     sourcetype_def_costs, sourcetype_gallons, sourcetype_fuel_costs, estimated_ages_df, sourcetype_repair_costs]
    if calc_pollution_effects == 'Y':
        df_merge_list = df_merge_list + [sourcetype_emission_costs]
    for df in df_merge_list:
        sourcetype_all_costs = sourcetype_all_costs.merge(df, on=gen_fxns.get_common_metrics(sourcetype_all_costs, df), how='left').reset_index(drop=True)
    sourcetype_all_costs.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    sourcetype_all_costs.drop(columns='static_id', inplace=True)
    sourcetype_all_costs.reset_index(drop=True, inplace=True)

# TODO qa/qc the new sourcetype_repair_costs
    # alt_st_rc_ft_vehs = pd.Series(sourcetype_tech_costs['alt_st_rc_ft']).unique()
    # for veh in alt_st_rc_ft_vehicles:
    #     # emission_repair_costs_dict[veh] = pd.DataFrame(sourcetype_tech_costs.loc[sourcetype_tech_costs['alt_st_rc_ft'] == veh, :])
    #     # emission_repair_cost_obj = RepairAndMaintenanceCost(sourcetype_tech_costs, metrics_repair_and_maint_dict, regclass_costs_dict)
    #     emission_repair_cost_obj = RepairAndMaintenanceCost(sourcetype_tech_costs, metrics_repair_and_maint_dict, scaling_frame_of_reference_df)
    #     emission_repair_costs_dict[veh] = emission_repair_cost_obj.emission_repair_costs(veh)
    # sourcetype_tech_costs = pd.DataFrame()
    # for veh in alt_st_rc_ft_vehicles:
    #     sourcetype_tech_costs = pd.concat([sourcetype_tech_costs, emission_repair_costs_dict[veh]], axis=0, ignore_index=True)
    # sourcetype_tech_costs.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)

    cols_owner = ['DEFCost_TotalCost', 'FuelCost_Retail_TotalCost', 'EmissionRepairCost_Owner_TotalCost']
    cols_bca = ['DEFCost_TotalCost', 'FuelCost_Pretax_TotalCost', 'EmissionRepairCost_Owner_TotalCost']
    sourcetype_all_costs.insert(sourcetype_all_costs.columns.get_loc('EmissionRepairCost_Owner_TotalCost') + 1,
                                'OperatingCost_Owner_TotalCost',
                                sourcetype_all_costs[cols_owner].sum(axis=1))
    sourcetype_all_costs.insert(sourcetype_all_costs.columns.get_loc('OperatingCost_Owner_TotalCost') + 1,
                                'OperatingCost_BCA_TotalCost',
                                sourcetype_all_costs[cols_bca].sum(axis=1))
    sourcetype_all_costs.insert(sourcetype_all_costs.columns.get_loc('OperatingCost_BCA_TotalCost') + 1,
                                'OperatingCost_Owner_AvgPerMile',
                                sourcetype_all_costs['OperatingCost_Owner_TotalCost'] / sourcetype_all_costs['VMT'])
    sourcetype_all_costs.insert(sourcetype_all_costs.columns.get_loc('OperatingCost_Owner_AvgPerMile') + 1,
                                'OperatingCost_Owner_AvgPerVeh',
                                sourcetype_all_costs[['OperatingCost_Owner_AvgPerMile', 'VMT_AvgPerVeh']].product(axis=1))

    # sourcetype_tech_costs.insert(len(sourcetype_tech_costs.columns), 'OperatingCost_Owner_TotalCost', sourcetype_tech_costs[cols_owner].sum(axis=1))
    # sourcetype_tech_costs.insert(len(sourcetype_tech_costs.columns), 'OperatingCost_BCA_TotalCost', sourcetype_tech_costs[cols_bca].sum(axis=1))
    # sourcetype_tech_costs.insert(len(sourcetype_tech_costs.columns), 'OperatingCost_Owner_AvgPerMile', sourcetype_tech_costs['OperatingCost_Owner_TotalCost'] / sourcetype_tech_costs['VMT'])
    # sourcetype_tech_costs.insert(len(sourcetype_tech_costs.columns), 'OperatingCost_Owner_AvgPerVeh', sourcetype_tech_costs[['OperatingCost_Owner_AvgPerMile', 'VMT_AvgPerVeh']].product(axis=1))
    operatingcost_metrics_to_discount = [col for col in sourcetype_all_costs.columns if 'RepairCost' in col or 'DEFCost' in col
                                         or 'FuelCost' in col or 'OperatingCost' in col]

    # now create some weighted results of operating costs
    # vehs_operating_costs = pd.Series(sourcetype_tech_costs['alt_st_rc_ft']).unique()
    # vehs_operating_rc_costs = pd.Series(sourcetype_tech_costs['alt_rc_ft']).unique()
    # weighted_repair_owner_cpm = dict()
    # weighted_def_cpm = dict()
    # weighted_fuel_cpm = dict()
    # if test_run == 't':
    #     year_list = [2027, 2030]
    # else:
    #     year_list = weighted_operating_cost_years
    # max_age_included = 9
    # for veh in vehs_operating_costs:
    #     weighted_def_cpm[veh] = weighted_result(sourcetype_tech_costs, 'DEFCost_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
    #     weighted_fuel_cpm[veh] = weighted_result(sourcetype_tech_costs, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
    #     weighted_repair_owner_cpm[veh] = weighted_result(sourcetype_tech_costs, 'EmissionRepairCost_Owner_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
    # for veh in vehs_operating_rc_costs:
    #     pass
    # alt_st_rc_ft_vehs = pd.Series(sourcetype_tech_costs['alt_st_rc_ft'].unique())
    weighted_results_obj = WeightedResult(sourcetype_all_costs, 'VMT_AvgPerVeh', alt_st_rc_ft_vehicles, 'modelYearID',
                                          weighted_operating_cost_years, max_age_included, options_dict)
    weighted_def_cpm_df = weighted_results_obj.weighted_results('DEFCost_AvgPerMile')
    weighted_repair_owner_cpm_df = weighted_results_obj.weighted_results('EmissionRepairCost_Owner_AvgPerMile')
    weighted_fuel_cpm_df = weighted_results_obj.weighted_results('FuelCost_Retail_AvgPerMile')

    # and now put the MOVES name identifier in the DataFrame
    sourcetype_all_costs.insert(sourcetype_all_costs.columns.get_loc('fuelTypeID') + 1, 'Vehicle_Name_MOVES', '')
    for veh in alt_st_rc_ft_vehicles:
        sourcetype_all_costs.loc[sourcetype_all_costs['alt_st_rc_ft'] == veh, 'Vehicle_Name_MOVES'] = Vehicle(veh).name_moves()



    # merge emission_costs into sourcetype_tech_costs if appropriate
    # if calc_pollution_effects == 'Y':
    #     sourcetype_tech_costs = sourcetype_tech_costs.merge(emission_costs_calcs, on=[moves_adjusted_cols +
    #                                                                         ['alt_st_rc_ft', 'alt_rc_ft', 'st_rc_ft', 'ageID']],
    #                                               how='left', sort='False')
    # else:
    #     pass
# TODO redo the discounting below since techcost no longer in a separate DF
    # pass each DataFrame thru the DiscountValues class and pass the list of metrics to be discounted for each thru the discount method
    print('\nWorking on discounting monetized values....')
    # techcost_dict = dict()
    calcs_dict = dict()
    if calc_pollution_effects == 'Y':
        # bca_metrics_to_discount = criteria_and_tailpipe_pollutant_costs_list + operatingcost_metrics_to_discount
        bca_metrics_to_discount = techcost_metrics_to_discount \
                                  + criteria_and_tailpipe_pollutant_costs_list \
                                  + operatingcost_metrics_to_discount
    else:
        # bca_metrics_to_discount = operatingcost_metrics_to_discount
        bca_metrics_to_discount = techcost_metrics_to_discount + operatingcost_metrics_to_discount
    for dr in [0, discrate_social_low, discrate_social_high]:
        # techcost_dict[dr] = DiscountValues(techcost, techcost_metrics_to_discount, discount_to_yearID, costs_start)
        # techcost_dict[dr] = techcost_dict[dr].discount(dr)
        # calcs_dict[dr] = DiscountValues(calcs, bca_metrics_to_discount, discount_to_yearID, costs_start)
        # calcs_dict[dr] = DiscountValues(sourcetype_tech_costs, bca_metrics_to_discount, discount_to_yearID, costs_start)
        # calcs_dict[dr] = calcs_dict[dr].discount(dr)
        discounting_obj = DiscountValues(sourcetype_all_costs, bca_metrics_to_discount, discount_to_yearID, costs_start)
        calcs_dict[dr] = discounting_obj.discount(dr)


    # now set to NaN discounted pollutant values using discount rates that are not consistent with the input values
    if calc_pollution_effects == 'Y':
        for col in criteria_costs_list_3:
            calcs_dict[0.07][col] = np.nan
            # emission_costs_dict[0.07][col] = np.nan
        for col in criteria_costs_list_7:
            calcs_dict[0.03][col] = np.nan
            # emission_costs_dict[0.03][col] = np.nan
        for col in tailpipe_pollutant_costs_list_3:
            calcs_dict[0.07][col] = np.nan
            # emission_costs_dict[0.07][col] = np.nan
        for col in tailpipe_pollutant_costs_list_7:
            calcs_dict[0.03][col] = np.nan
            # emission_costs_dict[0.03][col] = np.nan

    # work on pulling in all bca elements -- tech, pollution, operating
    print('\nWorking on benefit-cost analysis results and summarizing things....')
    # merge_metrics = ['DiscountRate', 'optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID',
    #                  'alt_st_rc_ft', 'alt_rc_ft', 'VPOP']
    # for dr in [0, discrate_social_low, discrate_social_high]:
    #     calcs_dict[dr] = techcost_dict[dr].merge(calcs_dict[dr], on=merge_metrics, how='outer')

    calcs = pd.DataFrame()
    for dr in [0, discrate_social_low, discrate_social_high]:
        calcs = pd.concat([calcs, calcs_dict[dr]], axis=0, ignore_index=True)

    # add some total cost columns
    calcs.insert(len(calcs.columns), 'TechAndOperatingCost_BCA_TotalCost', calcs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost']].sum(axis=1))
    if calc_pollution_effects == 'Y':
        for dr, mort_est in product([0.03, 0.07], ['low', 'high']):
            calcs.insert(len(calcs.columns), 'TotalCost_' + mort_est + '_' + str(dr),
                         calcs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(dr)]].sum(axis=1))
    else:
        pass

    # adjust the 3 and 7 DR total costs as needed
    if calc_pollution_effects == 'Y':
        for mort_est in ['low', 'high']:
            calcs.loc[calcs['DiscountRate'] == 0.03, 'TotalCost_' + mort_est + '_' + str(0.03)] \
                = calcs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(0.03)]].sum(axis=1)
            calcs.loc[calcs['DiscountRate'] == 0.03, 'TotalCost_' + mort_est + '_' + str(0.07)] \
                = np.nan
            calcs.loc[calcs['DiscountRate'] == 0.07, 'TotalCost_' + mort_est + '_' + str(0.07)] \
                = calcs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(0.07)]].sum(axis=1)
            calcs.loc[calcs['DiscountRate'] == 0.07, 'TotalCost_' + mort_est + '_' + str(0.03)] \
                = np.nan

    # Now add an OptionName column so that output files provide that information
    Fleet(calcs).insert_option_name(options_dict, number_alts)
    # Fleet(moves_adjusted).insert_option_name(options_dict, number_alts)

    # now set a standard row header for use in grouping along with metrics to group
    bca_metrics_to_sum = [col for col in calcs.columns if 'TotalCost' in col or 'VPOP' in col or 'Gallons' in col
                          or 'PM25' in col or 'NOx' in col or 'Criteria' in col]
    bca_metrics_to_avg = [col for col in calcs.columns if 'AvgPerVeh' in col or 'AvgPerMile' in col]
    bca_metrics_to_cumsum = [col for col in calcs.columns if 'TotalCost' in col or 'Criteria' in col]

    # create a dict of lists for passing thru grouping methods
    row_header_group = dict()
    common_metrics = ['optionID', 'OptionName', 'DiscountRate']
    row_header_group[1] = common_metrics + ['yearID']
    row_header_group[2] = common_metrics + ['yearID', 'regClassID', 'fuelTypeID']
    groups = 2 # increment this consistent with row_headers created

    row_header_group_cumsum = dict()
    row_header_group_cumsum[1] = common_metrics
    row_header_group_cumsum[2] = common_metrics + ['regClassID', 'fuelTypeID']

    # create a bca DataFrame that contains metrics necessary for the bca, i.e., TotalCost metrics
    bca = pd.DataFrame(calcs, columns=row_header_group[2] + ['modelYearID', 'ageID', 'sourceTypeID'] + bca_metrics_to_sum + bca_metrics_to_avg)
    # create some dicts to store the groupby.sum, groupby.cumsum and groupby.mean results
    bca_sum = dict()
    bca_mean = dict()
    bca_summary = dict()
    for group in range(1, groups + 1):
        # first a groupby.sum, then a groupby.cumsum on the groupby.sum which is joined into the groupby.sum, then a groupby.mean, then a merge into one
        bca_sum[group] = GroupMetrics(bca, row_header_group[group]).group_sum(bca_metrics_to_sum)
        bca_mean[group] = GroupMetrics(bca, row_header_group[group]).group_mean(bca_metrics_to_avg)
        bca_summary[group] = bca_sum[group].merge(bca_mean[group], on=row_header_group[group])
        bca_summary[group] = bca_summary[group].join(GroupMetrics(bca_summary[group], row_header_group_cumsum[group]).group_cumsum(bca_metrics_to_cumsum))

    # now annualize the cumsum metrics
    for group in range(1, groups + 1):
        bca_summary[group] = DiscountValues(bca_summary[group], bca_metrics_to_cumsum, discount_to_yearID, costs_start).annualize()

    # calc the deltas relative to alt0
    bca.sort_values(by=['DiscountRate', 'optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID'], ascending=True, inplace=True, axis=0)
    bca_metrics_for_deltas = bca_metrics_to_sum + bca_metrics_to_avg \
                             + [metric + '_CumSum' for metric in bca_metrics_to_cumsum] \
                             + [metric + '_Annualized' for metric in bca_metrics_to_cumsum]
    for group in range(1, groups + 1):
        bca_summary[group] = pd.concat([bca_summary[group],
                             CalcDeltas(bca_summary[group], number_alts, bca_metrics_for_deltas).calc_delta_and_new_alt_id()],
                             axis=0, ignore_index=True)

    # add some identifier columns to the grouped output files
    bca_summary[2].insert(bca_summary[2].columns.get_loc('regClassID') + 1,
                          'regclass',
                          pd.Series(regClassID[number] for number in bca_summary[2]['regClassID']))
    bca_summary[2].insert(bca_summary[2].columns.get_loc('fuelTypeID') + 1,
                          'fueltype',
                          pd.Series(fuelTypeID[number] for number in bca_summary[2]['fuelTypeID']))

    # calc the deltas relative to alt0 for the calcs and bca DataFrames
    calcs.sort_values(by=['DiscountRate', 'optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID'], ascending=True, inplace=True, axis=0)
    calcs_cols_for_deltas = [col for col in calcs.columns if 'Calculated' in col or 'Estimated' in col or 'Cost' in col or 'cost' in col
                             or 'Warranty' in col or 'UsefulLife' in col or 'Gallons' in col or 'max' in col or 'slope' in col
                             or ('AvgPerVeh' in col and 'VMT' not in col) or 'THC' in col or 'PM' in col or 'NOx' in col]
    calcs = pd.concat([calcs, CalcDeltas(calcs, number_alts, calcs_cols_for_deltas).calc_delta_and_new_alt_id()], axis=0, ignore_index=True)

    # generate more document tables
    preamble_program_metrics = ['DirectCost_TotalCost', 'WarrantyCost_TotalCost', 'RnDCost_TotalCost', 'OtherCost_TotalCost', 'ProfitCost_TotalCost', 'TechCost_TotalCost',
                                'EmissionRepairCost_Owner_TotalCost', 'DEFCost_TotalCost', 'FuelCost_Pretax_TotalCost', 'OperatingCost_BCA_TotalCost',
                                'TechAndOperatingCost_BCA_TotalCost']
    preamble_program_table = DocTables(calcs).preamble_ria_tables(preamble_program_metrics, ['DiscountRate', 'optionID', 'OptionName', 'yearID'], 'sum')
    preamble_program_table = gen_fxns.round_sig(preamble_program_table, preamble_program_metrics, 1000000, 2)
    preamble_program_table.insert(len(preamble_program_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    preamble_program_table_pv = DocTables(calcs).preamble_ria_tables(preamble_program_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    preamble_program_table_pv = gen_fxns.round_sig(preamble_program_table_pv, preamble_program_metrics, 1000000, 2)
    preamble_program_table_pv.insert(len(preamble_program_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    ria_program_metrics = ['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'TechAndOperatingCost_BCA_TotalCost']
    ria_program_table = DocTables(calcs).preamble_ria_tables(ria_program_metrics, ['DiscountRate', 'optionID', 'OptionName', 'yearID'], 'sum')
    ria_program_table = gen_fxns.round_sig(ria_program_table, ria_program_metrics, 1000000, 2)
    ria_program_table.insert(len(ria_program_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    ria_program_table_pv = DocTables(calcs).preamble_ria_tables(ria_program_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    ria_program_table_pv = gen_fxns.round_sig(ria_program_table_pv, ria_program_metrics, 1000000, 2)
    ria_program_table_pv.insert(len(ria_program_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_metrics = ['DirectCost_TotalCost', 'WarrantyCost_TotalCost', 'RnDCost_TotalCost', 'OtherCost_TotalCost', 'ProfitCost_TotalCost', 'TechCost_TotalCost']
    tech_by_ft_yr_table = DocTables(calcs).preamble_ria_tables(tech_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID', 'yearID'], 'sum')
    tech_by_ft_yr_table = gen_fxns.round_sig(tech_by_ft_yr_table, tech_metrics, 1000000, 2)
    tech_by_ft_yr_table.insert(len(tech_by_ft_yr_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_ft_yr_table_pv = DocTables(calcs).preamble_ria_tables(tech_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID'], 'sum')
    tech_by_ft_yr_table_pv = gen_fxns.round_sig(tech_by_ft_yr_table_pv, tech_metrics, 1000000, 2)
    tech_by_ft_yr_table_pv.insert(len(tech_by_ft_yr_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_ft_rc_table = DocTables(calcs).preamble_ria_tables(tech_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'regClassID'], 'sum')
    tech_by_ft_rc_table = gen_fxns.round_sig(tech_by_ft_rc_table, tech_metrics, 1000000, 2)
    tech_by_ft_rc_table.insert(len(tech_by_ft_rc_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_ft_alt_table = DocTables(calcs).preamble_ria_tables(tech_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName'], 'sum')
    tech_by_ft_alt_table = gen_fxns.round_sig(tech_by_ft_alt_table, tech_metrics, 1000000, 2)
    tech_by_ft_alt_table.insert(len(tech_by_ft_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_alt_table = DocTables(calcs).preamble_ria_tables(tech_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    tech_by_alt_table = gen_fxns.round_sig(tech_by_alt_table, tech_metrics, 1000000, 2)
    tech_by_alt_table.insert(len(tech_by_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_metrics = ['EmissionRepairCost_Owner_TotalCost', 'DEFCost_TotalCost', 'FuelCost_Pretax_TotalCost', 'OperatingCost_BCA_TotalCost']
    operating_ft_year_table = DocTables(calcs).preamble_ria_tables(operating_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID', 'yearID'], 'sum')
    operating_ft_year_table = gen_fxns.round_sig(operating_ft_year_table, operating_metrics, 1000000, 2)
    operating_ft_year_table.insert(len(operating_ft_year_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_ft_year_table_pv = DocTables(calcs).preamble_ria_tables(operating_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID'], 'sum')
    operating_ft_year_table_pv = gen_fxns.round_sig(operating_ft_year_table_pv, operating_metrics, 1000000, 2)
    operating_ft_year_table_pv.insert(len(operating_ft_year_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_by_ft_rc_table = DocTables(calcs).preamble_ria_tables(operating_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'regClassID'], 'sum')
    operating_by_ft_rc_table = gen_fxns.round_sig(operating_by_ft_rc_table, operating_metrics, 1000000, 2)
    operating_by_ft_rc_table.insert(len(operating_by_ft_rc_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_by_ft_alt_table = DocTables(calcs).preamble_ria_tables(operating_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName'], 'sum')
    operating_by_ft_alt_table = gen_fxns.round_sig(operating_by_ft_alt_table, operating_metrics, 1000000, 2)
    operating_by_ft_alt_table.insert(len(operating_by_ft_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_by_alt_table = DocTables(calcs).preamble_ria_tables(operating_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    operating_by_alt_table = gen_fxns.round_sig(operating_by_alt_table, operating_metrics, 1000000, 2)
    operating_by_alt_table.insert(len(operating_by_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    econ_table_metrics = ['TechCost_TotalCost']
    econ_table = pd.pivot_table(calcs, econ_table_metrics, ['DiscountRate', 'yearID'], columns=['optionID', 'OptionName'],
                                aggfunc='sum', margins=True)
    econ_table = econ_table.reset_index(drop=False)
    econ_table.insert(len(econ_table.columns), 'Units_SignificantDigits', 'USD; No rounding')

    bca_cost_metrics = ['TechAndOperatingCost_BCA_TotalCost']
    bca_cost_table = pd.pivot_table(calcs, bca_cost_metrics, ['DiscountRate', 'yearID'], columns=['optionID', 'OptionName'], aggfunc='sum')
    bca_cost_table = bca_cost_table.reset_index(drop=False)
    bca_cost_table.insert(len(bca_cost_table.columns), 'Units_SignificantDigits', 'USD; No rounding')
    
    bca_cost_table_pv = pd.pivot_table(calcs, bca_cost_metrics, ['DiscountRate'], columns=['optionID', 'OptionName'], aggfunc='sum')
    bca_cost_table_pv = bca_cost_table_pv.reset_index(drop=False)
    bca_cost_table_pv.insert(len(bca_cost_table_pv.columns), 'Units_SignificantDigits', 'USD; No rounding')

    doc_table_dict = {'program': preamble_program_table,
                      'program_pv': preamble_program_table_pv,
                      'ria_program': ria_program_table,
                      'ria_program_pv': ria_program_table_pv,
                      'tech': tech_by_ft_yr_table,
                      'tech_pv': tech_by_ft_yr_table_pv,
                      'tech_byRC': tech_by_ft_rc_table,
                      'tech_byFT': tech_by_ft_alt_table,
                      'tech_byOption': tech_by_alt_table,
                      'operating': operating_ft_year_table,
                      'operating_pv': operating_ft_year_table_pv,
                      'operating_byRC': operating_by_ft_rc_table,
                      'operating_byFT': operating_by_ft_alt_table,
                      'operating_byOption': operating_by_alt_table,
                      'econ': econ_table,
                      'bca_cost': bca_cost_table,
                      'bca_cost_pv': bca_cost_table_pv,
                      }
# TODO figure out how to print the doc tables to an excel file with multiple sheets
    # new_metrics = [metric for metric in bca.columns if 'VMT' in metric or 'Warranty' in metric or 'Useful' in metric or 'tons' in metric]
    # bca = pd.concat([bca, CalcDeltas(bca, number_alts, [col for col in bca.columns if 'Cost' in col] + new_metrics).calc_delta_and_new_alt_id()],
    #                 axis=0, ignore_index=True)
    #
    # bca_metrics_to_round = [metric for metric in bca.columns if 'Cost' in metric and 'PerMile' not in metric]
    # bca = gen_fxns.round_metrics(bca, bca_metrics_to_round, round_costs_by)

    elapsed_time_calcs = time.time() - start_time_calcs

    print("\nSaving the outputs....")
    start_time_outputs = time.time()

    # set results path in which to save all files created or used/copied by this module
    # and set output path in which to save all files created by this module; the output path will be in the results path
    # move this to earlier in main if results folder location is made user selectable so that the selection is made shortly after start of run
    path_outputs.mkdir(exist_ok=True)
    path_of_run_folder = path_outputs.joinpath(f'{start_time_readable}_CTI_{run_folder_identifier}')
    path_of_run_folder.mkdir(exist_ok=False)
    path_of_run_inputs_folder = path_of_run_folder.joinpath('run_inputs')
    path_of_run_inputs_folder.mkdir(exist_ok=False)
    path_of_run_results_folder = path_of_run_folder.joinpath('run_results')
    path_of_run_results_folder.mkdir(exist_ok=False)
    path_of_modified_inputs_folder = path_of_run_folder.joinpath('modified_inputs')
    path_of_modified_inputs_folder.mkdir(exist_ok=False)

    # first build some high level summary tables for copy/paste into slides/documents/etc.
    techcost_per_veh_cols = ['DiscountRate', 'yearID', 'regclass', 'fueltype', 'OptionName']
    result_cols = ['DirectCost_AvgPerVeh', 'WarrantyCost_AvgPerVeh', 'RnDCost_AvgPerVeh', 'OtherCost_AvgPerVeh', 'ProfitCost_AvgPerVeh', 'TechCost_AvgPerVeh']
    techcost_per_veh_cols += result_cols
    discount_rates = [0]
    techcost_years = techcost_summary_years
    regclasses = ['LHD', 'LHD45', 'MHD67', 'HHD8', 'Urban Bus']
    fueltypes = ['Diesel', 'Gasoline', 'CNG']
    techcost_per_veh_file = pd.ExcelWriter(path_of_run_results_folder.joinpath('techcosts_AvgPerVeh.xlsx'))
    DocTables(bca_summary[2]).techcost_per_veh_table(discount_rates, techcost_years, regclasses, fueltypes, techcost_per_veh_cols, techcost_per_veh_file)
    techcost_per_veh_file.save()

    bca_cols = ['OptionName', 'DiscountRate', 'TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'TechAndOperatingCost_BCA_TotalCost']
    bca_years = bca_summary_years
    bca_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annual.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_summary[1]).bca_yearID_tables('', 0, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.03', bca_years,
                                                    'billions', bca_cols, bca_annual)
    else:
        DocTables(bca_summary[1]).bca_yearID_tables('', 0, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                    'billions', bca_cols, bca_annual)
    bca_annual.save()

    bca_npv = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_npv.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_summary[1]).bca_yearID_tables('_CumSum', 0.03, 'CriteriaCost_low_0.03', 'CriteriaCost_high_0.03', bca_years,
                                                    'billions', bca_cols, bca_npv)
        DocTables(bca_summary[1]).bca_yearID_tables('_CumSum', 0.07, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.07', bca_years,
                                                    'billions', bca_cols, bca_npv)
    else:
        DocTables(bca_summary[1]).bca_yearID_tables('_CumSum', 0.03, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                    'billions', bca_cols, bca_npv)
        DocTables(bca_summary[1]).bca_yearID_tables('_CumSum', 0.07, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                    'billions', bca_cols, bca_npv)
    bca_npv.save()

    bca_annualized = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annualized.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_summary[1]).bca_yearID_tables('_Annualized', 0.03, 'CriteriaCost_low_0.03', 'CriteriaCost_high_0.03', bca_years,
                                                    'billions', bca_cols, bca_annualized)
        DocTables(bca_summary[1]).bca_yearID_tables('_Annualized', 0.07, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.07', bca_years,
                                                    'billions', bca_cols, bca_annualized)
    else:
        DocTables(bca_summary[1]).bca_yearID_tables('_Annualized', 0.03, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                    'billions', bca_cols, bca_annualized)
        DocTables(bca_summary[1]).bca_yearID_tables('_Annualized', 0.07, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                    'billions', bca_cols, bca_annualized)
    bca_annualized.save()

    # note that the inventory tables created below include MY2027+ only since emission_costs_sum is based on fleet_bca
    if calc_pollution_effects == 'Y':
        inventory_cols = ['OptionName', 'yearID', 'PM25_onroad', 'NOx_onroad']
        inventory_years = bca_summary_years
        inventory_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('inventory_annual_IncludedModelYears.xlsx'))
        DocTables(bca_summary[1]).inventory_tables1(inventory_years, inventory_cols, inventory_annual)
        inventory_annual.save()

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    inputs_filename_list = gen_fxns.inputs_filenames(input_files_pathlist)
    if create_all_files == 'y' or create_all_files == 'Y' or create_all_files == '':
        for file in inputs_filename_list:
            path_source = path_inputs.joinpath(file)
            path_destination = path_of_run_inputs_folder.joinpath(file)
            shutil.copy2(path_source, path_destination) # copy2 maintains original timestamp metadata
        fuel_prices.to_csv(path_of_modified_inputs_folder.joinpath('fuel_prices_' + aeo_case + '.csv'), index=False)
        regclass_costs.to_csv(path_of_modified_inputs_folder.joinpath('regclass_costs.csv'), index=False)
        markup_scalers_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('markup_scalers_reshaped.csv'), index=False)
        # def_doserate_inputs.to_csv(path_of_modified_inputs_folder.joinpath('def_doserate_inputs.csv'), index=False)
        repair_and_maintenance.to_csv(path_of_modified_inputs_folder.joinpath('repair_and_maintenance.csv'))
        def_prices.to_csv(path_of_modified_inputs_folder.joinpath('def_prices.csv'), index=False)
        gdp_deflators = pd.DataFrame(gdp_deflators)  # from dict to df
        gdp_deflators.to_csv(path_of_modified_inputs_folder.joinpath('gdp_deflators.csv'), index=True)
        if calc_pollution_effects == 'Y':
            criteria_emission_costs_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('criteria_emission_costs_reshaped.csv'), index=False)

        # write some output files
        weighted_repair_owner_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_emission_repair_owner_cpm.csv'), index=True)
        weighted_def_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_def_cpm.csv'), index=True)
        weighted_fuel_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_fuel_cpm.csv'), index=True)
        bca_summary[1].to_csv(path_of_run_results_folder.joinpath('bca_by_yearID.csv'), index=False)
        calcs.to_csv(path_of_run_results_folder.joinpath('bca_all_calcs.csv'), index=False)

        document_tables_file = pd.ExcelWriter(path_of_run_results_folder.joinpath('preamble_ria_tables.xlsx'))
        for sheet_name in doc_table_dict:
            doc_table_dict[sheet_name].to_excel(document_tables_file, sheet_name=sheet_name)
        document_tables_file.save()

    # for figures, an updated options_dict would be nice
    for alt_num in range(1, len(options_dict)):
        k = alt_num * 10
        alt0 = options_dict[0]['OptionName']
        alt = options_dict[alt_num]['OptionName']
        options_dict.update({k: {'OptionName': f'{alt}_minus_{alt0}'}})

    if generate_emissionrepair_cpm_figures != 'N':
        cpm_figure_years = generate_emissionrepair_cpm_figures.split(',')
        for i, v in enumerate(cpm_figure_years):
            cpm_figure_years[i] = pd.to_numeric(cpm_figure_years[i])
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(calcs.loc[calcs['optionID'] < 10, 'optionID']).unique()
        veh_names = pd.Series(calcs['Vehicle_Name_MOVES']).unique()
        for veh_name in veh_names:
            for cpm_figure_year in cpm_figure_years:
                CreateFigures(calcs, options_dict, path_figures).line_chart_vs_age(0, alts, cpm_figure_year, veh_name, 'EmissionRepairCost_Owner_AvgPerMile')

    if generate_BCA_ArgsByOption_figures == 'Y':
        yearID_min = int(calcs['yearID'].min())
        yearID_max = int(calcs['yearID'].max())
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(calcs.loc[calcs['optionID'] >= 10, 'optionID']).unique()
        for alt in alts:
            CreateFigures(bca_summary[1], options_dict, path_figures).line_chart_args_by_option(0, alt, yearID_min, yearID_max,
                                                                                                  'TechCost_TotalCost',
                                                                                                  'EmissionRepairCost_Owner_TotalCost',
                                                                                                  'DEFCost_TotalCost',
                                                                                                  'FuelCost_Pretax_TotalCost',
                                                                                                  'TechAndOperatingCost_BCA_TotalCost'
                                                                                                  )
    if generate_BCA_ArgByOptions_figures == 'Y':
        yearID_min = int(calcs['yearID'].min())
        yearID_max = int(calcs['yearID'].max())
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(calcs.loc[calcs['optionID'] >= 10, 'optionID']).unique()
        args = ['TechCost_TotalCost',
                'EmissionRepairCost_Owner_TotalCost',
                'DEFCost_TotalCost',
                'FuelCost_Pretax_TotalCost',
                'TechAndOperatingCost_BCA_TotalCost'
                ]
        for arg in args:
            CreateFigures(bca_summary[1], options_dict, path_figures).line_chart_arg_by_options(0, alts, yearID_min, yearID_max, arg)

    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder', 'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [project_code.__version__, path_of_run_folder, start_time_readable, elapsed_time_read, elapsed_time_calcs, elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log = pd.concat([summary_log, gen_fxns.get_file_datetime(input_files_pathlist)], axis=0, sort=False, ignore_index=True)
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)


if __name__ == '__main__':
    main()
