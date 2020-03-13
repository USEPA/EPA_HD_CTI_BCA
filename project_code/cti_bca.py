"""
This is the primary module of the benefit cost analysis. This module reads input files, calls other modules and generates output files.
"""
import pandas as pd
import numpy as np
from pathlib import Path, PurePath
import shutil
# import os
from datetime import datetime
import time
# from tqdm import tqdm
# import input_output as io
# from importlib import reload # for qa/qc to reload modules after revising
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


PATH_PROJECT = Path.cwd()
PATH_PROJECT_CODE = PATH_PROJECT.joinpath('project_code')


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


def convert_dollars_to_bca_basis(df, deflators, dollar_basis_years, _metric, bca_dollar_basis):
    """Convert all input dollars values to a consistent dollar basis where that basis is the year for which the GDP Price Deflator is 1.

    :param df: Data containing dollars values for conversion.
    :type df: DataFrame
    :param deflators: The GDP price deflators entered in the BCA inputs file.
    :type deflators: Dictionary
    :param dollar_basis_years: The years for which input dollar values are based, as entered in the BCA inputs file.
    :type dollar_basis_years: List
    :param _metric: The column heading of the dollar values to be converted.
    :type _metric: String
    :param bca_dollar_basis: The basis year for the analysis - the year for which the GDP Price Deflator is 1.
    :type bca_dollar_basis: Integer
    :return: A DataFrame consisting of the passed data but with dollar values in a single dollar basis year.
    """
    for number in range(len(dollar_basis_years)):
        df.loc[df['DollarBasis'] == dollar_basis_years[number], _metric] = df[_metric] * deflators[number]
        df.loc[df['DollarBasis'] == dollar_basis_years[number], 'DollarBasis'] = bca_dollar_basis
    return df


def weighted_result(df, metric, weightby_metric, veh, year_metric, year_list, max_age_included):
    weighted_results = dict()
    for year in year_list:
        df_temp = pd.DataFrame(df.loc[(df['alt_rc_ft'] == veh) & (df[year_metric] == year) & (df['ageID'] <= max_age_included), :])
        weighted_value = (df_temp[metric] * df_temp[weightby_metric]).sum() / df_temp[weightby_metric].sum()
        weighted_results[year] = weighted_value
    return weighted_results


def round_metrics(df, metrics, round_by):
    df[metrics] = df[metrics].round(round_by)
    # for metric in metrics:
    #     df[metric].round(round_by)
    return df


