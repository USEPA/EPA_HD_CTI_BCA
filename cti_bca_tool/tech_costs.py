
import pandas as pd
from itertools import product


per_veh_tech_cost_dict = dict()


def calc_per_veh_tech_costs(settings, vehicles, per_veh_dc_dict, per_veh_ic_dict):
    print('\nCalculating per vehicle technology costs.\n')
    for vehicle, year in product(vehicles, settings.model_years):
        dc_per_veh = per_veh_dc_dict[((vehicle), year)]['DirectCost_AvgPerVeh']
        ic_per_veh = per_veh_ic_dict[((vehicle), year)]['IndirectCost_AvgPerVeh']
        per_veh_tech_cost_dict[((vehicle), year)] = {'TechCost_AvgPerVeh': dc_per_veh + ic_per_veh}
    return per_veh_tech_cost_dict


def calc_tech_costs(settings, vehicles, per_veh_tc_dict, fleet_dict):
    """

    :param settings:
    :param vehicles: (alt, st, rc, ft) vehicles
    :param per_veh_tc_dict:
    :param fleet_dict:
    :return:
    """
    print('\nCalculating total technology costs.\n')
    for vehicle, year in product(vehicles, settings.model_years):
        alt, st, rc, ft = vehicle
        rc_vehicle = (alt, rc, ft)
        cost_per_veh = per_veh_tc_dict[((rc_vehicle), year)]['TechCost_AvgPerVeh']
        sales = fleet_dict[((vehicle), year, 0)]['VPOP']
        fleet_dict[((vehicle), year, 0)].update({'TechCost': cost_per_veh * sales})
    return fleet_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, create_regclass_sales_dict, create_fleet_dict, sourcetype_vehicles
    from cti_bca_tool.direct_costs2 import calc_per_veh_direct_costs, calc_direct_costs
    from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    project_regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    per_veh_dc_by_year_dict = calc_per_veh_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]
    per_veh_ic_by_year_dict = calc_per_veh_indirect_costs(settings, vehicles_rc, per_veh_dc_by_year_dict)
    per_veh_tc_by_year_dict = calc_per_veh_tech_cost(settings, vehicles_rc, per_veh_dc_by_year_dict, per_veh_ic_by_year_dict)
    per_veh_tech_costs_df = pd.DataFrame(per_veh_tc_by_year_dict)

    fleet_dict = create_fleet_dict(project_fleet_df)
    vehicles_st = sourcetype_vehicles(project_fleet_df)
    fleet_dict = calc_direct_costs(settings, vehicles_st, per_veh_dc_by_year_dict, fleet_dict)
    fleet_dict = calc_indirect_costs(settings, vehicles_st, per_veh_ic_by_year_dict, fleet_dict)
    fleet_dict = calc_tech_cost(settings, vehicles_st, per_veh_tc_by_year_dict, fleet_dict)

    # save dicts to csv
    save_dict_to_csv(per_veh_tech_costs_df, settings.path_project / 'test/per_veh_tech_costs_by_year', 'vehicle', 'modelYearID')
    save_dict_to_csv(fleet_dict, settings.path_project / 'test/fleet_totals', 'vehicle', 'modelYearID', 'ageID')
