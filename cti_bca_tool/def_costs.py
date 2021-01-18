
import pandas as pd
from itertools import product


base_doserate_dict = dict()


def calc_def_doserate(settings, vehicle):
    alt, st, rc, ft = vehicle
    base_doserate_dict_id = (rc, ft)
    if base_doserate_dict_id in base_doserate_dict:
        base_doserate = base_doserate_dict[base_doserate_dict_id]
    else:
        nox_std = settings.def_doserate_inputs_dict[(rc, ft)]['standard_NOx']
        nox_engine_out = settings.def_doserate_inputs_dict[(rc, ft)]['engineout_NOx']
        doserate_intercept = settings.def_doserate_inputs_dict[(rc, ft)]['intercept_DEFdoserate']
        doserate_slope = settings.def_doserate_inputs_dict[(rc, ft)]['slope_DEFdoserate']
        base_doserate = ((nox_std - nox_engine_out) - doserate_intercept) / doserate_slope
        base_doserate_dict[base_doserate_dict_id] = base_doserate
    return base_doserate


def calc_nox_reduction(vehicle, year, model_year, fleet_totals_dict):
    """

    :param settings: The SetInputs class.
    :param vehicle: An alt_st_rc_ft vehicle
    :param year: The calendar year (yearID).
    :param model_year: The model year.
    :param fleet_dict: The fleet dictionary.
    :return: The NOx reduction in terms of the no action case less the action case (larger no action emissions result in positive reductions).
    """
    alt, st, rc, ft = vehicle
    age = year - model_year
    nox_reduction = fleet_totals_dict[((0, st, rc, ft), model_year, age)]['NOx_UStons'] - fleet_totals_dict[((vehicle), model_year, age)]['NOx_UStons']
    return nox_reduction


def calc_def_gallons(settings, vehicle, year, model_year, fleet_totals_dict):
    age = year - model_year
    gallons_fuel = fleet_totals_dict[((vehicle), model_year, age)]['Gallons']
    base_doserate = calc_def_doserate(settings, vehicle)
    nox_reduction = calc_nox_reduction(vehicle, year, model_year, fleet_totals_dict)
    gallons_def = gallons_fuel * base_doserate + nox_reduction * settings.def_gallons_per_ton_nox_reduction
    return gallons_def


def calc_def_costs(settings, fleet_totals_dict):
    print('\nCalculating total DEF costs.')
    for key in fleet_totals_dict.keys():
        vehicle = key[0]
        model_year, age = key[1], key[2]
        alt, st, rc, ft = vehicle
        if ft == 2:
            year = model_year + age
            def_price = settings.def_prices_dict[year]['DEF_USDperGal']
            gallons_def = calc_def_gallons(settings, vehicle, year, model_year, fleet_totals_dict)
            fleet_totals_dict[key].update({'DEF_Gallons': gallons_def, 'DEFCost': def_price * gallons_def})
    return fleet_totals_dict


def calc_average_def_costs(fleet_totals_dict, fleet_averages_dict):
    print('\nCalculating DEF average cost per mile.')
    for key in fleet_averages_dict.keys():
        alt, st, rc, ft = key[0]
        if ft == 2:
            def_cost = fleet_totals_dict[key]['DEFCost']
            vmt = fleet_totals_dict[key]['VMT']
            vpop = fleet_totals_dict[key]['VPOP']
            fleet_averages_dict[key].update({'DEFCost_AvgPerMile': def_cost / vmt})
            fleet_averages_dict[key].update({'DEFCost_AvgPerVeh': def_cost / vpop})
    return fleet_averages_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    vehicles_st = sourcetype_vehicles(project_fleet_df)

    fleet_totals_dict = calc_def_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_def_costs(fleet_totals_dict, fleet_averages_dict)

    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
