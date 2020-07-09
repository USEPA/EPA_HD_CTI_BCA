"""
This is the primary module of the benefit cost analysis. This module reads input files, calls other modules and generates output files.
"""
import pandas as pd
import numpy as np
from pathlib import Path, PurePath
import shutil
import os
from datetime import datetime
from itertools import product
import time
import project_code
from project_code.fuel_prices_aeo import GetFuelPrices
from project_code.fleet import Fleet
from project_code.vehicle import Vehicle, sourceTypeID, regClassID, fuelTypeID
from project_code.direct_cost import DirectCost
from project_code.indirect_cost import IndirectCost, IndirectCostScalars
from project_code.operating_cost import DEFandFuelCost, RepairAndMaintenanceCost
from project_code.discounting import DiscountValues
from project_code.group_metrics import GroupMetrics
from project_code.calc_deltas import CalcDeltas
from project_code.emission_cost import EmissionCost
from project_code.doc_tables import DocTables
from project_code.estimated_age import EstimatedAge
from project_code.figures import CreateFigures


def inputs_filenames(input_files_pathlist):
    """
    :param input_files_pathlist: A list of those input files that are not modified in code.
    :type input_files_pathlist: List - currently hardcoded.
    :return: A list of input file paths - these will be copied directly to the output folder so that inputs and outputs end up bundled together in the output folder.
    """
    _filename_list = [PurePath(path).name for path in input_files_pathlist]
    return _filename_list


def reshape_df(df, value_variable_list, cols_to_melt, melted_header, new_column_name):
    """

    :param df: Data to melt.
    :type df: DataFrame
    :param value_variable_list: Column(s) to use as identifier variables.
    :type value_variable_list: List
    :param cols_to_melt: Column(s) to unpivot (melt).
    :type cols_to_melt: List - this is a list of columns determined in code that are to be melted.
    :param melted_header: The header for the column to be populated with the cols_to_melt list.
    :type melted_header: String
    :param new_column_name: Name to use for the ‘Value’ column.
    :type new_column_name: String
    :return: A new DataFrame in long and narrow shape rather than the passed short and wide shape.
    """
    df = df.melt(id_vars=value_variable_list,
                 value_vars=cols_to_melt, var_name=melted_header,
                 value_name=new_column_name)
    return df


def convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args):
    """

    This function converts dollars into a consistent dollar basis as set in the Inputs workbook.
    :param df: The passed DataFrame containing costs to convert.
    :param deflators: A dictionary of gdp price deflators and adjustments to be multiplied by costs.
    :param dollar_basis: The dollar basis of the analysis.
    :param args: Metrics to be converted to dollar_basis dollars.
    :return: The passed DataFrame with metric dollar values converted to dollar_basis dollars.
    """
    dollar_years = pd.Series(pd.DataFrame(df.loc[df['DollarBasis'] > 1])['DollarBasis']).unique()
    for year in dollar_years:
        for arg in args:
            df.loc[df['DollarBasis'] == year, arg] = df[arg] * deflators[year]['adjustment']
        df.loc[df['DollarBasis'] == year, 'DollarBasis'] = dollar_basis
    return df


def weighted_result(df, metric, weightby_metric, veh, year_metric, year_list, max_age_included):
    """

    :param df: DataFrame containing values to be weighted.
    :param metric: The specific metric (or series) of data to be weighted.
    :param weightby_metric:  The metric by which the data is being weighted.
    :param veh: The specific vehicle (tuple) for which weighting is requested.
    :param year_metric:  "yearID" or "modelYearID"
    :param year_list: List of years for which weighted results are requested.
    :param max_age_included: The age through which data is to be weighted (i.e., can be less than full life)
    :return: DataFrame containing weighted results for the passed vehicle.
    """
    if len(veh) == 3:
        veh_id = 'alt_rc_ft'
    elif len(veh) == 4:
        veh_id = 'alt_st_rc_ft'
    else:
        veh_id = 'alt_st_rc_ft_zg'
    weighted_results = dict()
    for year in year_list:
        df_temp = pd.DataFrame(df.loc[(df[veh_id] == veh) & (df[year_metric] == year) & (df['ageID'] <= max_age_included), :])
        weighted_value = (df_temp[metric] * df_temp[weightby_metric]).sum() / df_temp[weightby_metric].sum()
        weighted_results[year] = weighted_value
    return weighted_results


def round_metrics(df, metrics, round_by):
    """

    :param df: DataFrame containing data to be rounded.
    :param metrics: List of metrics within the passed DataFrame for which rounding is requested.
    :param round_by: A value entered via the BCA_Inputs sheet contained in the inputs folder that sets the level of rounding.
    :return: The passed DataFrame with 'metrics' rounded by 'round_by'
    """
    df[metrics] = df[metrics].round(round_by)
    return df


def get_file_datetime(list_of_files):
    file_datetime = pd.DataFrame()
    file_datetime.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
    file_datetime.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])
    return file_datetime


