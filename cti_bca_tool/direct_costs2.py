import pandas as pd
from itertools import product
# from cti_bca_tool.project_classes import Moves
from cti_bca_tool import project_fleet


# create some dictionaries for storing data
cumulative_sales_dict = dict()
pkg_cost = dict()


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


def seedvol_factor(seedvol_df, vehicle):
    """

    :param: seedvol_df: A DataFrame of learning rate scalers (seed volume factors) by regclass and fueltype.
    :return:  A single seed volume factor for use in calculating learning effects for the given vehicle in the given implementation step.
    """
    alt, rc, ft = vehicle
    pkg_seedvol_df = pd.DataFrame(seedvol_df.loc[(seedvol_df['optionID'] == alt)
                                                 & (seedvol_df['regClassID'] == rc)
                                                 & (seedvol_df['fuelTypeID'] == ft), 'SeedVolumeFactor'])
    pkg_seedvol_df.reset_index(drop=True, inplace=True)
    pkg_seedvol = pkg_seedvol_df['SeedVolumeFactor'][0]
    return pkg_seedvol


def tech_pkg_cost_with_learning(vehicle, sales_df, costs_df, seedvol_df, learning_rate):
    """

    :param _learning_rate: The learning rate entered in the BCA inputs sheet.
    :return: A DataFrame of learned, year-over-year direct manufacturer package costs for the given vehicle in the given implementation step.
    """
    return_df = sales_df.copy()
    vpop_age0 = return_df['VPOP'][0]
    model_year = return_df['modelYearID'][0]
    seedvolume_factor = seedvol_factor(seedvol_df, vehicle)
    # insert some new columns, set to zero or empty string, then calc desired results
    new_arg_numeric = [f'VPOP_CumSum', f'DirectCost_AvgPerVeh']
    for arg in new_arg_numeric:
        return_df.insert(len(return_df.columns), arg, 0)
    # now calculate results for these new metrics
    return_df[f'VPOP_CumSum'] = return_df['VPOP'].cumsum()
    return_df[f'DirectCost_AvgPerVeh'] = tech_package_cost(costs_df, vehicle, model_year) \
                                         * (((return_df[f'VPOP_CumSum']
                                              + (vpop_age0 * seedvolume_factor))
                                             / (vpop_age0 + (vpop_age0 * seedvolume_factor))) ** learning_rate)
    return_df.drop(columns=['VPOP', 'VPOP_CumSum'], inplace=True)
    return return_df


def tech_pkg_cost_withlearning_2(vehicle, step, model_year, project_regclass_sales_dict, costs_df, seedvol_df, learning_rate):
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
        cumulative_sales = project_regclass_sales_dict[((vehicle), int(step))]['VPOP']
        sales_year1 = project_regclass_sales_dict[((vehicle), int(step))]['VPOP']
        seedvolume_factor = seedvol_factor(seedvol_df, vehicle)
        pkg_cost = tech_package_cost(costs_df, vehicle, int(step))
    # apply learning effects to the package costs to get a learned package cost in the given year
    pkg_cost_learned = pkg_cost \
                       * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate)
    cumulative_sales_dict[cumulative_sales_dict_id] = cumulative_sales, sales_year1, seedvolume_factor, pkg_cost
    return pkg_cost_learned, cumulative_sales


def per_veh_direct_costs(settings, vehicles, project_sales_dict):
    """

    :param vehicles: A list/array of vehicles by alt_regclass_fueltype.
    :param project_sales_dict: A dictionary of the project fleet consisting of new vehicle sales by year.
    :param settings:
    :param moves_adjustments:
    :param cost_steps:
    :param model_year:
    :param project_regclass_sales_dict:
    :param costs_df:
    :param seedvol_df:
    :param learning_rate:
    :return: Two dictionaries - one dictionary of per vehicle package costs by model year and by implementation step and another dictionary of
    per vehicle package costs by model year.
    """
    print('\nCalculating per vehicle direct costs\n')
    costs_by_year_by_step_dict = dict()
    costs_by_year_dict = dict()
    for vehicle, step in product(vehicles, settings.cost_steps):
        alt, rc, ft = vehicle
        for model_year in range(int(step), settings.year_max + 1):
            pkg_cost, cumulative_sales = tech_pkg_cost_withlearning_2(vehicle, step, model_year, project_sales_dict,
                                                                      settings.regclass_costs, settings.regclass_learningscalers,
                                                                      settings.learning_rate)
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


def per_veh_direct_costs_to_csv(dict_to_save, save_path):
    """

    :param dict_to_save: A dictionary having ((vehicle), year, step) keys where vehicle is an alt_rc_ft tuple.
    :return: A DataFrame by vehicle and model year.
    """
    df = pd.DataFrame(dict_to_save).transpose()
    df.reset_index(inplace=True)
    df.rename(columns={'level_0': 'alt_rc_ft', 'level_1': 'modelYearID', 'level_2': 'cost_step'}, inplace=True)
    df.to_csv(f'{save_path}.csv', index=False)


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool import project_fleet

    project_fleet_df = project_fleet.project_fleet_df(settings)
    vehicles_rc = pd.Series(project_fleet_df['alt_rc_ft'].unique())
    project_regclass_sales_dict = project_fleet.project_regclass_sales_dict(project_fleet_df)
    per_veh_dc_by_year_by_step_dict, per_veh_dc_by_year_dict \
        = per_veh_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)

    # save dicts to csv
    per_veh_direct_costs_to_csv(per_veh_dc_by_year_by_step_dict, settings.path_project / 'test/per_veh_direct_costs_by_year_by_step')
    per_veh_direct_costs_to_csv(per_veh_dc_by_year_dict, settings.path_project / 'test/per_veh_direct_costs_by_year')
