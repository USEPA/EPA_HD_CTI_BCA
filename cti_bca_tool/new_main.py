

# import pandas as pd
# import numpy as np
# import shutil
# from datetime import datetime
# from itertools import product
# import time
# import cti_bca_tool
# from cti_bca_tool.get_context_data import GetFuelPrices, GetDeflators
# from cti_bca_tool.fleet import Fleet
# from cti_bca_tool.vehicle import Vehicle, regClassID, fuelTypeID
# from cti_bca_tool.direct_cost import DirectCost
# from cti_bca_tool.indirect_cost import IndirectCost, IndirectCostScalers
# from cti_bca_tool.operating_cost import DEFCost, ORVRadjust, FuelCost, RepairAndMaintenanceCost
# from cti_bca_tool.discounting import DiscountValues
# from cti_bca_tool.group_metrics import GroupMetrics
# from cti_bca_tool.calc_deltas import CalcDeltas
# from cti_bca_tool.emission_cost import EmissionCost
# from cti_bca_tool.weighted_results import WeightedResult
# from cti_bca_tool.doc_tables import DocTables
# from cti_bca_tool.estimated_age import EstimatedAge
# from cti_bca_tool.figures import CreateFigures
# from cti_bca_tool.data_table import DataTable
# import cti_bca_tool.general_functions as gen_fxns
# from cti_bca_tool.project_classes import Moves
from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_per_veh_direct_costs, calc_direct_costs
from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
from cti_bca_tool.tech_costs import calc_per_veh_tech_costs, calc_tech_costs
from cti_bca_tool.def_costs import calc_def_costs, calc_average_def_costs
from cti_bca_tool.fuel_costs import calc_fuel_costs, calc_average_fuel_costs
from cti_bca_tool.repair_costs import calc_emission_repair_costs_per_mile, calc_per_veh_emission_repair_costs, \
    calc_emission_repair_costs, estimated_ages_dict, repair_cpm_dict
from cti_bca_tool.emission_costs import calc_criteria_emission_costs
from cti_bca_tool.sum_by_vehicle import calc_sum_of_costs
from cti_bca_tool.discounting import discount_values
from cti_bca_tool.calc_deltas import calc_deltas
from cti_bca_tool.doc_tables import post_process

from cti_bca_tool.general_functions import save_dict_to_csv, convert_dict_to_df


def new_main(settings):

    # create project fleet data structures, both a DataFrame and a dictionary of regclass based sales
    project_fleet_df = create_fleet_df(settings)

    # create a sales (by regclass) and fleet dictionaries
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(settings, project_fleet_df, 0)
    fleet_averages_dict = create_fleet_averages_dict(settings, project_fleet_df)

    # calculate direct costs per reg class based on cumulative regclass sales (learning is applied to cumulative reg class sales)
    regclass_yoy_costs_per_step = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)

    # calculate total direct costs and then per vehicle costs (per sourcetype)
    fleet_averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step, fleet_averages_dict)
    fleet_totals_dict = calc_direct_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate indirect costs per vehicle and then total indirect costs
    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)

    # calculate tech costs per vehicle and total tech costs
    fleet_averages_dict = calc_per_veh_tech_costs(fleet_averages_dict)
    fleet_totals_dict = calc_tech_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate DEF costs
    fleet_totals_dict = calc_def_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_def_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate fuel costs, including adjustments for fuel consumption associated with ORVR
    fleet_totals_dict = calc_fuel_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_fuel_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate emission repair costs
    fleet_averages_dict = calc_emission_repair_costs_per_mile(settings, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_emission_repair_costs(fleet_averages_dict)
    fleet_totals_dict = calc_emission_repair_costs(fleet_totals_dict, fleet_averages_dict)

    # sum operating costs and operating-tech costs into a single key, value
    fleet_totals_dict = calc_sum_of_costs(fleet_totals_dict, 'OperatingCost', 'DEFCost', 'FuelCost_Pretax', 'EmissionRepairCost')
    fleet_totals_dict = calc_sum_of_costs(fleet_totals_dict, 'TechAndOperatingCost', 'TechCost', 'OperatingCost')
    fleet_averages_dict = calc_sum_of_costs(fleet_averages_dict,
                                            'OperatingCost_Owner_AvgPerMile',
                                            'DEFCost_AvgPerMile', 'FuelCost_Retail_AvgPerMile', 'EmissionRepairCost_AvgPerMile')
    fleet_averages_dict = calc_sum_of_costs(fleet_averages_dict,
                                            'OperatingCost_Owner_AvgPerVeh',
                                            'DEFCost_AvgPerVeh', 'FuelCost_Retail_AvgPerVeh', 'EmissionRepairCost_AvgPerVeh')

    if settings.calc_pollution_effects == 'Y':
        fleet_totals_dict = calc_criteria_emission_costs(settings, fleet_totals_dict)

    # discount monetized values
    fleet_totals_dict = discount_values(settings, fleet_totals_dict, 0.03, 0.07)
    fleet_averages_dict = discount_values(settings, fleet_averages_dict, 0.03, 0.07)

    # calculate deltas relative to the passed no action alternative ID
    fleet_totals_dict = calc_deltas(settings, fleet_totals_dict, 0)
    fleet_averages_dict = calc_deltas(settings, fleet_averages_dict, 0)

    # convert dictionary to DataFrame to generate pivot tables for copy/past to documents
    fleet_totals_df = convert_dict_to_df(fleet_totals_dict, 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    post_process(settings, fleet_totals_df)

    # save dictionaries to csv
    print('\nSaving output files.')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(estimated_ages_dict, settings.path_project / 'test/estimated_ages', 'vehicle', 'modelYearID', 'identifier')
    save_dict_to_csv(repair_cpm_dict, settings.path_project / 'test/repair_cpm_details', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')

    t = 0


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    new_main(settings)