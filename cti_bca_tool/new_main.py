

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
# from cti_bca_tool.project_classes import Moves
from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
from cti_bca_tool.direct_costs2 import calc_per_regclass_direct_costs, calc_direct_costs, calc_per_veh_direct_costs
from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
from cti_bca_tool.tech_costs import calc_per_veh_tech_costs, calc_tech_costs
from cti_bca_tool.def_costs import calc_def_costs, calc_average_def_costs
from cti_bca_tool.fuel_costs import calc_fuel_costs, calc_average_fuel_costs
from cti_bca_tool.repair_costs import calc_emission_repair_costs_per_mile, calc_per_veh_emission_repair_costs, \
    calc_emission_repair_costs, estimated_ages_dict, repair_cpm_dict
from cti_bca_tool.emission_costs import calc_criteria_emission_costs

from cti_bca_tool.general_functions import save_dict_to_csv


def new_main(settings):

    # create project fleet data structures, both a DataFrame and a dictionary of regclass based sales
    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)
    vehicles_st = sourcetype_vehicles(project_fleet_df)

    # create a sales (by regclass) and fleet dictionaries
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    # calculate direct costs per reg class based on cumulative regclass sales (learning is applied to cumulative reg class sales)
    per_veh_dc_by_year_by_step_dict, per_veh_dc_by_year_dict \
        = calc_per_regclass_direct_costs(settings, vehicles_rc, regclass_sales_dict)

    # calculate total direct costs and then per vehicle costs (per sourcetype)
    fleet_totals_dict = calc_direct_costs(per_veh_dc_by_year_dict, fleet_totals_dict)
    fleet_averages_dict = calc_per_veh_direct_costs(fleet_totals_dict, fleet_averages_dict)

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
    fleet_averages_dict = calc_emission_repair_costs_per_mile(settings, per_veh_dc_by_year_dict, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_emission_repair_costs(fleet_averages_dict)
    fleet_totals_dict = calc_emission_repair_costs(fleet_totals_dict, fleet_averages_dict)

    if settings.calc_pollution_effects:
        fleet_totals_dict = calc_criteria_emission_costs(settings, fleet_totals_dict)

    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(estimated_ages_dict, settings.path_project / 'test/estimated_ages', 'vehicle', 'modelYearID', 'identifier')
    save_dict_to_csv(repair_cpm_dict, settings.path_project / 'test/repair_cpm_details', 'vehicle', 'modelYearID', 'ageID')
    t = 0


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    new_main(settings)