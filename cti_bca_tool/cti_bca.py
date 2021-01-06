"""
cti_bca.py

This is the primary module of the benefit cost analysis tool. This module reads input files, calls other modules and generates output files.

"""
import pandas as pd
import numpy as np
import shutil
from datetime import datetime
from itertools import product
import time
import cti_bca_tool
from cti_bca_tool.get_context_data import GetFuelPrices, GetDeflators
from cti_bca_tool.fleet import Fleet
from cti_bca_tool.vehicle import Vehicle, regClassID, fuelTypeID
from cti_bca_tool.direct_cost import DirectCost
from cti_bca_tool.indirect_cost import IndirectCost, IndirectCostScalers
from cti_bca_tool.operating_cost import DEFCost, ORVRadjust, FuelCost, RepairAndMaintenanceCost
from cti_bca_tool.discounting import DiscountValues
from cti_bca_tool.group_metrics import GroupMetrics
from cti_bca_tool.calc_deltas import CalcDeltas
from cti_bca_tool.emission_cost import EmissionCost
from cti_bca_tool.weighted_results import WeightedResult
from cti_bca_tool.doc_tables import DocTables
from cti_bca_tool.estimated_age import EstimatedAge
from cti_bca_tool.figures import CreateFigures
from cti_bca_tool.data_table import DataTable
import cti_bca_tool.general_functions as gen_fxns