def main():
    """The main script."""
    PATH_PROJECT = Path.cwd()

    # first, set the output files desired for QA/QC work
    TEST_RUN = input('Use full CTI BCA inputs (<ENTER>) or use test inputs (t)?\n')
    if TEST_RUN == 't':
        PATH_INPUTS = PATH_PROJECT.joinpath('test/inputs')
        PATH_OUTPUTS = PATH_PROJECT.joinpath('test/outputs')
    else:
        PATH_INPUTS = PATH_PROJECT.joinpath('inputs')
        PATH_OUTPUTS = PATH_PROJECT.joinpath('outputs')
    RUN_FOLDER_IDENTIFIER = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
    RUN_FOLDER_IDENTIFIER = RUN_FOLDER_IDENTIFIER if RUN_FOLDER_IDENTIFIER != '' else 'BCA-Results'
    CREATE_ALL_FILES = input('Create all output files? (y)es or (n)o?\n')
    start_time = time.time()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    print(f'\nStart date and time:  {start_time_readable}\n')
    print(f'\nCTI BCA tool version: {project_code.__version__}\n')
    run_settings_file = PATH_INPUTS.joinpath('1_RunSettings.csv')
    bca_inputs_file = PATH_INPUTS.joinpath('BCA_General_Inputs.csv')
    regclass_costs_file = PATH_INPUTS.joinpath('DirectCostInputs_byRegClass_byFuelType.csv')
    regclass_learningscalars_file = PATH_INPUTS.joinpath('LearningRateScalars_byRegClass.csv')
    markups_file = PATH_INPUTS.joinpath('IndirectCostInputs_byFuelType.csv')
    warranty_inputs_file = PATH_INPUTS.joinpath('Warranty_Inputs.csv')
    usefullife_inputs_file = PATH_INPUTS.joinpath('UsefulLife_Inputs.csv')
    moves_file = PATH_INPUTS.joinpath('CTI_NPRM_CY2027_2045_NewGRID_for_Todd_withORVRcorrection.csv')
    moves_adjustments_file = PATH_INPUTS.joinpath('MOVES_Adjustments.csv')
    options_file = PATH_INPUTS.joinpath('options.csv')
    def_doserate_inputs_file = PATH_INPUTS.joinpath('DEF_DoseRateInputs.csv')
    def_prices_file = PATH_INPUTS.joinpath('DEF_Prices.csv')
    orvr_fuelchange_file = PATH_INPUTS.joinpath('ORVR_FuelChangeInputs.csv')
    repair_and_maintenance_file = PATH_INPUTS.joinpath('Repair_and_Maintenance_Curve_Inputs.csv')
    gdp_deflators_file = PATH_INPUTS.joinpath('GDP_Deflators.csv')
    # add input files as needed for copy to path_to_results folder
    input_files_pathlist = [run_settings_file, bca_inputs_file, regclass_costs_file, regclass_learningscalars_file,
                            markups_file, moves_file, moves_adjustments_file, options_file,
                            def_doserate_inputs_file, def_prices_file, orvr_fuelchange_file, repair_and_maintenance_file,
                            gdp_deflators_file, warranty_inputs_file, usefullife_inputs_file]

    # read input files
    print("Reading input files....")
    start_time_read = time.time()
    bca_inputs = pd.read_csv(bca_inputs_file, index_col=0)
    regclass_costs = pd.read_csv(regclass_costs_file)
    regclass_learningscalars = pd.read_csv(regclass_learningscalars_file)
    markups = pd.read_csv(markups_file)
    warranty_inputs = pd.read_csv(warranty_inputs_file)
    usefullife_inputs = pd.read_csv(usefullife_inputs_file)
    moves = pd.read_csv(moves_file)
    moves_adjustments = pd.read_csv(moves_adjustments_file)
    options = pd.read_csv(options_file, index_col=0)
    options_dict = options.to_dict('index')
    def_doserate_inputs = pd.read_csv(def_doserate_inputs_file)
    def_prices = pd.read_csv(def_prices_file)
    orvr_fuelchanges = pd.read_csv(orvr_fuelchange_file)
    repair_and_maintenance = pd.read_csv(repair_and_maintenance_file, index_col=0)
    gdp_deflators = pd.read_csv(gdp_deflators_file, index_col=0)
    gdp_deflators.insert(len(gdp_deflators.columns), 'adjustment', 0)  # adjustment values are filled below

    for df in [markups, orvr_fuelchanges, regclass_costs, repair_and_maintenance]:
        try:
            df.drop('Notes', axis=1, inplace=True)
        except:
            pass

    elapsed_time_read = time.time() - start_time_read

    # get necessary inputs from the bca_inputs_file
    print("Doing the work....")
    start_time_calcs = time.time()
    aeo_case = bca_inputs.at['aeo_fuel_price_case', 'Value']
    discrate_social_low = pd.to_numeric(bca_inputs.at['discrate_social_low', 'Value'])
    discrate_social_high = pd.to_numeric(bca_inputs.at['discrate_social_high', 'Value'])
    discount_to_yearID = pd.to_numeric(bca_inputs.at['discount_to_yearID', 'Value'])
    costs_start = bca_inputs.at['costs_start', 'Value']
    learning_rate = pd.to_numeric(bca_inputs.at['learning_rate', 'Value'])
    dollar_basis_analysis = int(bca_inputs.at['dollar_basis_analysis', 'Value'])
    warranty_vmt_share = pd.to_numeric(bca_inputs.at['warranty_vmt_share', 'Value'])
    r_and_d_vmt_share = pd.to_numeric(bca_inputs.at['r_and_d_vmt_share', 'Value'])
    indirect_cost_scaling_metric = bca_inputs.at['scale_indirect_costs_by', 'Value']
    calc_pollution_effects = bca_inputs.at['calculate_pollution_effects', 'Value']
    calc_sourcetype_costs = bca_inputs.at['calculate_sourcetype_costs', 'Value']
    # round_moves_ustons_by = pd.to_numeric(bca_inputs.at['round_moves_ustons_by', 'Value'])
    round_costs_by = pd.to_numeric(bca_inputs.at['round_costs_by', 'Value'])
    def_gallons_perTonNOxReduction = pd.to_numeric(bca_inputs.at['def_gallons_perTonNOxReduction', 'Value'])
    weighted_operating_cost_years = bca_inputs.at['weighted_operating_cost_years', 'Value']
    weighted_operating_cost_years = weighted_operating_cost_years.split(',')
    for i, v in enumerate(weighted_operating_cost_years):
        weighted_operating_cost_years[i] = pd.to_numeric(weighted_operating_cost_years[i])
    techcost_summary_years = bca_inputs.at['techcost_summary_years', 'Value']
    techcost_summary_years = techcost_summary_years.split(',')
    for i, v in enumerate(techcost_summary_years):
        techcost_summary_years[i] = pd.to_numeric(techcost_summary_years[i])
    bca_summary_years = bca_inputs.at['bca_summary_years', 'Value']
    bca_summary_years = bca_summary_years.split(',')
    for i, v in enumerate(bca_summary_years):
        bca_summary_years[i] = pd.to_numeric(bca_summary_years[i])
    generate_emissionrepair_cpm_figures = bca_inputs.at['generate_emissionrepair_cpm_figures', 'Value']
    generate_BCA_ArgsByOption_figures = bca_inputs.at['generate_BCA_ArgsByOption_figures', 'Value']
    generate_BCA_ArgByOptions_figures = bca_inputs.at['generate_BCA_ArgByOptions_figures', 'Value']

    # how many alternatives are there? But first, be sure that optionID is the header for optionID.
    if 'Alternative' in moves.columns.tolist():
        moves.rename(columns={'Alternative': 'optionID'}, inplace=True)
    if 0 in moves['optionID']:
        number_alts = int(moves['optionID'].max()) + 1
    else:
        number_alts = int(moves['optionID'].max())

    # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
    gdp_deflators = gdp_deflators.to_dict('index')
    for key in gdp_deflators:
        gdp_deflators[key]['adjustment'] = gdp_deflators[dollar_basis_analysis]['factor'] / gdp_deflators[key]['factor']
    regclass_costs_years = [col for col in regclass_costs.columns if '20' in col]
    convert_dollars_to_analysis_basis(regclass_costs, gdp_deflators, dollar_basis_analysis, [step for step in regclass_costs_years])
    convert_dollars_to_analysis_basis(def_prices, gdp_deflators, dollar_basis_analysis, 'DEF_USDperGal')
    convert_dollars_to_analysis_basis(repair_and_maintenance, gdp_deflators, dollar_basis_analysis, 'Value')

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

    fuel_prices = GetFuelPrices(PATH_PROJECT, aeo_case)
    fuel_prices = fuel_prices.get_fuel_prices()

    # Calculate the Indirect Cost scalars based on the warranty_inputs and usefullife_inputs
    warranty_scalars = IndirectCostScalars(warranty_inputs, 'Warranty', indirect_cost_scaling_metric)
    warranty_scalars = warranty_scalars.calc_scalars_absolute()
    usefullife_scalars = IndirectCostScalars(usefullife_inputs, 'RnD', indirect_cost_scaling_metric)
    usefullife_scalars = usefullife_scalars.calc_scalars_relative()
    markups_vmt_scalars = pd.concat([warranty_scalars, usefullife_scalars], ignore_index=True, axis=0)
    markups_vmt_scalars.reset_index(drop=True, inplace=True)

    # Now, reshape some of the inputs for easier use
    warranty_miles_reshaped = reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                         [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Miles')
    warranty_age_reshaped = reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                       [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Age')
    usefullife_miles_reshaped = reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                           [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Miles')
    usefullife_age_reshaped = reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                         [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Age')
    markups_vmt_scalars_reshaped = reshape_df(markups_vmt_scalars, ['optionID', 'regClassID', 'fuelTypeID', 'Markup_Factor'],
                                              [col for col in markups_vmt_scalars.columns if '20' in col], 'yearID', 'Value')
    warranty_miles_reshaped['modelYearID'] = pd.to_numeric(warranty_miles_reshaped['modelYearID'])
    warranty_age_reshaped['modelYearID'] = pd.to_numeric(warranty_age_reshaped['modelYearID'])
    usefullife_miles_reshaped['modelYearID'] = pd.to_numeric(usefullife_miles_reshaped['modelYearID'])
    usefullife_age_reshaped['modelYearID'] = pd.to_numeric(usefullife_age_reshaped['modelYearID'])
    markups_vmt_scalars_reshaped['yearID'] = pd.to_numeric(markups_vmt_scalars_reshaped['yearID'])

    # read and reshape criteria costs if pollution effects are being calculated
    if calc_pollution_effects == 'Y':
        criteria_emission_costs_file = PATH_INPUTS.joinpath('CriteriaEmissionCost_Inputs.csv')
        criteria_emission_costs = pd.read_csv(criteria_emission_costs_file)
        tailpipe_emission_costs_list = [col for col in criteria_emission_costs.columns if 'onroad' in col]
        criteria_emission_costs_reshaped = reshape_df(criteria_emission_costs, ['yearID', 'MortalityEstimate', 'DR', 'fuelTypeID', 'DollarBasis'],
                                                      tailpipe_emission_costs_list, 'Pollutant_source', 'USDpUSton')
        criteria_emission_costs_reshaped.insert(1, 'Key', '')
        criteria_emission_costs_reshaped['Key'] = criteria_emission_costs_reshaped['Pollutant_source'] + '_' \
                                                  + criteria_emission_costs_reshaped['MortalityEstimate'] + '_' \
                                                  + criteria_emission_costs_reshaped['DR'].map(str)
        input_files_pathlist += [criteria_emission_costs_file]

    # add the identifier metrics, alt_rc_ft and alt_st_rc_ft, to specific DataFrames
    for df in [regclass_costs, regclass_learningscalars, moves, moves_adjustments]:
        df = Fleet(df).define_bca_regclass()
    moves = Fleet(moves).define_bca_sourcetype()

    # adjust MOVES VPOP/VMT/Gallons to reflect what's included in CTI (excluding what's not in CTI)
    moves_adjusted = Fleet(moves).adjust_moves(moves_adjustments) # adjust (41, 2) to be engine cert only
    moves_adjusted = moves_adjusted.loc[(moves_adjusted['regClassID'] != 41) | (moves_adjusted['fuelTypeID'] != 1), :] # eliminate (41, 1) keeping (41, 2)
    moves_adjusted = moves_adjusted.loc[moves_adjusted['regClassID'] != 49, :] # eliminate Gliders
    moves_adjusted = moves_adjusted.loc[moves_adjusted['fuelTypeID'] != 5, :]  # eliminate E85
    moves_adjusted = moves_adjusted.loc[moves_adjusted['regClassID'] >= 41, :]  # eliminate non-CTI regclasses
    cols = [col for col in moves_adjusted.columns if 'PM25' in col]
    moves_adjusted.insert(len(moves_adjusted.columns), 'PM25_onroad', moves_adjusted[cols].sum(axis=1)) # sum PM25 metrics
    moves_adjusted.insert(len(moves_adjusted.columns), 'ageID', moves_adjusted['yearID'] - moves_adjusted['modelYearID'])
    moves_adjusted.rename(columns={'NOx_UStons': 'NOx_onroad'}, inplace=True)
    moves_adjusted.reset_index(drop=True, inplace=True)

    # add VMT/vehicle & Gallons/mile metrics to moves dataframe
    moves_adjusted.insert(len(moves_adjusted.columns), 'VMT_AvgPerVeh', moves_adjusted['VMT'] / moves_adjusted['VPOP'])
    moves_adjusted = moves_adjusted.join(GroupMetrics(moves_adjusted, ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID']).group_cumsum(['VMT_AvgPerVeh']))
    moves_adjusted.insert(len(moves_adjusted.columns), 'MPG_AvgPerVeh', moves_adjusted['VMT'] / moves_adjusted['Gallons'])

    # pass moves thru Fleet.sales to get sales (population ageID=0) of everything in the moves runs by both sourcetype and by regclass
    sales_moves = Fleet(moves_adjusted).sales()

    # determine the earliest model year for which MOVES runs have ageID=0 data (i.e., where does BCA start?)
    year_min = sales_moves.loc[sales_moves['ageID'] == 0, 'yearID'].min()

    # calculate the direct mfg costs by passing vehicles, package costs/pens, sales and learning metrics thru the DirectCost class
    print('Working on tech package costs....')
    pkg_directcost_veh_regclass_dict = dict()
    sales_for_learning = dict()
    rc_ft_age0 = dict()
    for step in regclass_costs_years:
        sales_for_learning[step] = Fleet(moves_adjusted.loc[moves_adjusted['modelYearID'] >= pd.to_numeric(step)]).sales_by_alt_rc_ft()
        rc_ft_age0[step] = pd.Series(sales_for_learning[step]['alt_rc_ft']).unique()
    # Apply learning to direct costs
    for step, veh in product(regclass_costs_years, rc_ft_age0[step]):
        pkg_cost_veh_regclass = DirectCost(veh).pkg_cost_vehicle_regclass1(regclass_costs, step)
        pkg_seedvol = DirectCost(veh).seedvol_factor_regclass(regclass_learningscalars)
        pkg_sales_vol_scalar = DirectCost(veh).cumulative_sales_scalar_regclass(regclass_learningscalars)
        pkg_directcost_veh_regclass_dict[veh, step] = DirectCost(veh).pkg_cost_regclass_withlearning(sales_for_learning[step], step, pkg_cost_veh_regclass,
                                                                                                     pkg_seedvol, pkg_sales_vol_scalar, learning_rate)

    # Now merge the steps into a single DataFrame so that the costs can be summed into a single cost series. An outer merge is used in case there are different vehicles (unlikely).
    rc_ft_age0 = pd.Series(sales_moves['alt_rc_ft']).unique()
    for veh in rc_ft_age0:
        pkg_directcost_veh_regclass_dict[veh] = pkg_directcost_veh_regclass_dict[veh, regclass_costs_years[0]].copy()
        pkg_directcost_veh_regclass_dict[veh]['DirectCost_AvgPerVeh_' + regclass_costs_years[0]].fillna(0, inplace=True)
        pkg_directcost_veh_regclass_dict[veh]['DirectCost_TotalCost_' + regclass_costs_years[0]].fillna(0, inplace=True)
        for step_number in range(1, len(regclass_costs_years)):
            step = regclass_costs_years[step_number]
            pkg_directcost_veh_regclass_dict[veh] = pkg_directcost_veh_regclass_dict[veh].merge(pkg_directcost_veh_regclass_dict[veh, step],
                                                                                                on=['optionID', 'regClassID', 'fuelTypeID',
                                                                                                    'yearID', 'modelYearID', 'ageID', 'alt_rc_ft', 'VPOP',
                                                                                                    'SeedVolumeFactor', 'SalesVolumeScalar'],
                                                                                                how='outer')
            pkg_directcost_veh_regclass_dict[veh]['DirectCost_AvgPerVeh_' + step].fillna(0, inplace=True)
            pkg_directcost_veh_regclass_dict[veh]['DirectCost_TotalCost_' + step].fillna(0, inplace=True)
            pkg_directcost_veh_regclass_dict[veh].insert(1, 'Vehicle_Name_RC', Vehicle(veh).name_regclass())
    # Since subsequent steps are incremental to prior steps, now sum the steps.
    for veh in rc_ft_age0:
        pkg_directcost_veh_regclass_dict[veh].insert(len(pkg_directcost_veh_regclass_dict[veh].columns), 'DirectCost_AvgPerVeh', 0)
        pkg_directcost_veh_regclass_dict[veh].insert(len(pkg_directcost_veh_regclass_dict[veh].columns), 'DirectCost_TotalCost', 0)
        for step in regclass_costs_years:
            pkg_directcost_veh_regclass_dict[veh]['DirectCost_AvgPerVeh'] += pkg_directcost_veh_regclass_dict[veh]['DirectCost_AvgPerVeh_' + step]
            pkg_directcost_veh_regclass_dict[veh]['DirectCost_TotalCost'] += pkg_directcost_veh_regclass_dict[veh]['DirectCost_TotalCost_' + step]

    # Since package costs for NoAction are absolute and for other options they are incremental to NoAction, add in NoAction costs
    rc_ft_age0_actions = pd.Series(sales_moves.loc[sales_moves['optionID'] > 0, 'alt_rc_ft']).unique()
    for veh in rc_ft_age0_actions:
        pkg_directcost_veh_regclass_dict[veh]['DirectCost_AvgPerVeh'] = pkg_directcost_veh_regclass_dict[veh]['DirectCost_AvgPerVeh'] \
                                                                        + pkg_directcost_veh_regclass_dict[(0, veh[1], veh[2])]['DirectCost_AvgPerVeh']

    # create DataFrame into which the individual DataFrames in the above dictionaries can be appended
    directcost_regclass = pd.DataFrame()
    for veh in rc_ft_age0:
        directcost_regclass = pd.concat([directcost_regclass, pkg_directcost_veh_regclass_dict[veh]], axis=0, ignore_index=True)

    # fleet_bca created here - the fleet of relevance to the bca, so >= starting MY
    fleet_bca = moves_adjusted.copy()
    fleet_bca = pd.DataFrame(fleet_bca.loc[fleet_bca['modelYearID'] >= year_min])
    fleet_bca.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    fleet_bca.reset_index(drop=True, inplace=True)
    sales_bca = Fleet(fleet_bca).sales()

    # merge the DataFrames into a new DataFrame, create and calculate some new metrics, drop some metrics
    directcost_regclass.drop(columns=['VPOP'], inplace=True) # this VPOP is now summed by regclass but we want sourcetype VPOP
    cols = ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'alt_st_rc_ft', 'alt_rc_ft', 'yearID', 'modelYearID', 'ageID', 'VPOP']
    directcost_bca = sales_bca[cols].merge(directcost_regclass, on=['optionID', 'regClassID', 'fuelTypeID', 'alt_rc_ft', 'yearID', 'modelYearID', 'ageID'], how='left', sort='False')
    directcost_bca.loc[directcost_bca['VPOP'] == 0, 'DirectCost_AvgPerVeh'] = 0
    directcost_bca['DirectCost_TotalCost'] = directcost_bca[['DirectCost_AvgPerVeh', 'VPOP']].product(axis=1)
    directcost_bca.reset_index(drop=True, inplace=True)

    # merge markups and direct costs
    markups_merged = IndirectCost(directcost_bca).merge_markups_and_directcosts(markups, ['optionID', 'regClassID', 'fuelTypeID', 'yearID'])
    markups_merged = IndirectCost(markups_merged).merge_vmt_scalars(markups_vmt_scalars_reshaped, ['optionID', 'regClassID', 'fuelTypeID', 'yearID'])
    markups_merged.ffill(inplace=True)
    markups_merged.reset_index(drop=True, inplace=True)

    # pass directcosts_bca thru the IndirectCost class and apply the markups to get new dataframe that includes indirect costs
    techcost = IndirectCost(directcost_bca).indirect_cost_scaled(markups_merged, 'Warranty', warranty_vmt_share)
    techcost = IndirectCost(techcost).indirect_cost_scaled(markups_merged, 'RnD', r_and_d_vmt_share)
    techcost = IndirectCost(techcost).indirect_cost_unscaled(markups_merged)
    techcost = IndirectCost(techcost).indirect_cost_sum()
    techcost.insert(len(techcost.columns), 'TechCost_AvgPerVeh', techcost['DirectCost_AvgPerVeh'] + techcost['IndirectCost_AvgPerVeh'])
    techcost.insert(len(techcost.columns), 'TechCost_TotalCost', techcost['DirectCost_TotalCost'] + techcost['IndirectCost_TotalCost'])
    techcost_metrics_to_discount = [col for col in techcost.columns if 'Cost' in col]

    # work on pollution damage costs
    if calc_pollution_effects == 'Y':
        print('Working on pollution costs....')
        cols = ['optionID', 'yearID', 'modelYearID', 'ageID',
                'sourceTypeID', 'regClassID', 'fuelTypeID',
                'alt_st_rc_ft', 'alt_rc_ft',
                'PM25_onroad', 'NOx_onroad']
        emission_costs = pd.DataFrame(fleet_bca, columns=cols)
        emission_cost_calcs = EmissionCost(emission_costs, criteria_emission_costs_reshaped)
        emission_costs = emission_cost_calcs.calc_criteria_emission_costs_df()
        criteria_costs_list = [col for col in emission_costs.columns if 'CriteriaCost' in col]
        criteria_costs_list_3 = [col for col in emission_costs.columns if 'CriteriaCost' in col and '0.03' in col]
        criteria_costs_list_7 = [col for col in emission_costs.columns if 'CriteriaCost' in col and '0.07' in col]
        tailpipe_emission_costs_list = [col for col in emission_costs.columns if 'Cost_onroad' in col]
        tailpipe_emission_costs_list_3 = [col for col in emission_costs.columns if 'Cost_onroad' in col and '0.03' in col]
        tailpipe_emission_costs_list_7 = [col for col in emission_costs.columns if 'Cost_onroad' in col and '0.07' in col]
        criteria_and_tailpipe_emission_costs_list = criteria_costs_list + tailpipe_emission_costs_list

    # work on operating costs
    # create DataFrame and then adjust MOVES fuel consumption as needed
    print('Working on operating costs....')
    cols = ['optionID', 'yearID', 'modelYearID', 'ageID',
            'sourceTypeID', 'regClassID', 'fuelTypeID',
            'alt_st_rc_ft', 'alt_rc_ft',
            'Gallons', 'MPG_AvgPerVeh', 'VMT', 'VMT_AvgPerVeh', 'VMT_AvgPerVeh_CumSum',
            'THC_UStons', 'NOx_onroad']
    operating_costs = pd.DataFrame(fleet_bca, columns=cols)
    # determine sourcetype-based estimated ages when warranty and useful life are reached
    repair_warranty_ages = EstimatedAge(operating_costs).ages_by_identifier(warranty_miles_reshaped, warranty_age_reshaped, typical_vmt_thru_age, 'Warranty')
    repair_usefullife_ages = EstimatedAge(operating_costs).ages_by_identifier(usefullife_miles_reshaped, usefullife_age_reshaped, typical_vmt_thru_age, 'UsefulLife')
    # merge in the estimated warranty and useful life ages for estimating repair costs
    for df in [repair_warranty_ages, repair_usefullife_ages]:
        operating_costs = operating_costs.merge(df, on=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'], how='left')
    # for those MYs without ageID data within the range specified in BCA_Inputs, we'll do a forward fill to fill their data with the last MY having ageID data within the range
    operating_costs.loc[operating_costs['modelYearID'] >= operating_costs['modelYearID'].max() - typical_vmt_thru_age] = \
        operating_costs.loc[operating_costs['modelYearID'] >= operating_costs['modelYearID'].max() - typical_vmt_thru_age].ffill(axis=0)
    emission_repair_cost_calcs = RepairAndMaintenanceCost(operating_costs, metrics_repair_and_maint_dict, pkg_directcost_veh_regclass_dict)
    operating_costs = emission_repair_cost_calcs.emission_repair_costs()
    get_nox_reductions = CalcDeltas(operating_costs, number_alts, ['NOx_onroad'])
    operating_costs = get_nox_reductions.calc_delta_and_keep_alt_id()
    operating_costs = DEFandFuelCost(operating_costs).orvr_fuel_impacts_mlpergram(orvr_fuelchanges, calc_sourcetype_costs)
    def_doserates = DEFandFuelCost(def_doserate_inputs).def_doserate_scaling_factor()
    operating_costs = DEFandFuelCost(operating_costs).def_cost_df(def_doserates, def_prices, def_gallons_perTonNOxReduction)
    operating_costs = DEFandFuelCost(operating_costs).fuel_costs(fuel_prices)
    cols_owner = ['EmissionRepairCost_Owner_TotalCost', 'UreaCost_TotalCost', 'FuelCost_Retail_TotalCost']
    cols_bca = ['EmissionRepairCost_Owner_TotalCost', 'UreaCost_TotalCost', 'FuelCost_Pretax_TotalCost']
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_Owner_TotalCost', operating_costs[cols_owner].sum(axis=1))
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_BCA_TotalCost', operating_costs[cols_bca].sum(axis=1))
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_Owner_AvgPerMile', operating_costs['OperatingCost_Owner_TotalCost'] / operating_costs['VMT'])
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_Owner_AvgPerVeh', operating_costs[['OperatingCost_Owner_AvgPerMile', 'VMT_AvgPerVeh']].product(axis=1))
    operatingcost_metrics_to_discount = [col for col in operating_costs.columns if 'Cost' in col]

    # now create some weighted results of operating costs
    vehs_operating_costs = pd.Series(operating_costs['alt_st_rc_ft']).unique()
    vehs_operating_rc_costs = pd.Series(operating_costs['alt_rc_ft']).unique()
    weighted_repair_owner_cpm = dict()
    weighted_def_cpm = dict()
    weighted_fuel_cpm = dict()
    if TEST_RUN == 't':
        year_list = [2027, 2030]
    else:
        year_list = weighted_operating_cost_years
    max_age_included = 9
    for veh in vehs_operating_costs:
        weighted_def_cpm[veh] = weighted_result(operating_costs, 'UreaCost_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
        weighted_fuel_cpm[veh] = weighted_result(operating_costs, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
        weighted_repair_owner_cpm[veh] = weighted_result(operating_costs, 'EmissionRepairCost_Owner_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
    for veh in vehs_operating_rc_costs:
        pass
    weighted_repair_owner_cpm_df = pd.DataFrame(weighted_repair_owner_cpm).transpose()
    weighted_def_cpm_df = pd.DataFrame(weighted_def_cpm).transpose()
    weighted_fuel_cpm_df = pd.DataFrame(weighted_fuel_cpm).transpose()

    # and now put the MOVES name identifier in the operating_costs DataFrame
    operating_costs.insert(operating_costs.columns.get_loc('fuelTypeID') + 1, 'Vehicle_Name_MOVES', '')
    for veh in vehs_operating_costs:
        operating_costs.loc[operating_costs['alt_st_rc_ft'] == veh, 'Vehicle_Name_MOVES'] = Vehicle(veh).name_moves()

    # pass each DataFrame thru the DiscountValues class and pass the list of metrics to be discounted for each thru the discount method
    print('Working on discounting monetized values....')
    techcost_dict = dict()
    emission_costs_dict = dict()
    operating_costs_dict = dict()
    for dr in [0, discrate_social_low, discrate_social_high]:
        techcost_dict[dr] = DiscountValues(techcost, techcost_metrics_to_discount, discount_to_yearID, costs_start)
        techcost_dict[dr] = techcost_dict[dr].discount(dr)
        operating_costs_dict[dr] = DiscountValues(operating_costs, operatingcost_metrics_to_discount, discount_to_yearID, costs_start)
        operating_costs_dict[dr] = operating_costs_dict[dr].discount(dr)
        if calc_pollution_effects == 'Y':
            emission_costs_dict[dr] = DiscountValues(emission_costs, criteria_and_tailpipe_emission_costs_list, discount_to_yearID, costs_start)
            emission_costs_dict[dr] = emission_costs_dict[dr].discount(dr)

    # now set to NaN discounted pollutant values using discount rates that are not consistent with the input values
    if calc_pollution_effects == 'Y':
        for col in criteria_costs_list_3:
            emission_costs_dict[0.07][col] = np.nan
        for col in criteria_costs_list_7:
            emission_costs_dict[0.03][col] = np.nan
        for col in tailpipe_emission_costs_list_3:
            emission_costs_dict[0.07][col] = np.nan
        for col in tailpipe_emission_costs_list_7:
            emission_costs_dict[0.03][col] = np.nan

    print('Working on benefit-cost analysis results and summarizing things....')
    bca_costs_dict = dict()
    techcost_metrics_for_bca = ['optionID', 'yearID', 'modelYearID', 'ageID',
                                'sourceTypeID', 'regClassID', 'fuelTypeID', 'Vehicle_Name_RC',
                                'DirectCost_TotalCost', 'WarrantyCost_TotalCost', 'RnDCost_TotalCost', 'OtherCost_TotalCost', 'ProfitCost_TotalCost',
                                'IndirectCost_TotalCost', 'TechCost_TotalCost']
    operating_metrics_for_bca = ['optionID', 'yearID', 'modelYearID', 'ageID',
                                 'sourceTypeID', 'regClassID', 'fuelTypeID', 'Vehicle_Name_MOVES'] \
                                + operatingcost_metrics_to_discount
    merge_metrics = ['optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID']
    cols = ['optionID', 'yearID', 'modelYearID', 'ageID',
            'sourceTypeID', 'regClassID', 'fuelTypeID']
    for dr in [0, discrate_social_low, discrate_social_high]:
        bca_costs_dict[dr] = pd.DataFrame(fleet_bca, columns=cols)
        bca_costs_dict[dr] = bca_costs_dict[dr].merge(techcost_dict[dr][techcost_metrics_for_bca], on=merge_metrics, how='left')
        bca_costs_dict[dr] = bca_costs_dict[dr].merge(operating_costs_dict[dr][operating_metrics_for_bca], on=merge_metrics, how='left')
        if calc_pollution_effects == 'Y':
            pollution_metrics_for_bca = ['optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID'] \
                                        + criteria_and_tailpipe_emission_costs_list
            bca_costs_dict[dr] = bca_costs_dict[dr].merge(emission_costs_dict[dr][pollution_metrics_for_bca], on=merge_metrics, how='left')
        bca_costs_dict[dr].insert(0, 'DiscountRate', dr)

    bca_costs = pd.DataFrame()
    for dr in [0, discrate_social_low, discrate_social_high]:
        bca_costs = pd.concat([bca_costs, bca_costs_dict[dr]], axis=0, ignore_index=True)

    # add some total cost columns
    bca_costs.insert(len(bca_costs.columns), 'TechAndOperatingCost_BCA_TotalCost', bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost']].sum(axis=1))
    if calc_pollution_effects == 'Y':
        for dr, mort_est in product([0.03, 0.07], ['low', 'high']):
            bca_costs.insert(len(bca_costs.columns), 'TotalCost_' + mort_est + '_' + str(dr),
                             bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(dr)]].sum(axis=1))
    else:
        pass
        # bca_costs.insert(len(bca_costs.columns), 'TotalCost', bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost']].sum(axis=1))
    # adjust the 3 and 7 DR total costs as needed
    if calc_pollution_effects == 'Y':
        for mort_est in ['low', 'high']:
            bca_costs.loc[bca_costs['DiscountRate'] == 0.03, 'TotalCost_' + mort_est + '_' + str(0.03)] \
                = bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(0.03)]].sum(axis=1)
            bca_costs.loc[bca_costs['DiscountRate'] == 0.03, 'TotalCost_' + mort_est + '_' + str(0.07)] = np.nan
            bca_costs.loc[bca_costs['DiscountRate'] == 0.07, 'TotalCost_' + mort_est + '_' + str(0.07)] \
                = bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(0.07)]].sum(axis=1)
            bca_costs.loc[bca_costs['DiscountRate'] == 0.07, 'TotalCost_' + mort_est + '_' + str(0.03)] = np.nan

    # pull different discount rates together
    techcost_all, emission_costs_all, operating_costs_all = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    for dr in [0, discrate_social_low, discrate_social_high]:
        techcost_all = pd.concat([techcost_all, techcost_dict[dr]], axis=0, ignore_index=True)
        operating_costs_all = pd.concat([operating_costs_all, operating_costs_dict[dr]], axis=0, ignore_index=True)
        if calc_pollution_effects == 'Y':
            emission_costs_all = pd.concat([emission_costs_all, emission_costs_dict[dr]], axis=0, ignore_index=True)

    # Since vehicle names were added via the DirectCost class, they exist only for age=0
    # So, now fill in some missing vehicle names for age>0, just for clarity.
    # bca_costs['Vehicle_Name_RC'].fillna(method='ffill', inplace=True)

    # Now add an OptionName column so that output files provide that information
    Fleet(techcost_all).insert_option_name(options_dict, number_alts)
    Fleet(operating_costs_all).insert_option_name(options_dict, number_alts)
    Fleet(bca_costs).insert_option_name(options_dict, number_alts)
    Fleet(moves_adjusted).insert_option_name(options_dict, number_alts)
    if calc_pollution_effects == 'Y':
        Fleet(emission_costs_all).insert_option_name(options_dict, number_alts)

    # now set a standard row header for use in grouping along with metrics to group
    techcost_metrics_to_sum = ['VPOP'] + [col for col in techcost_all.columns if 'TotalCost' in col]
    techcost_metrics_to_avg = [col for col in techcost_all.columns if 'AvgPerVeh' in col]
    operating_costs_metrics_to_sum = [col for col in operating_costs_all.columns if 'Gallons' in col or 'TotalCost' in col]
    operating_costs_metrics_to_avg = [col for col in operating_costs_all.columns if 'AvgPerVeh' in col or 'AvgPerMile' in col]
    bca_costs_metrics_to_sum = [col for col in bca_costs.columns if 'TotalCost' in col or 'low' in col or 'high' in col]
    if calc_pollution_effects == 'Y':
        emission_costs_metrics_to_sum = [col for col in emission_costs_all.columns if 'PM25' in col or 'NOx' in col or 'Criteria' in col]

    # create a dict of lists for passing thru grouping methods
    row_header_group = dict()
    common_metrics = ['optionID', 'OptionName', 'DiscountRate']
    row_header_group[1] = common_metrics + ['yearID']
    row_header_group[2] = common_metrics + ['yearID', 'regClassID', 'fuelTypeID']
    groups = 2 # increment this consistent with row_headers created
    if calc_sourcetype_costs == 'Y':
        row_header_group[3] = common_metrics + ['yearID', 'sourceTypeID', 'fuelTypeID']
        groups = 3 # increment this consistent with row_headers created

    row_header_group_cumsum = dict()
    row_header_group_cumsum[1] = common_metrics
    row_header_group_cumsum[2] = common_metrics + ['regClassID', 'fuelTypeID']
    if calc_sourcetype_costs == 'Y':
        row_header_group_cumsum[3] = common_metrics + ['sourceTypeID', 'fuelTypeID']

    # create some dicts to store the groupby.sum, groupby.cumsum and groupby.mean results
    techcost_sum = dict()
    techcost_mean = dict()
    techcost_summary = dict()
    emission_costs_sum = dict()
    operating_costs_sum = dict()
    operating_costs_mean = dict()
    operating_costs_summary = dict()
    bca_costs_sum = dict()
    for group in range(1, groups + 1):
        # first a groupby.sum, then a groupby.cumsum on the groupby.sum which is joined into the groupby.sum, then a groupby.mean, then a merge into one
        techcost_sum[group] = GroupMetrics(techcost_all, row_header_group[group]).group_sum(techcost_metrics_to_sum)
        techcost_mean[group] = GroupMetrics(techcost_all, row_header_group[group]).group_mean(techcost_metrics_to_avg)
        techcost_summary[group] = techcost_sum[group].merge(techcost_mean[group], on=row_header_group[group])

        operating_costs_sum[group] = GroupMetrics(operating_costs_all, row_header_group[group]).group_sum(operating_costs_metrics_to_sum)
        operating_costs_mean[group] = GroupMetrics(operating_costs_all, row_header_group[group]).group_mean(operating_costs_metrics_to_avg)
        operating_costs_summary[group] = operating_costs_sum[group].merge(operating_costs_mean[group], on=row_header_group[group])

        bca_costs_sum[group] = GroupMetrics(bca_costs, row_header_group[group]).group_sum(bca_costs_metrics_to_sum)
        bca_costs_sum[group] = bca_costs_sum[group].join(GroupMetrics(bca_costs_sum[group], row_header_group_cumsum[group]).group_cumsum(bca_costs_metrics_to_sum))

        if calc_pollution_effects == 'Y':
            emission_costs_sum[group] = GroupMetrics(emission_costs_all, row_header_group[group]).group_sum(emission_costs_metrics_to_sum)

    # now annualize the cumsum metrics
    for group in range(1, groups + 1):
        bca_costs_sum[group] = DiscountValues(bca_costs_sum[group], bca_costs_metrics_to_sum, discount_to_yearID, costs_start).annualize()

    # calc the deltas relative to alt0
    techcost_metrics_for_deltas = techcost_metrics_to_sum + techcost_metrics_to_avg
    operating_cost_metrics_for_deltas = operating_costs_metrics_to_sum + operating_costs_metrics_to_avg
    bca_costs_metrics_for_deltas = bca_costs_metrics_to_sum + [metric + '_CumSum' for metric in bca_costs_metrics_to_sum] \
                                   + [metric + '_Annualized' for metric in bca_costs_metrics_to_sum]
    for group in range(1, groups + 1):
        techcost_summary[group] = pd.concat([techcost_summary[group],
                                             CalcDeltas(techcost_summary[group], number_alts, techcost_metrics_for_deltas).calc_delta_and_new_alt_id()],
                                            axis=0, ignore_index=True)
        operating_costs_summary[group] = pd.concat([operating_costs_summary[group],
                                                    CalcDeltas(operating_costs_summary[group], number_alts, operating_cost_metrics_for_deltas).calc_delta_and_new_alt_id()],
                                                   axis=0, ignore_index=True)
        bca_costs_sum[group] = pd.concat([bca_costs_sum[group],
                                          CalcDeltas(bca_costs_sum[group], number_alts, bca_costs_metrics_for_deltas).calc_delta_and_new_alt_id()],
                                         axis=0, ignore_index=True)
        if calc_pollution_effects == 'Y':
            emission_costs_sum[group] = pd.concat([emission_costs_sum[group],
                                                   CalcDeltas(emission_costs_sum[group], number_alts, emission_costs_metrics_to_sum).calc_delta_and_new_alt_id()],
                                                  axis=0, ignore_index=True)

    # add some identifier columns to the grouped output files
    if calc_pollution_effects == 'Y':
        df_list = [techcost_summary, emission_costs_sum, operating_costs_summary, bca_costs_sum]
    else:
        df_list = [techcost_summary, operating_costs_summary, bca_costs_sum]
    for df in df_list: # inserts cols in techcost_summary[2], etc.
        df[2].insert(6, 'regclass', pd.Series(regClassID[number] for number in df[2]['regClassID']))
        df[2].insert(7, 'fueltype', pd.Series(fuelTypeID[number] for number in df[2]['fuelTypeID']))

    # calc the deltas relative to alt0 for the main DataFrames
    new_metrics = [metric for metric in operating_costs_all.columns if 'VMT' in metric or 'Warranty' in metric or 'Useful' in metric or 'tons' in metric]
    operating_cost_metrics_for_deltas = operating_cost_metrics_for_deltas + new_metrics
    operating_costs_all = pd.concat([operating_costs_all,
                                     CalcDeltas(operating_costs_all, number_alts, operating_cost_metrics_for_deltas).calc_delta_and_new_alt_id()],
                                    axis=0, ignore_index=True)
    bca_costs = pd.concat([bca_costs,
                           CalcDeltas(bca_costs, number_alts, [col for col in bca_costs.columns if 'Cost' in col]).calc_delta_and_new_alt_id()],
                          axis=0, ignore_index=True)
    if calc_pollution_effects == 'Y':
        emission_cost_metrics_for_deltas = criteria_and_tailpipe_emission_costs_list + ['PM25_onroad', 'NOx_onroad']
        emission_costs_all = pd.concat([emission_costs_all,
                                        CalcDeltas(emission_costs_all, number_alts, emission_cost_metrics_for_deltas).calc_delta_and_new_alt_id()],
                                       axis=0, ignore_index=True)

    # now do some rounding of monetized values
    techcosts_metrics_to_round = [metric for metric in techcost_all.columns if 'Cost' in metric]
    operating_costs_metrics_to_round = [metric for metric in operating_costs_all.columns if 'Cost' in metric and 'PerMile' not in metric]
    emission_costs_metrics_to_round = [metric for metric in emission_costs_all.columns if 'Cost' in metric]
    bca_costs_metrics_to_round = [metric for metric in bca_costs.columns if 'Cost' in metric and 'PerMile' not in metric]
    techcost_all = round_metrics(techcost_all, techcosts_metrics_to_round, round_costs_by)
    operating_costs_all = round_metrics(operating_costs_all, operating_costs_metrics_to_round, round_costs_by)
    emission_costs_all = round_metrics(emission_costs_all, emission_costs_metrics_to_round, round_costs_by)
    bca_costs = round_metrics(bca_costs, bca_costs_metrics_to_round, round_costs_by)

    elapsed_time_calcs = time.time() - start_time_calcs

    print("Saving the outputs....")
    start_time_outputs = time.time()

    # set results path in which to save all files created or used/copied by this module
    # and set output path in which to save all files created by this module; the output path will be in the results path
    # move this to earlier in main if results folder location is made user selectable so that the selection is made shortly after start of run
    PATH_OUTPUTS.mkdir(exist_ok=True)
    path_of_run_folder = PATH_OUTPUTS.joinpath(f'{start_time_readable}_CTI_{RUN_FOLDER_IDENTIFIER}')
    path_of_run_folder.mkdir(exist_ok=False)
    path_of_run_inputs_folder = path_of_run_folder.joinpath('run_inputs')
    path_of_run_inputs_folder.mkdir(exist_ok=False)
    path_of_run_results_folder = path_of_run_folder.joinpath('run_results')
    path_of_run_results_folder.mkdir(exist_ok=False)
    path_of_modified_inputs_folder = path_of_run_folder.joinpath('modified_inputs')
    path_of_modified_inputs_folder.mkdir(exist_ok=False)

    # first build some high level summary tables for copy/paste into slides/documents/etc.
    techcost_per_veh_cols = ['DiscountRate', 'yearID', 'regclass', 'fueltype', 'OptionName'] + [col for col in techcost_summary[2] if 'AvgPerVeh' in col and 'ZG' not in col and '20' not in col]
    discount_rates = [0]
    techcost_years = techcost_summary_years
    regclasses = ['LHD', 'LHD45', 'MHD67', 'HHD8', 'Urban Bus']
    fueltypes = ['Diesel', 'Gasoline', 'CNG']
    techcost_per_veh_file = pd.ExcelWriter(path_of_run_results_folder.joinpath('techcosts_AvgPerVeh.xlsx'))
    DocTables(techcost_summary[2]).techcost_per_veh_table(discount_rates, techcost_years, regclasses, fueltypes, techcost_per_veh_cols, techcost_per_veh_file)
    techcost_per_veh_file.save()

    bca_cols = ['OptionName', 'DiscountRate', 'TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'TechAndOperatingCost_BCA_TotalCost']
    bca_years = bca_summary_years
    bca_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annual.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_costs_sum[1]).bca_yearID_tables('', 0, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.03', bca_years,
                                                      'billions', bca_cols, bca_annual)
    else:
        DocTables(bca_costs_sum[1]).bca_yearID_tables('', 0, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_annual)
    bca_annual.save()

    bca_npv = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_npv.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.03, 'CriteriaCost_low_0.03', 'CriteriaCost_high_0.03', bca_years,
                                                      'billions', bca_cols, bca_npv)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.07, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.07', bca_years,
                                                      'billions', bca_cols, bca_npv)
    else:
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.03, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_npv)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.07, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_npv)
    bca_npv.save()

    bca_annualized = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annualized.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.03, 'CriteriaCost_low_0.03', 'CriteriaCost_high_0.03', bca_years,
                                                      'billions', bca_cols, bca_annualized)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.07, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.07', bca_years,
                                                      'billions', bca_cols, bca_annualized)
    else:
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.03, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_annualized)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.07, 'TechAndOperatingCost_BCA_TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_annualized)
    bca_annualized.save()

    # note that the inventory tables created below include MY2027+ only since emission_costs_sum is based on fleet_bca
    if calc_pollution_effects == 'Y':
        inventory_cols = ['OptionName', 'yearID', 'PM25_onroad', 'NOx_onroad']
        inventory_years = bca_summary_years
        inventory_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('inventory_annual_IncludedModelYears.xlsx'))
        DocTables(emission_costs_sum[1]).inventory_tables1(inventory_years, inventory_cols, inventory_annual)
        inventory_annual.save()

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    inputs_filename_list = inputs_filenames(input_files_pathlist)
    if CREATE_ALL_FILES == 'y' or CREATE_ALL_FILES == 'Y' or CREATE_ALL_FILES == '':
        for file in inputs_filename_list:
            path_source = PATH_INPUTS.joinpath(file)
            path_destination = path_of_run_inputs_folder.joinpath(file)
            shutil.copy2(path_source, path_destination)
        fuel_prices.to_csv(path_of_modified_inputs_folder.joinpath('fuel_prices_' + aeo_case + '.csv'), index=False)
        regclass_costs.to_csv(path_of_modified_inputs_folder.joinpath('regclass_costs.csv'), index=False)
        markups_vmt_scalars_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('markups_vmt_scalars_reshaped.csv'), index=False)
        def_doserates.to_csv(path_of_modified_inputs_folder.joinpath('def_doserates.csv'), index=False)
        repair_and_maintenance.to_csv(path_of_modified_inputs_folder.joinpath('repair_and_maintenance.csv'), index=False)
        def_prices.to_csv(path_of_modified_inputs_folder.joinpath('def_prices.csv'), index=False)
        gdp_deflators = pd.DataFrame(gdp_deflators)  # from dict to df
        gdp_deflators.to_csv(path_of_modified_inputs_folder.joinpath('gdp_deflators.csv'), index=True)
        if calc_pollution_effects == 'Y':
            criteria_emission_costs_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('criteria_emission_costs_reshaped.csv'), index=False)

        # write some output files
        techcost_all.to_csv(path_of_run_results_folder.joinpath('techcosts.csv'), index=False)
        if calc_pollution_effects == 'Y':
            emission_costs_all.to_csv(path_of_run_results_folder.joinpath('criteria_emission_costs.csv'), index=False)

        operating_costs_all.to_csv(path_of_run_results_folder.joinpath('operating_costs.csv'), index=False)
        weighted_repair_owner_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_emission_repair_owner_cpm.csv'))
        weighted_def_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_urea_cpm.csv'))
        weighted_fuel_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_fuel_cpm.csv'))

        bca_costs.to_csv(path_of_run_results_folder.joinpath('bca_costs.csv'), index=False)
        bca_costs_sum[1].to_csv(path_of_run_results_folder.joinpath('bca_costs_by_yearID.csv'), index=False)

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
        alts = pd.Series(bca_costs.loc[bca_costs['optionID'] < 10, 'optionID']).unique()
        veh_names = pd.Series(bca_costs['Vehicle_Name_MOVES']).unique()
        for veh_name in veh_names:
            for cpm_figure_year in cpm_figure_years:
                CreateFigures(bca_costs, options_dict, path_figures).line_chart_vs_age(0, alts, cpm_figure_year, veh_name, 'EmissionRepairCost_Owner_AvgPerMile')

    if generate_BCA_ArgsByOption_figures == 'Y':
        yearID_min = int(bca_costs['yearID'].min())
        yearID_max = int(bca_costs['yearID'].max())
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(bca_costs.loc[bca_costs['optionID'] >= 10, 'optionID']).unique()
        for alt in alts:
            CreateFigures(bca_costs_sum[1], options_dict, path_figures).line_chart_args_by_option(0, alt, yearID_min, yearID_max,
                                                                                                  'TechCost_TotalCost',
                                                                                                  'EmissionRepairCost_Owner_TotalCost',
                                                                                                  'UreaCost_TotalCost',
                                                                                                  'FuelCost_Pretax_TotalCost',
                                                                                                  'TechAndOperatingCost_BCA_TotalCost'
                                                                                                  )
    if generate_BCA_ArgByOptions_figures == 'Y':
        yearID_min = int(bca_costs['yearID'].min())
        yearID_max = int(bca_costs['yearID'].max())
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(bca_costs.loc[bca_costs['optionID'] >= 10, 'optionID']).unique()
        args = ['TechCost_TotalCost',
                'EmissionRepairCost_Owner_TotalCost',
                'UreaCost_TotalCost',
                'FuelCost_Pretax_TotalCost',
                'TechAndOperatingCost_BCA_TotalCost'
                ]
        for arg in args:
            CreateFigures(bca_costs_sum[1], options_dict, path_figures).line_chart_arg_by_options(0, alts, yearID_min, yearID_max, arg)

    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder', 'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [project_code.__version__, path_of_run_folder, start_time_readable, elapsed_time_read, elapsed_time_calcs, elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log = pd.concat([summary_log, get_file_datetime(input_files_pathlist)], axis=0, sort=False, ignore_index=True)
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)


if __name__ == '__main__':
    main()
