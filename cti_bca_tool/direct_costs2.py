import pandas as pd
from itertools import product
from cti_bca_tool import project_fleet


# create some dictionaries for storing data
cumulative_sales_dict = dict()
pkg_cost = dict()
costs_by_year_by_step_dict = dict()
costs_by_year_dict = dict()


def tech_package_cost(costs_df, vehicle, year):
    """
    :param: costs_df: A DataFrame of individual tech costs by regclass and fueltype.
    :return: A tech package cost (a single float value).
    """

    alt, rc, ft = vehicle
    techs_on_veh = costs_df.loc[(costs_df['optionID'] == alt)
                                & (costs_df['regClassID'] == rc)
                                & (costs_df['fuelTypeID'] == ft),
                                ['TechPackageDescription', str(year)]]
    pkg_cost = techs_on_veh[str(year)].sum(axis=0)
    return pkg_cost


# def seedvol_factor(seedvol_df, vehicle):
#     """
#
#     :param: seedvol_df: A DataFrame of learning rate scalers (seed volume factors) by regclass and fueltype.
#     :return:  A single seed volume factor for use in calculating learning effects for the given vehicle in the given implementation step.
#     """
#     alt, rc, ft = vehicle
#     pkg_seedvol_df = pd.DataFrame(seedvol_df.loc[(seedvol_df['optionID'] == alt)
#                                                  & (seedvol_df['regClassID'] == rc)
#                                                  & (seedvol_df['fuelTypeID'] == ft), 'SeedVolumeFactor'])
#     pkg_seedvol_df.reset_index(drop=True, inplace=True)
#     pkg_seedvol = pkg_seedvol_df['SeedVolumeFactor'][0]
#     return pkg_seedvol


def tech_pkg_cost_withlearning(settings, vehicle, step, model_year, project_regclass_sales_dict):
    """

    :param vehicle:
    :param step:
    :param model_year:
    :param project_regclass_sales_dict:
    :param costs_df:
    :param seedvol_df:
    :param learning_rate: The learning rate entered in the BCA inputs sheet.
    :return: A single package cost with learning applied along with the cumulative sales used in the learning calculation.
    """
    cumulative_sales_dict_id = ((vehicle), int(step))
    sales = project_regclass_sales_dict[((vehicle), model_year)]['VPOP']
    if cumulative_sales_dict_id in cumulative_sales_dict:
        cumulative_sales, sales_year1, seedvolume_factor, pkg_cost = cumulative_sales_dict[cumulative_sales_dict_id]
        cumulative_sales += sales
    else:
        sales_year1 = project_regclass_sales_dict[((vehicle), int(step))]['VPOP']
        cumulative_sales = sales_year1
        seedvolume_factor = settings.seedvol_factor_dict[vehicle]['SeedVolumeFactor']
        pkg_cost = tech_package_cost(settings.regclass_costs, vehicle, int(step))
    # apply learning effects to the package costs to get a learned package cost in the given year
    pkg_cost_learned = pkg_cost \
                       * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** settings.learning_rate)
    cumulative_sales_dict[cumulative_sales_dict_id] = cumulative_sales, sales_year1, seedvolume_factor, pkg_cost
    return pkg_cost_learned, cumulative_sales


def calc_per_veh_direct_costs(settings, vehicles, project_sales_dict):
    """

    :param vehicles: A list/array of vehicles by alt_regclass_fueltype.
    :param project_sales_dict: A dictionary of the project fleet consisting of new vehicle sales by year.
    :param settings: The project input settings.
    :return: Two dictionaries - one dictionary of per vehicle package costs by model year and by implementation step and another dictionary of
    per vehicle package costs by model year.
    """
    print('\nCalculating per vehicle direct costs.\n')
    for vehicle, step in product(vehicles, settings.cost_steps):
        alt, rc, ft = vehicle
        for model_year in range(int(step), settings.year_max + 1):
            pkg_cost, cumulative_sales = tech_pkg_cost_withlearning(settings, vehicle, step, model_year, project_sales_dict)
            costs_by_year_by_step_dict[((vehicle), model_year, int(step))] = {'CumulativeSales': cumulative_sales, 'DirectCost_AvgPerVeh': pkg_cost}
            if alt == 0 and step == settings.cost_steps[0]:
                costs_by_year_dict[((vehicle), model_year)] \
                    = {'DirectCost_AvgPerVeh': costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh']}
            elif alt == 0 and step != settings.cost_steps[0]:
                costs_by_year_dict[((vehicle), model_year)] = {'DirectCost_AvgPerVeh': costs_by_year_dict[((vehicle), model_year)]['DirectCost_AvgPerVeh']}
            elif step == settings.cost_steps[0]:
                costs_by_year_dict[((vehicle), model_year)] \
                    = {'DirectCost_AvgPerVeh': costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh'] \
                                               + costs_by_year_dict[((0, rc, ft), model_year)]['DirectCost_AvgPerVeh']}
            else:
                costs_by_year_dict[((vehicle), model_year)] \
                    = {'DirectCost_AvgPerVeh': costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh'] \
                                               + costs_by_year_dict[((vehicle), model_year)]['DirectCost_AvgPerVeh']}
    return costs_by_year_by_step_dict, costs_by_year_dict


def calc_direct_costs(settings, vehicles, costs_by_year_dict, fleet_totals_dict):
    print('\nCalculating total direct costs.\n')
    for vehicle, year in product(vehicles, settings.years):
        alt, st, rc, ft = vehicle
        vehicle_rc = (alt, rc, ft)
        cost_per_veh = costs_by_year_dict[((vehicle_rc), year)]['DirectCost_AvgPerVeh']
        sales = fleet_totals_dict[((vehicle), year, 0)]['VPOP']
        fleet_totals_dict[((vehicle), year, 0)].update({'DirectCost': cost_per_veh * sales})
    return fleet_totals_dict


def update_fleet_averages_dict(fleet_totals_dict, fleet_averages_dict):
    for k in fleet_totals_dict.keys():
        vehicle, model_year, age = k
        if age == 0:
            fleet_averages_dict[((vehicle), model_year, age)]\
                .update({'DirectCost_AvgPerVeh': fleet_totals_dict[((vehicle), model_year, age)]['DirectCost']
                                                 / fleet_totals_dict[((vehicle), model_year, age)]['VPOP']})
        else:
            pass
    return fleet_averages_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)
    project_regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    per_veh_dc_by_year_by_step_dict, per_veh_dc_by_year_dict \
        = calc_per_veh_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)

    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)
    vehicles_st = project_fleet.sourcetype_vehicles(project_fleet_df)
    fleet_totals_dict = calc_direct_costs(settings, vehicles_st, per_veh_dc_by_year_dict, fleet_totals_dict)
    fleet_averages_dict = update_fleet_averages_dict(fleet_totals_dict, fleet_averages_dict)

    # save dicts to csv
    save_dict_to_csv(per_veh_dc_by_year_by_step_dict, settings.path_project / 'test/per_veh_direct_costs_by_year_by_step', 'vehicle', 'modelYearID', 'cost_step')
    save_dict_to_csv(per_veh_dc_by_year_dict, settings.path_project / 'test/per_veh_direct_costs_by_year', 'vehicle', 'modelYearID')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/fleet_averages', 'vehicle', 'modelYearID', 'ageID')