def main(settings):
    """

    :param settings: The SetInputs class within __main__.py establishes the input files to use and other input settings set in the BCA_Inputs file and needed within the tool.
    :return: The results of the cti_bca_tool.
    """
    print("\nDoing the work....")
    start_time_calcs = time.time()

    # how many alternatives are there? But first, be sure that optionID is the header for optionID.
    if 'Alternative' in settings.moves.columns.tolist():
        settings.moves.rename(columns={'Alternative': 'optionID'}, inplace=True)
    number_alts = len(settings.moves['optionID'].unique())

    # get the fuel price inputs and usd basis for the analysis
    fuel_prices_obj = GetFuelPrices(settings.fuel_prices_file, settings.aeo_case, 'full name', 'Motor Gasoline', 'Diesel')
    print(fuel_prices_obj)
    fuel_prices = fuel_prices_obj.get_prices()
    dollar_basis_analysis = fuel_prices_obj.aeo_dollars()

    # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
    deflators_obj = GetDeflators(settings.deflators_file, 'Unnamed: 1', 'Gross domestic product')
    print(deflators_obj)
    gdp_deflators = deflators_obj.calc_adjustment_factors(dollar_basis_analysis)
    cost_steps = [col for col in settings.regclass_costs.columns if '20' in col]
    gen_fxns.convert_dollars_to_analysis_basis(settings.regclass_costs, gdp_deflators, dollar_basis_analysis, [step for step in cost_steps])
    gen_fxns.convert_dollars_to_analysis_basis(settings.def_prices, gdp_deflators, dollar_basis_analysis, 'DEF_USDperGal')
    gen_fxns.convert_dollars_to_analysis_basis(settings.repair_and_maintenance, gdp_deflators, dollar_basis_analysis, 'Value')

    # now get specific inputs from repair_and_maintenance
    inwarranty_repair_and_maintenance_owner_cpm = settings.repair_and_maintenance.at['in-warranty_R&M_Owner_CPM', 'Value']
    atusefullife_repair_and_maintenance_owner_cpm = settings.repair_and_maintenance.at['at-usefullife_R&M_Owner_CPM', 'Value']
    mile_increase_beyond_usefullife = settings.repair_and_maintenance.at['mile_increase_beyond_usefullife', 'Value']
    max_repair_and_maintenance_CPM = settings.repair_and_maintenance.at['max_R&M_Owner_CPM', 'Value']
    typical_vmt_thru_age = settings.repair_and_maintenance.at['typical_vmt_thru_ageID', 'Value']
    emission_repair_share = settings.repair_and_maintenance.at['emission_repair_share', 'Value']
    metrics_repair_and_maint_dict = {'inwarranty_repair_and_maintenance_owner_cpm': inwarranty_repair_and_maintenance_owner_cpm,
                                     'atusefullife_repair_and_maintenance_owner_cpm': atusefullife_repair_and_maintenance_owner_cpm,
                                     'mile_increase_beyond_usefullife': mile_increase_beyond_usefullife,
                                     'max_repair_and_maintenance_cpm': max_repair_and_maintenance_CPM,
                                     'typical_vmt_thru_ageID': typical_vmt_thru_age,
                                     'emission_repair_share': emission_repair_share}

    # Calculate the Indirect Cost scalers based on the warranty_inputs and usefullife_inputs
    warranty_scalers_obj = IndirectCostScalers(settings.warranty_inputs, 'Warranty', settings.indirect_cost_scaling_metric)
    warranty_scalers = warranty_scalers_obj.calc_scalers_absolute()
    usefullife_scalers_obj = IndirectCostScalers(settings.usefullife_inputs, 'RnD', settings.indirect_cost_scaling_metric)
    usefullife_scalers = usefullife_scalers_obj.calc_scalers_relative()
    markup_scalers = pd.concat([warranty_scalers, usefullife_scalers], ignore_index=True, axis=0)
    markup_scalers.reset_index(drop=True, inplace=True)

    # Now, reshape some of the inputs for easier use
    warranty_miles_reshaped = gen_fxns.reshape_df(settings.warranty_inputs.loc[settings.warranty_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                  [col for col in settings.warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Miles')
    warranty_age_reshaped = gen_fxns.reshape_df(settings.warranty_inputs.loc[settings.warranty_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                [col for col in settings.warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Age')
    usefullife_miles_reshaped = gen_fxns.reshape_df(settings.usefullife_inputs.loc[settings.usefullife_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                    [col for col in settings.usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Miles')
    usefullife_age_reshaped = gen_fxns.reshape_df(settings.usefullife_inputs.loc[settings.usefullife_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                  [col for col in settings.usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Age')
    markup_scalers_reshaped = gen_fxns.reshape_df(markup_scalers, ['optionID', 'regClassID', 'fuelTypeID', 'Markup_Factor'],
                                                  [col for col in markup_scalers.columns if '20' in col], 'yearID', 'Value')
    for df in [warranty_miles_reshaped, warranty_age_reshaped, usefullife_miles_reshaped, usefullife_age_reshaped]:
        df['modelYearID'] = pd.to_numeric(df['modelYearID'])
        df.insert(0, 'alt_rc_ft', pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID'])))
    markup_scalers_reshaped['yearID'] = pd.to_numeric(markup_scalers_reshaped['yearID'])

    # read and reshape criteria costs if pollution effects are being calculated
    if settings.calc_pollution_effects == 'Y':
        criteria_emission_costs = gen_fxns.read_input_files(settings.path_inputs, settings.input_files_dict['criteria_emission_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
        tailpipe_pollutant_costs_list = [col for col in criteria_emission_costs.columns if 'onroad' in col]
        criteria_emission_costs_reshaped = gen_fxns.reshape_df(criteria_emission_costs, ['yearID', 'MortalityEstimate', 'DR', 'fuelTypeID', 'DollarBasis'],
                                                               tailpipe_pollutant_costs_list, 'Pollutant_source', 'USDpUSton')
        criteria_emission_costs_reshaped.insert(1, 'Key', '')
        criteria_emission_costs_reshaped['Key'] = criteria_emission_costs_reshaped['Pollutant_source'] + '_' \
                                                  + criteria_emission_costs_reshaped['MortalityEstimate'] + '_' \
                                                  + criteria_emission_costs_reshaped['DR'].map(str)
        discrate_criteria_low = criteria_emission_costs_reshaped['DR'].min()
        discrate_criteria_high = criteria_emission_costs_reshaped['DR'].max()
        assert discrate_criteria_low == settings.discrate_social_low, "Inconsistent discount rates - must be equal. If you want to use your own discount rates, you must toggle 'calculate_pollution_effects' to 'N'."
        assert discrate_criteria_high == settings.discrate_social_high, "Inconsistent discount rates - must be equal. If you want to use your own discount rates, you must toggle 'calculate_pollution_effects' to 'N'."

    # add the identifier metrics, alt_rc_ft and alt_st_rc_ft, to specific DataFrames
    for df in [settings.regclass_costs, settings.regclass_learningscalers, settings.moves, settings.moves_adjustments]:
        df = Fleet(df).define_bca_regclass()
    moves = Fleet(settings.moves).define_bca_sourcetype()

    # adjust MOVES VPOP/VMT/Gallons to reflect what's included in CTI (excluding what's not in CTI)
    moves_adjusted = Fleet(moves).adjust_moves(settings.moves_adjustments, 'VPOP', 'VMT', 'Gallons')  # adjust (41, 2) to be engine cert only
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
    reductions = CalcDeltas(sourcetype_criteria).calc_delta_and_keep_alt_id('THC_UStons', 'PM25_onroad', 'NOx_onroad')
    sourcetype_criteria = sourcetype_criteria.merge(reductions, on=gen_fxns.get_common_metrics(sourcetype_criteria, reductions), how='left')
    sourcetype_per_veh.insert(len(sourcetype_per_veh.columns), 'VMT_AvgPerVeh', sourcetype_vmt['VMT'] / sourcetype_vpop['VPOP'])
    sourcetype_per_veh = sourcetype_per_veh.join(GroupMetrics(sourcetype_per_veh, ['alt_st_rc_ft', 'modelYearID']).group_cumsum(['VMT_AvgPerVeh']))
    sourcetype_per_veh.insert(len(sourcetype_per_veh.columns), 'MPG_AvgPerVeh', sourcetype_vmt['VMT'] / sourcetype_gallons['Gallons'])

    # calculate the direct mfg costs by passing vehicles, package costs/pens, sales and learning metrics thru the DirectCost class
    print('\nWorking on tech package costs....')
    regclass_costs_dict = dict()
    regclass_sales_dict = dict()  # this will provide sales by regclass-fueltype (rather than sourcetype-regclass-fueltype) which is needed for learning effects
    alt_rc_ft_vehicles = dict()
    for step in cost_steps:
        regclass_sales_dict[step] = pd.DataFrame(regclass_sales.loc[regclass_sales['modelYearID'] >= pd.to_numeric(step), :])
        alt_rc_ft_vehicles[step] = pd.Series(regclass_sales_dict[step]['alt_rc_ft'].unique())
    # Apply learning to direct costs
    for step, veh in product(cost_steps, alt_rc_ft_vehicles[step]):
        direct_costs_obj = DirectCost(veh, step, settings.regclass_costs, settings.regclass_learningscalers, regclass_sales_dict[step])
        print(direct_costs_obj)
        regclass_costs_dict[veh, step] = direct_costs_obj.pkg_cost_regclass_withlearning(settings.learning_rate)

    # Now merge the steps into a single DataFrame so that the costs can be summed into a single cost series. An outer merge is used in case there are different vehicles (unlikely).
    alt_rc_ft_vehicles = pd.Series(regclass_sales['alt_rc_ft'].unique())
    for veh in alt_rc_ft_vehicles:
        regclass_costs_dict[veh] = regclass_costs_dict[veh, cost_steps[0]].copy()
        regclass_costs_dict[veh][f'DirectCost_AvgPerVeh_{cost_steps[0]}'].fillna(0, inplace=True)
        for step_number, step in enumerate(cost_steps[1:]): #range(1, len(cost_steps)):  # this brings in costs from subsequent steps
            regclass_costs_dict[veh] = regclass_costs_dict[veh]\
                .merge(regclass_costs_dict[veh, step],
                       on=gen_fxns.get_common_metrics(regclass_costs_dict[veh], regclass_costs_dict[veh, step], ignore=['static_id']),
                       how='outer')
            regclass_costs_dict[veh][f'DirectCost_AvgPerVeh_{step}'].fillna(0, inplace=True)

    # Since subsequent steps are incremental to prior steps, now sum the steps.
    for veh in alt_rc_ft_vehicles:
        regclass_costs_dict[veh].insert(len(regclass_costs_dict[veh].columns), 'DirectCost_AvgPerVeh', 0)
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
        merge_object = IndirectCost(regclass_costs_dict[veh], settings.markups)
        regclass_costs_dict[veh] = merge_object.get_markups(settings.markups.loc[settings.markups['fuelTypeID'] == veh[2], :])
        regclass_costs_dict[veh] = merge_object.merge_markup_scalers(markup_scalers_reshaped.loc[(markup_scalers_reshaped['optionID'] == veh[0])
                                                                                                 & (markup_scalers_reshaped['regClassID'] == veh[1])
                                                                                                 & (markup_scalers_reshaped['fuelTypeID'] == veh[2]), :],
                                                                     'yearID')
        regclass_costs_dict[veh].ffill(inplace=True)
        regclass_costs_dict[veh].reset_index(drop=True, inplace=True)

        indirect_cost_obj = IndirectCost(regclass_costs_dict[veh], settings.markups)
        print(f'IndirectCost: Vehicle {veh}')
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_scaled(regclass_costs_dict[veh], 'Warranty', settings.warranty_vmt_share)
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_scaled(regclass_costs_dict[veh], 'RnD', settings.r_and_d_vmt_share)
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_unscaled(regclass_costs_dict[veh])
        regclass_costs_dict[veh] = indirect_cost_obj.indirect_cost_sum()
        regclass_costs_dict[veh].insert(len(regclass_costs_dict[veh].columns),
                                        'TechCost_AvgPerVeh',
                                        regclass_costs_dict[veh]['DirectCost_AvgPerVeh'] + regclass_costs_dict[veh]['IndirectCost_AvgPerVeh'])
        # drop VPOP from regclass_costs since it's VPOP by regclass
        regclass_costs_dict[veh].drop(columns=['VPOP'], inplace=True)
        regclass_costs_df = pd.concat([regclass_costs_df, regclass_costs_dict[veh]], axis=0, ignore_index=True)

    # To get costs on a sourcetype basis, create a sourcetype_tech_costs DataFrame into which to merge the regclass_costs
    sourcetype_tech_costs = sourcetype_vpop.merge(regclass_costs_df, on=gen_fxns.get_common_metrics(sourcetype_vpop, regclass_costs_df), how='left', sort='False')
    sourcetype_tech_costs.loc[sourcetype_tech_costs['VPOP'] == 0, 'DirectCost_AvgPerVeh'] = 0
    for metric in [item for item in sourcetype_tech_costs.columns if 'Cost_AvgPerVeh' in item]:
        sourcetype_tech_costs[f'{metric}'].fillna(0, inplace=True)
    for metric in indirect_cost_obj.markup_factors() + ['Direct', 'Indirect', 'Tech']:
        sourcetype_tech_costs.insert(len(sourcetype_tech_costs.columns),
                                     f'{metric}Cost_TotalCost',
                                     sourcetype_tech_costs[[f'{metric}Cost_AvgPerVeh', 'VPOP']].product(axis=1))
    sourcetype_tech_costs.reset_index(drop=True, inplace=True)
    techcost_metrics_to_discount = [col for col in sourcetype_tech_costs.columns if 'Cost' in col]

    # work on pollution costs, if being calculated
    if settings.calc_pollution_effects == 'Y':
        print('\nWorking on pollution costs....')
        # first calc emission costs
        emission_cost_obj = EmissionCost(sourcetype_criteria, criteria_emission_costs_reshaped,
                                         [discrate_criteria_low, discrate_criteria_high], ['PM25', 'NOx'], ['onroad'], ['low', 'high'])
        sourcetype_emission_costs = emission_cost_obj.calc_emission_costs_df()
        # now calc criteria costs (sum of emission costs)
        emission_cost_obj = EmissionCost(sourcetype_emission_costs, criteria_emission_costs_reshaped,
                                         [discrate_criteria_low, discrate_criteria_high], ['PM25', 'NOx'], ['onroad'], ['low', 'high'])
        sourcetype_emission_costs = emission_cost_obj.calc_criteria_costs_df()
        # make some useful lists of metrics
        criteria_costs_list = [col for col in sourcetype_emission_costs.columns if 'CriteriaCost' in col]
        criteria_costs_list_low = [col for col in sourcetype_emission_costs.columns if 'CriteriaCost' in col and str(discrate_criteria_low) in col]
        criteria_costs_list_high = [col for col in sourcetype_emission_costs.columns if 'CriteriaCost' in col and str(discrate_criteria_high) in col]
        tailpipe_pollutant_costs_list = [col for col in sourcetype_emission_costs.columns if 'Cost_onroad' in col]
        tailpipe_pollutant_costs_list_low = [col for col in sourcetype_emission_costs.columns if 'Cost_onroad' in col and str(discrate_criteria_low) in col]
        tailpipe_pollutant_costs_list_high = [col for col in sourcetype_emission_costs.columns if 'Cost_onroad' in col and str(discrate_criteria_high) in col]
        criteria_and_tailpipe_pollutant_costs_list = criteria_costs_list + tailpipe_pollutant_costs_list

    # work now on operating costs which include repair, DEF, fuel costs
    print('\nWorking on operating costs....')
    # calc the DEF costs
    def_costs_dict = dict()
    sourcetype_def_costs = pd.DataFrame()
    alt_st_rc_ft_vehicles = pd.Series(sourcetype_tech_costs['alt_st_rc_ft'].unique())
    for veh in alt_st_rc_ft_vehicles:
        if veh[3] == 2:
            def_costs_dict[veh] = pd.DataFrame(sourcetype_criteria.loc[sourcetype_criteria['alt_st_rc_ft'] == veh,
                                                                       ['alt_st_rc_ft', 'yearID', 'modelYearID', 'ageID',
                                                                        'NOx_onroad_Reductions']]).reset_index(drop=True)
            def_costs_obj = DEFCost(veh, cost_steps, def_costs_dict[veh], settings.def_doserate_inputs, settings.def_gallons_perTonNOxReduction, settings.def_prices)
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
    orvr_adjust_obj = ORVRadjust(alt_st_rc_ft_vehicles, settings.orvr_fuelchanges, sourcetype_gallons,
                                 sourcetype_criteria[['THC_UStons_Reductions']], sourcetype_vmt)
    sourcetype_gallons = orvr_adjust_obj.adjust_gallons(settings)
    sourcetype_per_veh = orvr_adjust_obj.adjust_mpg(sourcetype_per_veh)  # must adjust MPG prior to calc of fuel costs
    sourcetype_fuel_costs = FuelCost(alt_st_rc_ft_vehicles, sourcetype_gallons, sourcetype_vmt, sourcetype_per_veh, fuel_prices).calc_fuel_costs()

    # work on emission repair costs, but first need the estimated ages at which warranty and useful life are expected to be reached
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

    # merge everything -- tech, operating, pollution -- into a single sourcetype_all_costs dataframe
    sourcetype_all_costs = sourcetype_vpop.copy()
    df_merge_list = [sourcetype_vmt, sourcetype_per_veh, sourcetype_tech_costs,
                     sourcetype_def_costs, sourcetype_gallons, sourcetype_fuel_costs, estimated_ages_df, sourcetype_repair_costs]
    if settings.calc_pollution_effects == 'Y':
        df_merge_list = df_merge_list + [sourcetype_emission_costs]
    for df in df_merge_list:
        sourcetype_all_costs = sourcetype_all_costs.merge(df, on=gen_fxns.get_common_metrics(sourcetype_all_costs, df), how='left').reset_index(drop=True)
    sourcetype_all_costs.sort_values(by=['optionID', 'regClassID', 'fuelTypeID', 'sourceTypeID', 'yearID', 'ageID'], ascending=True, inplace=True, axis=0)
    sourcetype_all_costs.drop(columns='static_id', inplace=True)
    sourcetype_all_costs.reset_index(drop=True, inplace=True)

    # add some new metrics to track total operating costs
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

    operatingcost_metrics_to_discount = [col for col in sourcetype_all_costs.columns if 'RepairCost' in col or 'DEFCost' in col
                                         or 'FuelCost' in col or 'OperatingCost' in col]

    # now create some weighted results of operating costs
    weighted_results_obj = WeightedResult(sourcetype_all_costs, 'VMT_AvgPerVeh', alt_st_rc_ft_vehicles, 'modelYearID',
                                          settings.weighted_operating_cost_years, settings.max_age_included, settings.options_dict)
    weighted_def_cpm_df = weighted_results_obj.weighted_results('DEFCost_AvgPerMile')
    weighted_repair_owner_cpm_df = weighted_results_obj.weighted_results('EmissionRepairCost_Owner_AvgPerMile')
    weighted_fuel_cpm_df = weighted_results_obj.weighted_results('FuelCost_Retail_AvgPerMile')

    # and now put the MOVES name identifier into the DataFrame
    sourcetype_all_costs.insert(sourcetype_all_costs.columns.get_loc('fuelTypeID') + 1, 'Vehicle_Name_MOVES', '')
    for veh in alt_st_rc_ft_vehicles:
        sourcetype_all_costs.loc[sourcetype_all_costs['alt_st_rc_ft'] == veh, 'Vehicle_Name_MOVES'] = Vehicle(veh).name_moves()

    # pass things thru the DiscountValues class and pass the list of metrics to be discounted thru the discount method
    print('\nWorking on discounting monetized values....')
    bca_dict = dict()
    if settings.calc_pollution_effects == 'Y':
        bca_metrics_to_discount = techcost_metrics_to_discount \
                                  + criteria_and_tailpipe_pollutant_costs_list \
                                  + operatingcost_metrics_to_discount
    else:
        bca_metrics_to_discount = techcost_metrics_to_discount + operatingcost_metrics_to_discount
    for dr in [0, settings.discrate_social_low, settings.discrate_social_high]:
        discounting_obj = DiscountValues(sourcetype_all_costs, settings.discount_to_yearID, settings.costs_start, *bca_metrics_to_discount)
        bca_dict[dr] = discounting_obj.discount(dr)

    # now set to NaN discounted pollutant values using discount rates that are not consistent with the input values
    if settings.calc_pollution_effects == 'Y':
        for col in criteria_costs_list_low:
            bca_dict[discrate_criteria_high][col] = np.nan
        for col in criteria_costs_list_high:
            bca_dict[discrate_criteria_low][col] = np.nan
        for col in tailpipe_pollutant_costs_list_low:
            bca_dict[discrate_criteria_high][col] = np.nan
        for col in tailpipe_pollutant_costs_list_high:
            bca_dict[discrate_criteria_low][col] = np.nan

    # pull together each discount rate into a single DataFrame
    print('\nWorking on benefit-cost analysis results and summarizing things....')
    bca = pd.DataFrame()
    for dr in [0, settings.discrate_social_low, settings.discrate_social_high]:
        bca = pd.concat([bca, bca_dict[dr]], axis=0, ignore_index=True)

    # add some total cost columns
    bca.insert(len(bca.columns), 'TechAndOperatingCost_BCA_TotalCost', bca[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost']].sum(axis=1))
    if settings.calc_pollution_effects == 'Y':
        for dr, mort_est in product([discrate_criteria_low, discrate_criteria_high], ['low', 'high']):
            bca.insert(len(bca.columns), 'TotalCost_' + mort_est + '_' + str(dr),
                         bca[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(dr)]].sum(axis=1))
    else:
        pass

    # adjust the low and high DR total costs as needed
    if settings.calc_pollution_effects == 'Y':
        for mort_est in ['low', 'high']:
            bca.loc[bca['DiscountRate'] == settings.discrate_social_low, 'TotalCost_' + mort_est + '_' + str(settings.discrate_social_low)] \
                = bca[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(settings.discrate_social_low)]].sum(axis=1)
            bca.loc[bca['DiscountRate'] == settings.discrate_social_low, 'TotalCost_' + mort_est + '_' + str(settings.discrate_social_high)] \
                = np.nan
            bca.loc[bca['DiscountRate'] == settings.discrate_social_high, 'TotalCost_' + mort_est + '_' + str(settings.discrate_social_high)] \
                = bca[['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'CriteriaCost_' + mort_est + '_' + str(settings.discrate_social_high)]].sum(axis=1)
            bca.loc[bca['DiscountRate'] == settings.discrate_social_high, 'TotalCost_' + mort_est + '_' + str(settings.discrate_social_low)] \
                = np.nan

    # Now add an OptionName column so that output files provide that information
    Fleet(bca).insert_option_name(settings.options_dict, number_alts)

    # now set a standard row header for use in grouping along with metrics to group
    bca_metrics_to_sum = [col for col in bca.columns if 'TotalCost' in col or 'VPOP' in col or 'Gallons' in col
                          or 'PM25' in col or 'NOx' in col or 'Criteria' in col]
    bca_metrics_to_avg = [col for col in bca.columns if 'AvgPerVeh' in col or 'AvgPerMile' in col]
    bca_metrics_to_cumsum = [col for col in bca.columns if 'TotalCost' in col or 'Criteria' in col]

    # create a dict of lists for passing thru grouping methods
    row_header_group = dict()
    common_metrics = ['optionID', 'OptionName', 'DiscountRate']
    row_header_group['yearID'] = common_metrics + ['yearID']
    row_header_group['yearID_rc_ft'] = common_metrics + ['yearID', 'regClassID', 'fuelTypeID']
    # groups = 2 # increment this consistent with row_headers created

    row_header_group_cumsum = dict()
    row_header_group_cumsum['yearID'] = common_metrics
    row_header_group_cumsum['yearID_rc_ft'] = common_metrics + ['regClassID', 'fuelTypeID']

    # create some dicts to store the groupby.sum, groupby.cumsum and groupby.mean results
    bca_sum = dict()
    bca_mean = dict()
    bca_summary = dict()
    for group in ['yearID', 'yearID_rc_ft']:
        # first a groupby.sum, then a groupby.cumsum on the groupby.sum which is joined into the groupby.sum, then a groupby.mean, then a merge into one
        bca_sum[group] = GroupMetrics(bca, row_header_group[group]).group_sum(bca_metrics_to_sum)
        bca_mean[group] = GroupMetrics(bca, row_header_group[group]).group_mean(bca_metrics_to_avg)
        bca_summary[group] = bca_sum[group].merge(bca_mean[group], on=row_header_group[group])
        bca_summary[group] = bca_summary[group].join(GroupMetrics(bca_summary[group], row_header_group_cumsum[group]).group_cumsum(bca_metrics_to_cumsum))

    # now annualize the cumsum metrics
    for group in ['yearID', 'yearID_rc_ft']:
        bca_summary[group] = DiscountValues(bca_summary[group], settings.discount_to_yearID, settings.costs_start, *bca_metrics_to_cumsum).annualize()

    # calc the deltas relative to alt0
    bca_summary['yearID'].sort_values(by=['DiscountRate', 'optionID', 'yearID'], ascending=True, inplace=True, axis=0)
    bca_summary['yearID_rc_ft'].sort_values(by=['DiscountRate', 'optionID', 'yearID', 'regClassID', 'fuelTypeID'], ascending=True, inplace=True, axis=0)
    bca_metrics_for_deltas = bca_metrics_to_sum + bca_metrics_to_avg \
                             + [metric + '_CumSum' for metric in bca_metrics_to_cumsum] \
                             + [metric + '_Annualized' for metric in bca_metrics_to_cumsum]
    for group in ['yearID', 'yearID_rc_ft']:
        bca_summary[group] = pd.concat([bca_summary[group], 
                                        CalcDeltas(bca_summary[group]).calc_delta_and_new_alt_id(*bca_metrics_for_deltas)],
                                       axis=0, ignore_index=True)

    # add some identifier columns to the grouped output files
    bca_summary['yearID_rc_ft'].insert(bca_summary['yearID_rc_ft'].columns.get_loc('regClassID') + 1,
                                       'regclass',
                                       pd.Series(regClassID[number] for number in bca_summary['yearID_rc_ft']['regClassID']))
    bca_summary['yearID_rc_ft'].insert(bca_summary['yearID_rc_ft'].columns.get_loc('fuelTypeID') + 1,
                                       'fueltype',
                                       pd.Series(fuelTypeID[number] for number in bca_summary['yearID_rc_ft']['fuelTypeID']))

    # calc the deltas relative to alt0 for the bca DataFrame
    bca.sort_values(by=['DiscountRate', 'optionID', 'yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID'], ascending=True, inplace=True, axis=0)
    bca_cols_for_deltas = [col for col in bca.columns if 'Calculated' in col or 'Estimated' in col or 'Cost' in col or 'cost' in col
                             or 'Warranty' in col or 'UsefulLife' in col or 'Gallons' in col or 'max' in col or 'slope' in col
                             or ('AvgPerVeh' in col and 'VMT' not in col) or 'THC' in col or 'PM' in col or 'NOx' in col]
    bca = pd.concat([bca, CalcDeltas(bca).calc_delta_and_new_alt_id(*bca_cols_for_deltas)], axis=0, ignore_index=True)

    # generate some document tables
    preamble_program_metrics = ['DirectCost_TotalCost', 'WarrantyCost_TotalCost', 'RnDCost_TotalCost', 'OtherCost_TotalCost', 'ProfitCost_TotalCost', 'TechCost_TotalCost',
                                'EmissionRepairCost_Owner_TotalCost', 'DEFCost_TotalCost', 'FuelCost_Pretax_TotalCost', 'OperatingCost_BCA_TotalCost',
                                'TechAndOperatingCost_BCA_TotalCost']
    preamble_program_table = DocTables(bca).preamble_ria_tables(preamble_program_metrics, ['DiscountRate', 'optionID', 'OptionName', 'yearID'], 'sum')
    preamble_program_table = gen_fxns.round_sig(preamble_program_table, 1000000, 2, *preamble_program_metrics)
    preamble_program_table.insert(len(preamble_program_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    preamble_program_table_pv = DocTables(bca).preamble_ria_tables(preamble_program_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    preamble_program_table_pv = gen_fxns.round_sig(preamble_program_table_pv, 1000000, 2, *preamble_program_metrics)
    preamble_program_table_pv.insert(len(preamble_program_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    ria_program_metrics = ['TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'TechAndOperatingCost_BCA_TotalCost']
    ria_program_table = DocTables(bca).preamble_ria_tables(ria_program_metrics, ['DiscountRate', 'optionID', 'OptionName', 'yearID'], 'sum')
    ria_program_table = gen_fxns.round_sig(ria_program_table, 1000000, 2, *ria_program_metrics)
    ria_program_table.insert(len(ria_program_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    ria_program_table_pv = DocTables(bca).preamble_ria_tables(ria_program_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    ria_program_table_pv = gen_fxns.round_sig(ria_program_table_pv, 1000000, 2, *ria_program_metrics)
    ria_program_table_pv.insert(len(ria_program_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_metrics = ['DirectCost_TotalCost', 'WarrantyCost_TotalCost', 'RnDCost_TotalCost', 'OtherCost_TotalCost', 'ProfitCost_TotalCost', 'TechCost_TotalCost']
    tech_by_ft_yr_table = DocTables(bca).preamble_ria_tables(tech_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID', 'yearID'], 'sum')
    tech_by_ft_yr_table = gen_fxns.round_sig(tech_by_ft_yr_table, 1000000, 2, *tech_metrics)
    tech_by_ft_yr_table.insert(len(tech_by_ft_yr_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_ft_yr_table_pv = DocTables(bca).preamble_ria_tables(tech_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID'], 'sum')
    tech_by_ft_yr_table_pv = gen_fxns.round_sig(tech_by_ft_yr_table_pv, 1000000, 2, *tech_metrics)
    tech_by_ft_yr_table_pv.insert(len(tech_by_ft_yr_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_ft_rc_table = DocTables(bca).preamble_ria_tables(tech_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'regClassID'], 'sum')
    tech_by_ft_rc_table = gen_fxns.round_sig(tech_by_ft_rc_table, 1000000, 2, *tech_metrics)
    tech_by_ft_rc_table.insert(len(tech_by_ft_rc_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_ft_alt_table = DocTables(bca).preamble_ria_tables(tech_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName'], 'sum')
    tech_by_ft_alt_table = gen_fxns.round_sig(tech_by_ft_alt_table, 1000000, 2, *tech_metrics)
    tech_by_ft_alt_table.insert(len(tech_by_ft_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    tech_by_alt_table = DocTables(bca).preamble_ria_tables(tech_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    tech_by_alt_table = gen_fxns.round_sig(tech_by_alt_table, 1000000, 2, *tech_metrics)
    tech_by_alt_table.insert(len(tech_by_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_metrics = ['EmissionRepairCost_Owner_TotalCost', 'DEFCost_TotalCost', 'FuelCost_Pretax_TotalCost', 'OperatingCost_BCA_TotalCost']
    operating_ft_year_table = DocTables(bca).preamble_ria_tables(operating_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID', 'yearID'], 'sum')
    operating_ft_year_table = gen_fxns.round_sig(operating_ft_year_table, 1000000, 2, *operating_metrics)
    operating_ft_year_table.insert(len(operating_ft_year_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_ft_year_table_pv = DocTables(bca).preamble_ria_tables(operating_metrics, ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID'], 'sum')
    operating_ft_year_table_pv = gen_fxns.round_sig(operating_ft_year_table_pv, 1000000, 2, *operating_metrics)
    operating_ft_year_table_pv.insert(len(operating_ft_year_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_by_ft_rc_table = DocTables(bca).preamble_ria_tables(operating_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'regClassID'], 'sum')
    operating_by_ft_rc_table = gen_fxns.round_sig(operating_by_ft_rc_table, 1000000, 2, *operating_metrics)
    operating_by_ft_rc_table.insert(len(operating_by_ft_rc_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_by_ft_alt_table = DocTables(bca).preamble_ria_tables(operating_metrics, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName'], 'sum')
    operating_by_ft_alt_table = gen_fxns.round_sig(operating_by_ft_alt_table, 1000000, 2, *operating_metrics)
    operating_by_ft_alt_table.insert(len(operating_by_ft_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    operating_by_alt_table = DocTables(bca).preamble_ria_tables(operating_metrics, ['DiscountRate', 'optionID', 'OptionName'], 'sum')
    operating_by_alt_table = gen_fxns.round_sig(operating_by_alt_table, 1000000, 2, *operating_metrics)
    operating_by_alt_table.insert(len(operating_by_alt_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    econ_table_metrics = ['TechCost_TotalCost']
    econ_table = pd.pivot_table(bca, econ_table_metrics, ['DiscountRate', 'yearID'], columns=['optionID', 'OptionName'], aggfunc='sum')
    econ_table = econ_table.reset_index(drop=False)
    econ_table.insert(len(econ_table.columns), 'Units_SignificantDigits', 'USD; No rounding')

    bca_cost_metrics = ['TechAndOperatingCost_BCA_TotalCost']
    bca_cost_table = pd.pivot_table(bca, bca_cost_metrics, ['DiscountRate', 'yearID'], columns=['optionID', 'OptionName'], aggfunc='sum')
    bca_cost_table = bca_cost_table.reset_index(drop=False)
    bca_cost_table.insert(len(bca_cost_table.columns), 'Units_SignificantDigits', 'USD; No rounding')
    
    bca_cost_table_pv = pd.pivot_table(bca, bca_cost_metrics, ['DiscountRate'], columns=['optionID', 'OptionName'], aggfunc='sum')
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

    ages_cols = ['TypicalVMTperYear', 'Warranty_Miles', 'Warranty_Age', 'CalculatedAgeWhenWarrantyReached', 'EstimatedAge_Warranty', 'UsefulLife_Miles', 'UsefulLife_Age', 'CalculatedAgeWhenUsefulLifeReached', 'EstimatedAge_UsefulLife']
    ages_table = DocTables(bca.loc[bca['DiscountRate'] == 0, :])\
        .preamble_ria_tables(ages_cols, ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'modelYearID', 'Vehicle_Name_MOVES', 'sourceTypeID', 'regClassID'], 'mean')

    elapsed_time_calcs = time.time() - start_time_calcs

    print("\nSaving the outputs....")
    start_time_outputs = time.time()

    # set results path in which to save all files created or used/copied by this module
    # and set output path in which to save all files created by this module; the output path will be in the results path
    # move this to earlier in main if results folder location is made user selectable so that the selection is made shortly after start of run
    settings.path_outputs.mkdir(exist_ok=True)
    path_of_run_folder = settings.path_outputs.joinpath(f'{settings.start_time_readable}_CTI_{settings.run_folder_identifier}')
    path_of_run_folder.mkdir(exist_ok=False)
    path_of_run_inputs_folder = path_of_run_folder.joinpath('run_inputs')
    path_of_run_inputs_folder.mkdir(exist_ok=False)
    path_of_run_results_folder = path_of_run_folder.joinpath('run_results')
    path_of_run_results_folder.mkdir(exist_ok=False)
    path_of_modified_inputs_folder = path_of_run_folder.joinpath('modified_inputs')
    path_of_modified_inputs_folder.mkdir(exist_ok=False)
# TODO the techcost_per_veh table is not working, where upstream has this gone wrong - maybe eliminate these summary files?
    # now build some high level summary tables for copy/paste into slides/documents/etc. # TODO rewrite this to make use of pd.pivot_table()?
    techcost_per_veh_cols = ['DiscountRate', 'yearID', 'regclass', 'fueltype', 'OptionName']
    result_cols = ['DirectCost_AvgPerVeh', 'WarrantyCost_AvgPerVeh', 'RnDCost_AvgPerVeh', 'OtherCost_AvgPerVeh', 'ProfitCost_AvgPerVeh', 'TechCost_AvgPerVeh']
    techcost_per_veh_cols += result_cols
    discount_rates = [0]
    techcost_years = settings.techcost_summary_years
    regclasses = ['LHD', 'LHD45', 'MHD67', 'HHD8', 'Urban Bus']
    fueltypes = ['Diesel', 'Gasoline', 'CNG']
    techcost_per_veh_file = pd.ExcelWriter(path_of_run_results_folder.joinpath('techcosts_AvgPerVeh.xlsx'))
    DocTables(bca_summary['yearID_rc_ft']).techcost_per_veh_table(discount_rates, techcost_years, regclasses, fueltypes, techcost_per_veh_cols, techcost_per_veh_file)
    techcost_per_veh_file.save()

    bca_cols = ['OptionName', 'DiscountRate', 'TechCost_TotalCost', 'OperatingCost_BCA_TotalCost', 'TechAndOperatingCost_BCA_TotalCost']
    bca_years = settings.bca_summary_years
    bca_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annual.xlsx'))
    if settings.calc_pollution_effects == 'Y':
        DocTables(bca_summary['yearID']).bca_yearID_tables('', 0, bca_years, 'billions', bca_cols, bca_annual,
                                                           f'CriteriaCost_low_{discrate_criteria_high}', f'CriteriaCost_high_{discrate_criteria_low}')
    else:
        DocTables(bca_summary['yearID']).bca_yearID_tables('', 0, bca_years, 'billions', bca_cols, bca_annual)
    bca_annual.save()

    bca_npv = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_npv.xlsx'))
    if settings.calc_pollution_effects == 'Y':
        DocTables(bca_summary['yearID']).bca_yearID_tables('_CumSum', discrate_criteria_low, bca_years, 'billions', bca_cols, bca_npv,
                                                           f'CriteriaCost_low_{discrate_criteria_low}', f'CriteriaCost_high_{discrate_criteria_low}')
        DocTables(bca_summary['yearID']).bca_yearID_tables('_CumSum', discrate_criteria_high, bca_years, 'billions', bca_cols, bca_npv,
                                                           f'CriteriaCost_low_{discrate_criteria_high}', f'CriteriaCost_high_{discrate_criteria_high}')
    else:
        DocTables(bca_summary['yearID']).bca_yearID_tables('_CumSum', settings.discrate_social_low, bca_years, 'billions', bca_cols, bca_npv)
        DocTables(bca_summary['yearID']).bca_yearID_tables('_CumSum', settings.discrate_social_high, bca_years, 'billions', bca_cols, bca_npv)
    bca_npv.save()

    bca_annualized = pd.ExcelWriter(path_of_run_results_folder.joinpath('bca_annualized.xlsx'))
    if settings.calc_pollution_effects == 'Y':
        DocTables(bca_summary['yearID']).bca_yearID_tables('_Annualized', discrate_criteria_low, bca_years, 'billions', bca_cols, bca_annualized,
                                                           f'CriteriaCost_low_{discrate_criteria_low}', f'CriteriaCost_high_{discrate_criteria_low}')
        DocTables(bca_summary['yearID']).bca_yearID_tables('_Annualized', discrate_criteria_high, bca_years, 'billions', bca_cols, bca_annualized,
                                                           f'CriteriaCost_low_{discrate_criteria_high}', f'CriteriaCost_high_{discrate_criteria_high}')
    else:
        DocTables(bca_summary['yearID']).bca_yearID_tables('_Annualized', settings.discrate_social_low, bca_years, 'billions', bca_cols, bca_annualized)
        DocTables(bca_summary['yearID']).bca_yearID_tables('_Annualized', settings.discrate_social_high, bca_years, 'billions', bca_cols, bca_annualized)
    bca_annualized.save()

    # note that the inventory tables created below include MY2027+ only since emission_costs_sum is based on fleet_bca
    if settings.calc_pollution_effects == 'Y':
        inventory_cols = ['OptionName', 'yearID', 'PM25_onroad', 'NOx_onroad']
        inventory_years = settings.bca_summary_years
        inventory_annual = pd.ExcelWriter(path_of_run_results_folder.joinpath('inventory_annual_IncludedModelYears.xlsx'))
        DocTables(bca_summary['yearID']).inventory_tables1(inventory_years, inventory_cols, inventory_annual)
        inventory_annual.save()

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    inputs_filename_list = gen_fxns.inputs_filenames(settings.input_files_pathlist)

    for file in inputs_filename_list:
        path_source = settings.path_inputs.joinpath(file)
        path_destination = path_of_run_inputs_folder.joinpath(file)
        shutil.copy2(path_source, path_destination) # copy2 maintains original timestamp metadata
    fuel_prices.to_csv(path_of_modified_inputs_folder.joinpath('fuel_prices_' + settings.aeo_case + '.csv'), index=False)
    settings.regclass_costs.to_csv(path_of_modified_inputs_folder.joinpath('regclass_costs.csv'), index=False)
    markup_scalers_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('markup_scalers_reshaped.csv'), index=False)
    settings.repair_and_maintenance.to_csv(path_of_modified_inputs_folder.joinpath('repair_and_maintenance.csv'))
    settings.def_prices.to_csv(path_of_modified_inputs_folder.joinpath('def_prices.csv'), index=False)
    gdp_deflators = pd.DataFrame(gdp_deflators)  # from dict to df
    gdp_deflators.to_csv(path_of_modified_inputs_folder.joinpath('gdp_deflators.csv'), index=True)
    if settings.calc_pollution_effects == 'Y':
        criteria_emission_costs_reshaped.to_csv(path_of_modified_inputs_folder.joinpath('criteria_emission_costs_reshaped.csv'), index=False)

    # write some output files
    weighted_repair_owner_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_emission_repair_owner_cpm.csv'), index=True)
    weighted_def_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_def_cpm.csv'), index=True)
    weighted_fuel_cpm_df.to_csv(path_of_run_results_folder.joinpath('vmt_weighted_fuel_cpm.csv'), index=True)
    bca_summary['yearID'].to_csv(path_of_run_results_folder.joinpath('bca_by_yearID.csv'), index=False)

    document_tables_file = pd.ExcelWriter(path_of_run_results_folder.joinpath('preamble_ria_tables.xlsx'))
    for sheet_name in doc_table_dict:
        doc_table_dict[sheet_name].to_excel(document_tables_file, sheet_name=sheet_name)
    # document_tables_file.save()
    ages_table.to_csv(path_of_run_results_folder / 'ages.csv', index=True)

    # for figures, an updated options_dict would be nice
    for alt_num in range(1, len(settings.options_dict)):
        k = alt_num * 10
        alt0 = settings.options_dict[0]['OptionName']
        alt = settings.options_dict[alt_num]['OptionName']
        settings.options_dict.update({k: {'OptionName': f'{alt}_minus_{alt0}'}})

    if settings.generate_emissionrepair_cpm_figures != 'N':
        cpm_figure_years = settings.generate_emissionrepair_cpm_figures.split(',')
        for i, v in enumerate(cpm_figure_years):
            cpm_figure_years[i] = pd.to_numeric(cpm_figure_years[i])
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(bca.loc[bca['optionID'] < 10, 'optionID']).unique()
        veh_names = pd.Series(bca['Vehicle_Name_MOVES']).unique()
        for veh_name in veh_names:
            for cpm_figure_year in cpm_figure_years:
                CreateFigures(bca, settings.options_dict, path_figures).line_chart_vs_age(0, alts, cpm_figure_year, veh_name, 'EmissionRepairCost_Owner_AvgPerMile')

    if settings.generate_BCA_ArgsByOption_figures == 'Y':
        yearID_min = int(bca['yearID'].min())
        yearID_max = int(bca['yearID'].max())
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(bca.loc[bca['optionID'] >= 10, 'optionID']).unique()
        for alt in alts:
            CreateFigures(bca_summary['yearID'], settings.options_dict, path_figures).line_chart_args_by_option(0, alt, yearID_min, yearID_max,
                                                                                                                'TechCost_TotalCost',
                                                                                                                'EmissionRepairCost_Owner_TotalCost',
                                                                                                                'DEFCost_TotalCost',
                                                                                                                'FuelCost_Pretax_TotalCost',
                                                                                                                'TechAndOperatingCost_BCA_TotalCost'
                                                                                                                )
    if settings.generate_BCA_ArgByOptions_figures == 'Y':
        yearID_min = int(bca['yearID'].min())
        yearID_max = int(bca['yearID'].max())
        path_figures = path_of_run_results_folder.joinpath('figures')
        path_figures.mkdir(exist_ok=True)
        alts = pd.Series(bca.loc[bca['optionID'] >= 10, 'optionID']).unique()
        args = ['TechCost_TotalCost',
                'EmissionRepairCost_Owner_TotalCost',
                'DEFCost_TotalCost',
                'FuelCost_Pretax_TotalCost',
                'TechAndOperatingCost_BCA_TotalCost'
                ]
        for arg in args:
            CreateFigures(bca_summary['yearID'], settings.options_dict, path_figures).line_chart_arg_by_options(0, alts, yearID_min, yearID_max, arg)

    if settings.create_all_files == 'y' or settings.create_all_files == 'Y' or settings.create_all_files == '':
        bca.to_csv(path_of_run_results_folder.joinpath('bca_all_calcs.csv'), index=False)

    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder', 'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [cti_bca_tool.__version__, path_of_run_folder, settings.start_time_readable, settings.elapsed_time_read, elapsed_time_calcs, elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log = pd.concat([summary_log, gen_fxns.get_file_datetime(settings.input_files_pathlist)], axis=0, sort=False, ignore_index=True)

    # add summary log to document_tables_file for tracking this file which is the most likely to be shared
    summary_log.to_excel(document_tables_file, sheet_name='summary_log', index=False)
    document_tables_file.save()
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)
    print(f'\nOutput files have been saved to {path_of_run_folder}')


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs
    main(SetInputs())
