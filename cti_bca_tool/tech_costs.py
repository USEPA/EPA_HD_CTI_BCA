
import pandas as pd
from itertools import product


per_veh_tech_cost_dict = dict()


def calc_per_veh_tech_costs(fleet_averages_dict):
    print('\nCalculating per vehicle technology costs.\n')
    for key in fleet_averages_dict.keys():
        age = key[2]
        if age == 0:
            dc_per_veh = fleet_averages_dict[key]['DirectCost_AvgPerVeh']
            ic_per_veh = fleet_averages_dict[key]['IndirectCost_AvgPerVeh']
            fleet_averages_dict[key].update({'TechCost_AvgPerVeh': dc_per_veh + ic_per_veh})
    return fleet_averages_dict


def calc_tech_costs(fleet_totals_dict, fleet_averages_dict):
    """

    :param settings:
    :param vehicles: (alt, st, rc, ft) vehicles
    :param per_veh_tc_dict:
    :param fleet_dict:
    :return:
    """
    print('\nCalculating total technology costs.\n')
    for key in fleet_totals_dict.keys():
        age = key[2]
        if age == 0:
            cost_per_veh = fleet_averages_dict[key]['TechCost_AvgPerVeh']
            sales = fleet_totals_dict[key]['VPOP']
            fleet_totals_dict[key].update({'TechCost': cost_per_veh * sales})
    return fleet_totals_dict

# def calc_per_veh_tech_costs(settings, vehicles, per_veh_dc_dict, per_veh_ic_dict):
#     print('\nCalculating per vehicle technology costs.\n')
#     for vehicle, year in product(vehicles, settings.model_years):
#         dc_per_veh = per_veh_dc_dict[((vehicle), year)]['DirectCost_AvgPerVeh']
#         ic_per_veh = per_veh_ic_dict[((vehicle), year)]['IndirectCost_AvgPerVeh']
#         per_veh_tech_cost_dict[((vehicle), year)] = {'TechCost_AvgPerVeh': dc_per_veh + ic_per_veh}
#     return per_veh_tech_cost_dict
#
#
# def calc_tech_costs(settings, vehicles, per_veh_tc_dict, fleet_dict):
#     """
#
#     :param settings:
#     :param vehicles: (alt, st, rc, ft) vehicles
#     :param per_veh_tc_dict:
#     :param fleet_dict:
#     :return:
#     """
#     print('\nCalculating total technology costs.\n')
#     for vehicle, year in product(vehicles, settings.model_years):
#         alt, st, rc, ft = vehicle
#         rc_vehicle = (alt, rc, ft)
#         cost_per_veh = per_veh_tc_dict[((rc_vehicle), year)]['TechCost_AvgPerVeh']
#         sales = fleet_dict[((vehicle), year, 0)]['VPOP']
#         fleet_dict[((vehicle), year, 0)].update({'TechCost': cost_per_veh * sales})
#     return fleet_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs import calc_per_regclass_direct_costs, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    project_regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    per_veh_dc_by_year_dict = calc_per_regclass_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]

    fleet_totals_dict = calc_direct_costs(per_veh_dc_by_year_dict, fleet_totals_dict)
    fleet_averages_dict = calc_per_veh_direct_costs(fleet_totals_dict, fleet_averages_dict)

    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_tech_costs(fleet_averages_dict)

    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)
    fleet_totals_dict = calc_tech_costs(fleet_totals_dict, fleet_averages_dict)

    # save dicts to csv
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