def main():
    """The main script."""
    # first, set the output files desired for QA/QC work
    TEST_RUN = input('Use full CTI BCA inputs (<ENTER>) or use test inputs (t)?\n')
    if TEST_RUN == 't':
        PATH_INPUTS = PATH_PROJECT.joinpath('test/inputs')
        PATH_OUTPUTS = PATH_PROJECT.joinpath('test/outputs')
    else:
        PATH_INPUTS = PATH_PROJECT.joinpath('inputs')
        PATH_OUTPUTS = PATH_PROJECT.joinpath('outputs')
    RUN_FOLDER_IDENTIFIER = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
    RUN_FOLDER_IDENTIFIER = RUN_FOLDER_IDENTIFIER if RUN_FOLDER_IDENTIFIER != '' else 'HDCTI-BCA-Results'
    CREATE_ALL_FILES = input('Create all output files? (y)es or (n)o?\n')
    start_time = time.time()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    print(f'\nStart date and time:  {start_time_readable}\n')
    print(f'\nCTI BCA tool version: {project_code.__version__}\n')
    # these can be returned to interactive once further along, but for now just hardcoding the inputs
    run_settings_file = PATH_INPUTS.joinpath('1_RunSettings.csv')
    bca_inputs_file = PATH_INPUTS.joinpath('BCA_General_Inputs.csv')
    regclass_costs_file = PATH_INPUTS.joinpath('DirectCostInputs_byRegClass_byFuelType.csv')
    # regclass_techpens_file = PATH_INPUTS.joinpath('TechPackages_TechPens.csv')
    regclass_learningscalars_file = PATH_INPUTS.joinpath('LearningRateScalars_byRegClass.csv')
    # sourcetype_costs_file = PATH_INPUTS.joinpath('DirectCostInputs_bySourcetype_no_0gtech.csv')
    sourcetype_costs_file = PATH_INPUTS.joinpath('DirectCostInputs_bySourcetype.csv')
    markups_file = PATH_INPUTS.joinpath('IndirectCostInputs_byFuelType.csv')
    # markups_vmt_scalars_file = PATH_INPUTS.joinpath('IndirectCostInputs_VMTscalars_byRegClass_byFuelType.csv')
    warranty_inputs_file = PATH_INPUTS.joinpath('Warranty_Inputs.csv')
    usefullife_inputs_file = PATH_INPUTS.joinpath('UsefulLife_Inputs.csv')
    # markups_sourcetype_file = PATH_INPUTS.joinpath('IndirectCostInputs_bySourcetype.csv')
    moves_file = PATH_INPUTS.joinpath('CTI_NPRM_CY2027_2045_NewGRID_for_Todd.csv')
    moves_adjustments_file = PATH_INPUTS.joinpath('MOVES_Adjustments.csv')
    options_file = PATH_INPUTS.joinpath('options.csv')
    def_doserate_inputs_file = PATH_INPUTS.joinpath('DEF_DoseRateInputs.csv')
    def_prices_file = PATH_INPUTS.joinpath('DEF_Prices.csv')
    orvr_fuelchange_file = PATH_INPUTS.joinpath('ORVR_FuelChangeInputs.csv')
    repair_and_maintenance_file = PATH_INPUTS.joinpath('Repair_and_Maintenance_Curve_Inputs.csv')
    # add input files as needed for copy to path_to_results folder
    input_files_pathlist = [run_settings_file, bca_inputs_file, regclass_costs_file, regclass_learningscalars_file,
                            markups_file, sourcetype_costs_file, moves_file, moves_adjustments_file, options_file,
                            def_doserate_inputs_file, orvr_fuelchange_file, repair_and_maintenance_file, warranty_inputs_file, usefullife_inputs_file]

    # read input files
    print("Reading input files....")
    start_time_read = time.time()
    bca_inputs = pd.read_csv(bca_inputs_file, index_col=0)
    regclass_costs = pd.read_csv(regclass_costs_file)
    regclass_learningscalars = pd.read_csv(regclass_learningscalars_file)
    sourcetype_costs = pd.read_csv(sourcetype_costs_file)
    markups = pd.read_csv(markups_file)
    # markups_vmt_scalars = pd.read_csv(markups_vmt_scalars_file)
    warranty_inputs = pd.read_csv(warranty_inputs_file)
    usefullife_inputs = pd.read_csv(usefullife_inputs_file)
    # sourcetype_markups = pd.read_csv(markups_sourcetype_file)
    moves = pd.read_csv(moves_file)
    moves_adjustments = pd.read_csv(moves_adjustments_file)
    options = pd.read_csv(options_file)
    def_doserate_inputs = pd.read_csv(def_doserate_inputs_file)
    def_prices = pd.read_csv(def_prices_file)
    orvr_fuelchanges = pd.read_csv(orvr_fuelchange_file)
    repair_and_maintenance = pd.read_csv(repair_and_maintenance_file, index_col=0)

    markups.drop('Notes', axis=1, inplace=True)
    # markups_vmt_scalars.drop('Notes', axis=1, inplace=True)
    orvr_fuelchanges.drop('Notes', axis=1, inplace=True)
    regclass_costs.drop('Notes', axis=1, inplace=True)
    elapsed_time_read = time.time() - start_time_read

    # get necessary inputs from the bca_inputs_file
    print("Doing the work....")
    start_time_calcs = time.time()
    aeo_case = bca_inputs.at['aeo_fuel_price_case', 'Value']
    discrate_social_low = pd.to_numeric(bca_inputs.at['discrate_social_low', 'Value'])
    discrate_social_high = pd.to_numeric(bca_inputs.at['discrate_social_high', 'Value'])
    discount_to_yearID = pd.to_numeric(bca_inputs.at['discount_to_yearID', 'Value'])
    discount_to = bca_inputs.at['discount_to', 'Value']
    learning_rate = pd.to_numeric(bca_inputs.at['learning_rate', 'Value'])
    dollar_basis_years_gdp = bca_inputs.at['dollar_basis_years_gdp', 'Value']
    # convert dollar_basis_years_gdp to numeric rather than string
    dollar_basis_years_gdp = dollar_basis_years_gdp.split(',')
    for item in range(len(dollar_basis_years_gdp)):
        dollar_basis_years_gdp[item] = pd.to_numeric(dollar_basis_years_gdp[item])
    dollar_basis_years_cpiu = bca_inputs.at['dollar_basis_years_cpiu', 'Value']
    # convert dollar_basis_years_cpiu to numeric rather than string
    dollar_basis_years_cpiu = dollar_basis_years_cpiu.split(',')
    for item in range(len(dollar_basis_years_cpiu)):
        dollar_basis_years_cpiu[item] = pd.to_numeric(dollar_basis_years_cpiu[item])
    warranty_vmt_share = pd.to_numeric(bca_inputs.at['warranty_vmt_share', 'Value'])
    r_and_d_vmt_share = pd.to_numeric(bca_inputs.at['r_and_d_vmt_share', 'Value'])
    indirect_cost_scaling_metric = bca_inputs.at['scale_indirect_costs_by', 'Value']
    calc_pollution_effects = bca_inputs.at['calculate_pollution_effects', 'Value']
    round_moves_ustons_by = pd.to_numeric(bca_inputs.at['round_moves_ustons_by', 'Value'])
    round_costs_by = pd.to_numeric(bca_inputs.at['round_costs_by', 'Value'])

    # how many alternatives are there? But first, be sure that optionID is the header for optionID.
    if 'Alternative' in moves.columns.tolist():
        moves.rename(columns={'Alternative': 'optionID'}, inplace=True)
    if 0 in moves['optionID']:
        number_alts = int(moves['optionID'].max()) + 1
    else:
        number_alts = int(moves['optionID'].max())

    # generate a dictionary of gdp deflators and apply gdp_deflators to direct costs
    deflators_gdp = dict()
    for number in range(len(dollar_basis_years_gdp)):
        deflators_gdp[number] = pd.to_numeric(bca_inputs.at['gdp_deflator_' + str(dollar_basis_years_gdp[number]), 'Value'])
    bca_dollar_basis = dollar_basis_years_gdp[[k for k, v in deflators_gdp.items() if v == 1][0]] # this is a list containing one item reflecting the key in deflators where value=1; the [0] returns that 1 item
    regclass_costs_years = [col for col in regclass_costs.columns if '20' in col]
    regclass_costs_modified = convert_dollars_to_bca_basis(regclass_costs, deflators_gdp, dollar_basis_years_gdp, [step for step in regclass_costs_years], bca_dollar_basis)
    sourcetype_costs = convert_dollars_to_bca_basis(sourcetype_costs, deflators_gdp, dollar_basis_years_gdp, 'TechPackageCost', bca_dollar_basis)
    def_prices = convert_dollars_to_bca_basis(def_prices, deflators_gdp, dollar_basis_years_gdp, 'DEF_USDperGal', bca_dollar_basis)
    repair_and_maintenance = convert_dollars_to_bca_basis(repair_and_maintenance, deflators_gdp, dollar_basis_years_gdp, 'Value', bca_dollar_basis)

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

    factors_cpiu = dict()
    for number in range(len(dollar_basis_years_cpiu)):
        factors_cpiu[number] = pd.to_numeric(bca_inputs.at['cpiu_factor_' + str(dollar_basis_years_cpiu[number]), 'Value'])

    fuel_prices = GetFuelPrices(PATH_PROJECT).get_fuel_prices(aeo_case)

    # Calculate the Indirect Cost scalars based on the warranty_inputs and usefullife_inputs
    warranty_scalars = IndirectCostScalars(warranty_inputs).calc_scalars_absolute('Warranty', indirect_cost_scaling_metric)
    usefullife_scalars = IndirectCostScalars(usefullife_inputs).calc_scalars_relative('RnD', indirect_cost_scaling_metric)
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
    for df in [regclass_costs_modified, regclass_learningscalars, moves, moves_adjustments, sourcetype_costs]:
        df = Fleet(df).define_bca_regclass()
    for df in [moves, sourcetype_costs]:
        df = Fleet(df).define_bca_sourcetype()

    # round MOVES values
    # uston_list = [metric for metric in moves.columns if 'UStons' in metric]
    # moves = round_metrics(moves, uston_list, round_moves_ustons_by)
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
    for step in regclass_costs_years:
        for veh in rc_ft_age0[step]:
            pkg_cost_veh_regclass = DirectCost(veh).pkg_cost_vehicle_regclass1(regclass_costs_modified, step)
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

    # determine how many zgtechs are in the analysis and then calc VPOP of each, including reducing VPOP_MOVES accordingly
    try:
        zgtech_max = int(sourcetype_costs.loc[sourcetype_costs['percent'] > 0, 'zerogramTechID'].max()) # returns NaN if no zgtech
    except ValueError:
        zgtech_max = 0

    fleet_bca = Fleet(moves_adjusted).fleet_with_0gtech(sourcetype_costs, zgtech_max)
    fleet_bca = pd.DataFrame(fleet_bca.loc[fleet_bca['modelYearID'] >= year_min])
    fleet_bca.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'zerogramTechID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    fleet_bca.reset_index(drop=True, inplace=True)
    # add the identifier metric, alt_st_rc_ft_zg, to the dataframes
    for df in [sourcetype_costs, fleet_bca]:
        df = Fleet(df).define_bca_sourcetype_zg()
    sales_bca = Fleet(fleet_bca).sales()

    # calculate the zero gram tech direct mfg costs by passing vehicles, package costs, sales and learning metrics thru the DirectCost class
    st_rc_ft_zg_age0 = pd.Series(sales_bca['alt_st_rc_ft_zg']).unique()
    sourcetype_costs_vehs = pd.Series(sourcetype_costs['alt_st_rc_ft_zg']).unique()
    pkg_directcost_veh_zgtech_dict = dict()
    for veh in st_rc_ft_zg_age0:
        if veh not in list(sourcetype_costs_vehs):
            pkg_cost_veh_zgtech, pkg_seedvol = 0, 0
            techpen = 0 # this is the zgtech techpen on this vehicle, so ICE=0
            sales_to_pass = sales_bca.loc[sales_bca['alt_st_rc_ft_zg'] == veh, :]
            sales_to_pass.reset_index(inplace=True, drop=True)
            pkg_directcost_veh_zgtech_dict[veh] = DirectCost(veh).pkg_cost_zgtech_withlearning(sales_to_pass, pkg_cost_veh_zgtech, techpen,
                                                                                               pkg_seedvol, learning_rate)
        else:
            pkg_cost_veh_zgtech, pkg_seedvol = DirectCost(veh).pkg_cost_vehicle_zgtech(sourcetype_costs)[0], \
                                               DirectCost(veh).pkg_cost_vehicle_zgtech(sourcetype_costs)[1]
            techpen = 1 # this is the zgtech techpen on this vehicle, so non-ICE=1 since VPOP already includes the percentage having the zgtech
            sales_to_pass = sales_bca.loc[sales_bca['alt_st_rc_ft_zg'] == veh, :]
            sales_to_pass.reset_index(inplace=True, drop=True)
            pkg_directcost_veh_zgtech_dict[veh] = DirectCost(veh).pkg_cost_zgtech_withlearning(sales_to_pass, pkg_cost_veh_zgtech, techpen,
                                                                                               pkg_seedvol, learning_rate)
        pkg_directcost_veh_zgtech_dict[veh]['DirectCost_AvgPerVeh_ZG'].fillna(0, inplace=True)
        pkg_directcost_veh_zgtech_dict[veh].insert(1, 'Vehicle_Name_BCA', Vehicle(veh).name_bca())

    # create DataFrames into which the individual DataFrames in the above dictionaries can be appended
    directcost_regclass = pd.DataFrame()
    directcost_sourcetype = pd.DataFrame()
    for veh in rc_ft_age0:
        directcost_regclass = pd.concat([directcost_regclass, pkg_directcost_veh_regclass_dict[veh]], axis=0, ignore_index=True)
    for veh in st_rc_ft_zg_age0:
        directcost_sourcetype = pd.concat([directcost_sourcetype, pkg_directcost_veh_zgtech_dict[veh]], axis=0, ignore_index=True)

    # merge the DataFrames into a new DataFrame, create and calculate some new metrics, drop some metrics
    directcost_sourcetype.fillna(0, inplace=True)
    directcost_regclass.drop(columns=['VPOP'], inplace=True)
    directcost_bca = directcost_sourcetype.merge(directcost_regclass, on=['optionID', 'regClassID', 'fuelTypeID', 'alt_rc_ft', 'yearID', 'modelYearID', 'ageID'], how='left', sort='False')
    directcost_bca['DirectCost_AvgPerVeh'] = directcost_bca[['DirectCost_AvgPerVeh', 'DirectCost_AvgPerVeh_ZG']].sum(axis=1)
    directcost_bca.loc[directcost_bca['VPOP'] == 0, 'DirectCost_AvgPerVeh'] = 0
    # drop some columns that are confusing in the merged DataFrame
    directcost_bca.drop(columns=['DirectCost_TotalCost_ZG'], inplace=True)
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
        emission_costs = pd.DataFrame(fleet_bca, columns=['optionID', 'yearID', 'modelYearID', 'ageID',
                                                          'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID',
                                                          'alt_st_rc_ft_zg', 'alt_st_rc_ft', 'alt_rc_ft',
                                                          'PM25_onroad', 'NOx_onroad'])
        emission_costs = EmissionCost(emission_costs).calc_criteria_emission_costs_df(criteria_emission_costs_reshaped)
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
    operating_costs = pd.DataFrame(fleet_bca, columns=['optionID', 'yearID', 'modelYearID', 'ageID',
                                                       'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID',
                                                       'alt_st_rc_ft_zg', 'alt_st_rc_ft', 'alt_rc_ft',
                                                       'Gallons', 'MPG_AvgPerVeh', 'VMT', 'VMT_AvgPerVeh', 'VMT_AvgPerVeh_CumSum',
                                                       'THC_UStons'])
    # determine sourcetype-based estimated ages when warranty and useful life are reached
    repair_warranty_ages = EstimatedAge(operating_costs).ages_by_identifier(warranty_miles_reshaped, warranty_age_reshaped, typical_vmt_thru_age, 'Warranty')
    repair_usefullife_ages = EstimatedAge(operating_costs).ages_by_identifier(usefullife_miles_reshaped, usefullife_age_reshaped, typical_vmt_thru_age, 'UsefulLife')
    # merge in the estimated warranty and useful life ages for estimating repair costs
    for df in [repair_warranty_ages, repair_usefullife_ages]:
        operating_costs = operating_costs.merge(df, on=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'], how='left')
    operating_costs = RepairAndMaintenanceCost(operating_costs).repair_and_maintenance_costs_curve(metrics_repair_and_maint_dict, pkg_directcost_veh_regclass_dict)
    operating_costs = DEFandFuelCost(operating_costs).orvr_fuel_impacts_mlpergram(orvr_fuelchanges)
    def_doserates = DEFandFuelCost(def_doserate_inputs).def_doserate_scaling_factor()
    operating_costs = DEFandFuelCost(operating_costs).def_cost_df(def_doserates, def_prices)
    operating_costs = DEFandFuelCost(operating_costs).fuel_costs(fuel_prices)
    cols_owner = ['EmissionRepairCost_Owner_TotalCost', 'UreaCost_TotalCost', 'FuelCost_Retail_TotalCost']
    cols_bca = ['EmissionRepairCost_Owner_TotalCost', 'UreaCost_TotalCost', 'FuelCost_Pretax_TotalCost']
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_Owner_TotalCost', operating_costs[cols_owner].sum(axis=1))
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_BCA_TotalCost', operating_costs[cols_bca].sum(axis=1))
    operating_costs.insert(len(operating_costs.columns), 'OperatingCost_Owner_AvgPerMile', operating_costs['OperatingCost_Owner_TotalCost'] / operating_costs['VMT'])
    operatingcost_metrics_to_discount = [col for col in operating_costs.columns if 'Cost' in col]

    # now create some weighted results of operating costs
    vehs_operating_costs = pd.Series(operating_costs['alt_rc_ft']).unique()
    weighted_repair_owner_cpm = dict()
    weighted_def_cpm = dict()
    weighted_fuel_cpm = dict()
    if TEST_RUN == 't':
        year_list = [2027, 2030]
    else:
        year_list = [2027, 2030, 2035]
    max_age_included = 9
    for veh in vehs_operating_costs:
        weighted_repair_owner_cpm[veh] = weighted_result(operating_costs, 'EmissionRepairCost_Owner_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
        weighted_def_cpm[veh] = weighted_result(operating_costs, 'UreaCost_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)
        weighted_fuel_cpm[veh] = weighted_result(operating_costs, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh', veh, 'modelYearID', year_list, max_age_included)

    weighted_repair_owner_cpm_df = pd.DataFrame(weighted_repair_owner_cpm).transpose()
    weighted_def_cpm_df = pd.DataFrame(weighted_def_cpm).transpose()
    weighted_fuel_cpm_df = pd.DataFrame(weighted_fuel_cpm).transpose()

    # pass each DataFrame thru the DiscountValues class and pass the list of metrics to be discounted for each thru the discount method
    print('Working on discounting monetized values....')
    techcost_dict = dict()
    emission_costs_dict = dict()
    operating_costs_dict = dict()
    for dr in [0, discrate_social_low, discrate_social_high]:
        techcost_dict[dr] = DiscountValues(techcost, dr, discount_to_yearID, discount_to).discount(techcost_metrics_to_discount)
        operating_costs_dict[dr] = DiscountValues(operating_costs, dr, discount_to_yearID, discount_to).discount(operatingcost_metrics_to_discount)
        if calc_pollution_effects == 'Y':
            emission_costs_dict[dr] = DiscountValues(emission_costs, dr, discount_to_yearID, discount_to).discount(criteria_and_tailpipe_emission_costs_list)

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
                                'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID',
                                'Vehicle_Name_RC', 'Vehicle_Name_BCA',
                                'DirectCost_TotalCost', 'WarrantyCost_TotalCost', 'RnDCost_TotalCost', 'OtherCost_TotalCost', 'ProfitCost_TotalCost',
                                'IndirectCost_TotalCost', 'TechCost_TotalCost']
    operating_metrics_for_bca = ['optionID', 'yearID', 'modelYearID', 'ageID',
                                 'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID'] \
                                + operatingcost_metrics_to_discount
    merge_metrics = ['optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID']
    for dr in [0, discrate_social_low, discrate_social_high]:
        bca_costs_dict[dr] = pd.DataFrame(fleet_bca, columns=['optionID', 'yearID', 'modelYearID', 'ageID',
                                                              'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID',
                                                              'TechPackageDescription'])
        bca_costs_dict[dr] = bca_costs_dict[dr].merge(techcost_dict[dr][techcost_metrics_for_bca], on=merge_metrics, how='left')
        bca_costs_dict[dr] = bca_costs_dict[dr].merge(operating_costs_dict[dr][operating_metrics_for_bca], on=merge_metrics, how='left')
        if calc_pollution_effects == 'Y':
            pollution_metrics_for_bca = ['optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID'] \
                                        + criteria_and_tailpipe_emission_costs_list
            bca_costs_dict[dr] = bca_costs_dict[dr].merge(emission_costs_dict[dr][pollution_metrics_for_bca], on=merge_metrics, how='left')
        bca_costs_dict[dr].insert(0, 'DiscountRate', dr)

    bca_costs = pd.DataFrame()
    for dr in [0, discrate_social_low, discrate_social_high]:
        bca_costs = pd.concat([bca_costs, bca_costs_dict[dr]], axis=0, ignore_index=True)

    # add some total cost columns
    if calc_pollution_effects == 'Y':
        for dr in [0.03, 0.07]:
            for mort_est in ['low', 'high']:
                bca_costs.insert(len(bca_costs.columns), 'TotalCost_' + mort_est + '_' + str(dr),
                                 bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(dr)]].sum(axis=1))
    else:
        bca_costs.insert(len(bca_costs.columns), 'TotalCost', bca_costs[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost']].sum(axis=1))

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
    bca_costs['Vehicle_Name_RC'].fillna(method='ffill', inplace=True)
    bca_costs['Vehicle_Name_BCA'].fillna(method='ffill', inplace=True)

    # Now add an OptionName column so that output files provide that information
    Fleet(techcost_all).insert_option_name(options, number_alts)
    Fleet(operating_costs_all).insert_option_name(options, number_alts)
    Fleet(bca_costs).insert_option_name(options, number_alts)
    Fleet(moves_adjusted).insert_option_name(options, number_alts)
    if calc_pollution_effects == 'Y':
        Fleet(emission_costs_all).insert_option_name(options, number_alts)

    # now set a standard row header for use in grouping along with metrics to group
    techcost_metrics_to_sum = ['VPOP'] + [col for col in techcost_all.columns if 'TotalCost' in col]
    techcost_metrics_to_avg = [col for col in techcost_all.columns if 'AvgPerVeh' in col]
    operating_costs_metrics_to_sum = [col for col in operating_costs_all.columns if 'Gallons' in col or 'TotalCost' in col]
    operating_costs_metrics_to_avg = [col for col in operating_costs_all.columns if 'AvgPerVeh' in col or 'AvgPerMile' in col]
    bca_costs_metrics_to_sum = [col for col in bca_costs.columns if 'TotalCost' in col or 'low' in col or 'high' in col]
    moves_metrics_to_sum = [col for col in moves_adjusted.columns if 'PM25' in col or 'NOx' in col]
    if calc_pollution_effects == 'Y':
        emission_costs_metrics_to_sum = [col for col in emission_costs_all.columns if 'PM25' in col or 'NOx' in col or 'Criteria' in col]

    # create a dict of lists for passing thru grouping methods
    groups = 3 # increment this consistent with row_headers created
    row_header_group = dict()
    common_metrics = ['optionID', 'OptionName', 'DiscountRate']
    row_header_group[1] = common_metrics + ['yearID']
    row_header_group[2] = common_metrics + ['yearID', 'regClassID', 'fuelTypeID']
    row_header_group[3] = common_metrics + ['yearID', 'sourceTypeID', 'fuelTypeID']

    row_header_group_cumsum = dict()
    row_header_group_cumsum[1] = common_metrics
    row_header_group_cumsum[2] = common_metrics + ['regClassID', 'fuelTypeID']
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

    moves_sum = GroupMetrics(moves_adjusted, ['optionID', 'OptionName', 'yearID']).group_sum(moves_metrics_to_sum)

    # now annualize the cumsum metrics
    for group in range(1, groups + 1):
        bca_costs_sum[group] = GroupMetrics(bca_costs_sum[group], row_header_group[group]).annualize_cumsum(bca_costs_metrics_to_sum, year_min)

    # now group model year data for the operating costs
    row_header_modelyear = common_metrics + ['modelYearID', 'regClassID', 'fuelTypeID']
    # row_header_modelyear_cumsum = row_header_group_cumsum[2].copy()
    operating_costs_modelyear_metrics_to_avg = [col for col in operating_costs_all.columns if 'MPG_AvgPerVeh' in col or 'AvgPerMile' in col]
    operating_costs_modelyear_metrics_to_sum = [col for col in operating_costs_all.columns if 'Gallons' in col or 'VMT' in col or 'TotalCost' in col or ('AvgPerVeh' in col and 'MPG' not in col)]
    operating_costs_modelyear_sum = GroupMetrics(operating_costs_all, row_header_modelyear).group_sum(operating_costs_modelyear_metrics_to_sum)
    operating_costs_modelyear_mean = GroupMetrics(operating_costs_all, row_header_modelyear).group_mean(operating_costs_modelyear_metrics_to_avg)
    operating_costs_modelyear_summary = operating_costs_modelyear_sum.merge(operating_costs_modelyear_mean, on=row_header_modelyear)

    # calc the deltas relative to alt0
    techcost_metrics_for_deltas = techcost_metrics_to_sum + techcost_metrics_to_avg
    operating_cost_metrics_for_deltas = operating_costs_metrics_to_sum + operating_costs_metrics_to_avg
    bca_costs_metrics_for_deltas = bca_costs_metrics_to_sum + [metric + '_CumSum' for metric in bca_costs_metrics_to_sum] \
                                   + [metric + '_Annualized' for metric in bca_costs_metrics_to_sum]
    for group in range(1, groups + 1):
        techcost_summary[group] = pd.concat([techcost_summary[group], CalcDeltas(techcost_summary[group]).
                                            calc_delta(number_alts, techcost_metrics_for_deltas)], axis=0, ignore_index=True)
        operating_costs_summary[group] = pd.concat([operating_costs_summary[group], CalcDeltas(operating_costs_summary[group]).
                                               calc_delta(number_alts, operating_cost_metrics_for_deltas)], axis=0, ignore_index=True)
        bca_costs_sum[group] = pd.concat([bca_costs_sum[group], CalcDeltas(bca_costs_sum[group]).
                                         calc_delta(number_alts, bca_costs_metrics_for_deltas)], axis=0, ignore_index=True)
        if calc_pollution_effects == 'Y':
            emission_costs_sum[group] = pd.concat([emission_costs_sum[group], CalcDeltas(emission_costs_sum[group]).
                                                  calc_delta(number_alts, emission_costs_metrics_to_sum)], axis=0, ignore_index=True)
    moves_sum = pd.concat([moves_sum, CalcDeltas(moves_sum).calc_delta(number_alts, moves_metrics_to_sum)], axis=0, ignore_index=True)
    operating_costs_modelyear_summary = pd.concat([operating_costs_modelyear_summary, CalcDeltas(operating_costs_modelyear_summary).
                                                  calc_delta(number_alts, operating_cost_metrics_for_deltas)], axis=0, ignore_index=True)

    # add some identifier columns to the grouped output files
    if calc_pollution_effects == 'Y':
        df_list = [techcost_summary, emission_costs_sum, operating_costs_summary, bca_costs_sum]
    else:
        df_list = [techcost_summary, operating_costs_summary, bca_costs_sum]
    for df in df_list:
        df[2].insert(6, 'regclass', pd.Series(regClassID[number] for number in df[2]['regClassID']))
        df[2].insert(7, 'fueltype', pd.Series(fuelTypeID[number] for number in df[2]['fuelTypeID']))
        df[3].insert(6, 'sourceype', pd.Series(sourceTypeID[number] for number in df[3]['sourceTypeID']))
        df[3].insert(7, 'fueltype', pd.Series(fuelTypeID[number] for number in df[3]['fuelTypeID']))
    operating_costs_modelyear_summary.insert(6, 'regclass', pd.Series(regClassID[number] for number in operating_costs_modelyear_summary['regClassID']))
    operating_costs_modelyear_summary.insert(7, 'fueltype', pd.Series(fuelTypeID[number] for number in operating_costs_modelyear_summary['fuelTypeID']))

    # calc the deltas relative to alt0 for the main DataFrames
    new_metrics = [metric for metric in operating_costs_all.columns if 'VMT' in metric or 'Warranty' in metric or 'Useful' in metric or 'tons' in metric]
    operating_cost_metrics_for_deltas = operating_cost_metrics_for_deltas + new_metrics
    operating_costs_all = pd.concat([operating_costs_all, CalcDeltas(operating_costs_all).calc_delta(number_alts, operating_cost_metrics_for_deltas)], axis=0, ignore_index=True)
    bca_costs = pd.concat([bca_costs, CalcDeltas(bca_costs).calc_delta(number_alts, [col for col in bca_costs.columns if 'Cost' in col])], axis=0, ignore_index=True)
    if calc_pollution_effects == 'Y':
        emission_cost_metrics_for_deltas = criteria_and_tailpipe_emission_costs_list + ['PM25_onroad', 'NOx_onroad']
        emission_costs_all = pd.concat([emission_costs_all, CalcDeltas(emission_costs_all).calc_delta(number_alts, emission_cost_metrics_for_deltas)], axis=0, ignore_index=True)

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
    # path_to_results = SetupFilesAndFolders('location for output folder').get_folder()
    PATH_OUTPUTS.mkdir(exist_ok=True)
    path_of_run_folder = PATH_OUTPUTS.joinpath(start_time_readable + '_' + RUN_FOLDER_IDENTIFIER)
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
    techcost_years = [2027, 2030, 2036, 2045]
    regclasses = ['LHD', 'LHD45', 'MHD67', 'HHD8', 'Urban Bus']
    fueltypes = ['Diesel', 'Gasoline', 'CNG']
    techcost_per_veh_file = pd.ExcelWriter(path_of_run_results_folder.joinpath('techcosts_AvgPerVeh.xlsx'))
    DocTables(techcost_summary[2]).techcost_per_veh_table(discount_rates, techcost_years, regclasses, fueltypes, techcost_per_veh_cols, techcost_per_veh_file)
    techcost_per_veh_file.save()

    bca_cols = ['OptionName', 'DiscountRate', 'TechCost_TotalCost', 'OperatingCost_BCA_TotalCost']
    bca_years = [2036, 2045]
    bca_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annual.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_costs_sum[1]).bca_yearID_tables('', 0, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.03', bca_years,
                                                      'billions', bca_cols, bca_annual)
    else:
        DocTables(bca_costs_sum[1]).bca_yearID_tables('', 0, 'TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_annual)
    bca_annual.save()

    bca_npv = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_npv.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.03, 'CriteriaCost_low_0.03', 'CriteriaCost_high_0.03', bca_years,
                                                      'billions', bca_cols, bca_npv)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.07, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.07', bca_years,
                                                      'billions', bca_cols, bca_npv)
    else:
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.03, 'TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_npv)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_CumSum', 0.07, 'TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_npv)
    bca_npv.save()

    bca_annualized = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annualized.xlsx'))
    if calc_pollution_effects == 'Y':
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.03, 'CriteriaCost_low_0.03', 'CriteriaCost_high_0.03', bca_years,
                                                      'billions', bca_cols, bca_annualized)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.07, 'CriteriaCost_low_0.07', 'CriteriaCost_high_0.07', bca_years,
                                                      'billions', bca_cols, bca_annualized)
    else:
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.03, 'TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_annualized)
        DocTables(bca_costs_sum[1]).bca_yearID_tables('_Annualized', 0.07, 'TotalCost', '', bca_years,
                                                      'billions', bca_cols, bca_annualized)
    bca_annualized.save()

    # note that the inventory tables created below include MY2027+ only since emission_costs_sum is based on fleet_bca
    if calc_pollution_effects == 'Y':
        inventory_cols = ['OptionName', 'DiscountRate', 'yearID', 'PM25_tailpipe', 'NOx_tailpipe']
        inventory_years = [2027, 2030, 2036, 2045]
        inventory_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('inventory_annual_BCA_ModelYears.xlsx'))
        DocTables(emission_costs_sum[1]).inventory_tables1(inventory_years, inventory_cols, inventory_annual)
        inventory_annual.save()

        inventory_cols_moves = ['OptionName', 'yearID', 'PM25_tailpipe', 'NOx_tailpipe']
        inventory_annual_moves = pd.ExcelWriter(path_of_run_results_folder.joinpath('inventory_annual_All_ModelYears.xlsx'))
        DocTables(moves_sum).inventory_tables2(inventory_years, inventory_cols_moves, inventory_annual_moves)
        inventory_annual_moves.save()

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    inputs_filename_list = inputs_filenames(input_files_pathlist)
    if CREATE_ALL_FILES == 'y' or CREATE_ALL_FILES == 'Y':
        for file in inputs_filename_list:
            path_source = PATH_INPUTS.joinpath(file)
            path_destination = path_of_run_inputs_folder.joinpath(file)
            shutil.copy(path_source, path_destination)
        fuel_prices.to_csv(path_of_modified_inputs_folder.joinpath('fuel_prices_' + aeo_case + '.csv'), index=False)
        regclass_costs.to_csv(path_of_modified_inputs_folder.joinpath('regclass_costs.csv'), index=False)
        sourcetype_costs.to_csv(path_of_modified_inputs_folder.joinpath('sourcetype_costs.csv'), index=False)
        markups_vmt_scalars_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('markups_vmt_scalars_reshaped.csv'), index=False)
        def_doserates.to_csv(path_of_modified_inputs_folder.joinpath('def_doserates.csv'), index=False)
        def_prices.to_csv(path_of_modified_inputs_folder.joinpath('def_prices.csv'), index=False)
        if calc_pollution_effects == 'Y':
            criteria_emission_costs_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('criteria_emission_costs_reshaped.csv'), index=False)

        # write some output files
        techcost_all.to_csv(path_of_run_results_folder.joinpath('techcosts.csv'), index=False)
        # techcost_summary[1].to_csv(path_of_run_results_folder.joinpath('techcosts_by_yearID.csv'), index=False)
        # techcost_summary[2].to_csv(path_of_run_results_folder.joinpath('techcosts_by_regClass_fuelType.csv'), index=False)
        # techcost_summary[3].to_csv(path_of_run_results_folder.joinpath('techcosts_by_sourcetype_fuelType.csv'), index=False)

        if calc_pollution_effects == 'Y':
            emission_costs_all.to_csv(path_of_run_results_folder.joinpath('criteria_emission_costs.csv'), index=False)
            # emission_costs_sum[1].to_csv(path_of_run_results_folder.joinpath('criteria_emission_costs_by_yearID.csv'), index=False)
            # emission_costs_sum[2].to_csv(path_of_run_results_folder.joinpath('criteria_emission_costs_by_regClass_fuelType.csv'), index=False)
            # emission_costs_sum[3].to_csv(path_of_run_results_folder.joinpath('criteria_emission_costs_by_sourcetype_fuelType.csv'), index=False)

        operating_costs_all.to_csv(path_of_run_results_folder.joinpath('operating_costs.csv'), index=False)
        weighted_repair_owner_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_emission_repair_owner_cpm.csv'))
        weighted_def_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_urea_cpm.csv'))
        weighted_fuel_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_fuel_cpm.csv'))
        # operating_costs_summary[1].to_csv(path_of_run_results_folder.joinpath('operating_costs_by_yearID.csv'), index=False)
        # operating_costs_summary[2].to_csv(path_of_run_results_folder.joinpath('operating_costs_by_regClass_fuelType.csv'), index=False)
        # operating_costs_summary[3].to_csv(path_of_run_results_folder.joinpath('operating_costs_by_sourcetype_fuelType.csv'), index=False)
        # operating_costs_modelyear_summary.to_csv(path_of_run_results_folder.joinpath('operating_costs_by_modelYearID_regClass_fuelType.csv'), index=False)

        bca_costs.to_csv(path_of_run_results_folder.joinpath('bca_costs.csv'), index=False)
        # bca_costs_sum[1].to_csv(path_of_run_results_folder.joinpath('bca_costs_by_yearID.csv'), index=False)
        # bca_costs_sum[2].to_csv(path_of_run_results_folder.joinpath('bca_costs_by_regClass_fuelType.csv'), index=False)
        # bca_costs_sum[3].to_csv(path_of_run_results_folder.joinpath('bca_costs_by_sourcetype_fuelType.csv'), index=False)

    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder', 'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [project_code.__version__, path_of_run_folder, start_time_readable, elapsed_time_read, elapsed_time_calcs, elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)


if __name__ == '__main__':
    main()
