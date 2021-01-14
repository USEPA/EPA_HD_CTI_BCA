import pandas as pd
from itertools import product
from cti_bca_tool.project_classes import Moves
from cti_bca_tool.project_fleet import alt_rc_ft_vehicles


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
    :return:
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


def per_veh_direct_costs_by_year(settings, vehicles, project_sales_dict, max_year):
    """

    :param vehicles:
    :param project_sales_dict: A dictionary of the project fleet consisting of new vehicle sales by year.
    :param settings:
    :param moves_adjustments:
    :param cost_steps:
    :param model_year:
    :param project_regclass_sales_dict:
    :param costs_df:
    :param seedvol_df:
    :param learning_rate:
    :return:
    """
    costs_by_year_by_step_dict = dict()
    costs_by_year_dict = dict()
    for vehicle, step in product(vehicles, settings.cost_steps):
        alt, rc, ft = vehicle
        for model_year in range(int(step), max_year + 1):
            pkg_cost, cumulative_sales = tech_pkg_cost_withlearning_2(vehicle, step, model_year, project_sales_dict,
                                                                      settings.regclass_costs, settings.regclass_learningscalers,
                                                                      settings.learning_rate)
            costs_by_year_by_step_dict[((vehicle), model_year, int(step))] = {'CumulativeSales': cumulative_sales, 'DirectCost_AvgPerVeh': pkg_cost}
            if alt == 0 and step == settings.cost_steps[0]:
                costs_by_year_dict[((vehicle), model_year)] = costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh']
            elif alt == 0 and step != settings.cost_steps[0]:
                costs_by_year_dict[((vehicle), model_year)] = costs_by_year_dict[((vehicle), model_year)]
            elif step == settings.cost_steps[0]:
                costs_by_year_dict[((vehicle), model_year)] \
                    = costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh'] \
                      + costs_by_year_dict[((0, rc, ft), model_year)]
            else:
                costs_by_year_dict[((vehicle), model_year)] \
                    = costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh'] \
                      + costs_by_year_dict[((vehicle), model_year)]
    return costs_by_year_by_step_dict, costs_by_year_dict

    # for vehicle in vehicles:
    #     alt, rc, ft = vehicle
    #     for step_num in range(len(settings.cost_steps)):
    #         for model_year in range(int(settings.cost_steps[step_num]), max_year + 1):
    #             if alt == 0:
    #                 # alt = 0 is the no action case so costs are always equal to the first step of costs
    #                 costs_by_year_dict[((vehicle), model_year, 9999)] \
    #                     = costs_by_year_by_step_dict[((vehicle), model_year, int(settings.cost_steps[0]))]['DirectCost_AvgPerVeh']
    #             elif model_year < int(settings.cost_steps[step_num + 1]):
    #                 costs_by_year_dict[((vehicle), model_year, 9999)] \
    #                     = costs_by_year_by_step_dict[((vehicle), model_year, int(settings.cost_steps[step_num]))]['DirectCost_AvgPerVeh'] \
    #                       + costs_by_year_dict[((0, rc, ft), model_year, 9999)]
    #             else:
    #                 costs_by_year_dict[((vehicle), model_year, 9999)] \
    #                     = costs_by_year_by_step_dict[((vehicle), model_year, int(settings.cost_steps[step_num - 1]))]['DirectCost_AvgPerVeh'] \
    #                       + costs_by_year_by_step_dict[((vehicle), model_year, int(settings.cost_steps[step_num]))]['DirectCost_AvgPerVeh']\
    #                       + costs_by_year_by_step_dict[((0, rc, ft), model_year, 9999)]
                # else:
                #     costs_by_year_dict[((vehicle), model_year)] \
                #         = costs_by_year_by_step_dict[((vehicle), model_year, int(settings.cost_steps[step_num - 1]))]['DirectCost_AvgPerVeh'] \
                #           + costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh']
        # for step in settings.cost_steps:
        #     for model_year in range(int(step), max_year + 1):
        #         step_num = 0
        #         if model_year <= int(settings.cost_steps[step_num + 1]):
        #             costs_by_year_dict[((vehicle), model_year)] = costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh']
        #         else:
        #             costs_by_year_dict[((vehicle), model_year)] \
        #                 = costs_by_year_by_step_dict[((vehicle), model_year, int(settings.cost_steps[step_num - 1]))]['DirectCost_AvgPerVeh'] \
        #                   + costs_by_year_by_step_dict[((vehicle), model_year, int(step))]['DirectCost_AvgPerVeh']
    # return costs_by_year_dict


def per_veh_direct_costs_by_year_df(per_veh_direct_costs_dict):
    per_veh_direct_costs_df = pd.DataFrame(per_veh_direct_costs_dict).transpose()
    per_veh_direct_costs_df.reset_index(inplace=True)
    per_veh_direct_costs_df.rename(columns={'level_0': 'alt_rc_ft', 'level_1': 'modelYearID', 'level_2': 'cost_step'}, inplace=True)
    return per_veh_direct_costs_df


# def calc_per_veh_direct_costs_old(project_fleet, settings):
#     # create some dictionaries and dataframes to store data
#     direct_costs_veh_step_dict = dict()
#     direct_costs_veh_dict = dict()
#     direct_costs_fleet_df = pd.DataFrame()
#     # determine the cost steps - the model years for which new standards/cost-steps are incurred
#     cost_steps = [col for col in settings.regclass_costs.columns if '20' in col]
#     # determine the vehicles
#     vehicles = alt_rc_ft_vehicles(project_fleet)
#     # create a loop to get sales that will allow learning to be applied to tech package costs for each vehicle at each step
#     for vehicle, step in product(vehicles, cost_steps):
#         sales_df = ProjectClass(vehicle=vehicle).regclass_sales_following_given_my(project_fleet, settings.moves_adjustments, int(step))
#         direct_costs_veh_step_dict[vehicle, step] \
#             = tech_pkg_cost_withlearning(vehicle, sales_df, settings.regclass_costs, settings.regclass_learningscalers, settings.learning_rate)
#     # now concatenate the steps together for each vehicle to then groupby.sum()
#     for vehicle in vehicles:
#         direct_costs_veh_dict[vehicle] = pd.DataFrame()
#     for vehicle, step in product(vehicles, cost_steps):
#         direct_costs_veh_dict[vehicle] \
#             = pd.concat([direct_costs_veh_dict[vehicle], direct_costs_veh_step_dict[vehicle, step]], axis=0, ignore_index=True)
#     # now do the groupby.sum() to get a stream of costs model_year-over-model_year
#     for vehicle in vehicles:
#         direct_costs_veh_dict[vehicle] = direct_costs_veh_dict[vehicle].groupby(by=['optionID', 'modelYearID', 'ageID', 'regClassID', 'fuelTypeID'], as_index=False).sum()
#     # now sum the alt vehicles with the alt0 vehicles after first determining the non-alt0 vehicles
#     non_alt0_vehicles = alt_rc_ft_vehicles(project_fleet.loc[project_fleet['optionID'] != 0, :])
#     for vehicle in non_alt0_vehicles:
#         alt, rc, ft = vehicle
#         direct_costs_veh_dict[vehicle]['DirectCost_AvgPerVeh'] = direct_costs_veh_dict[vehicle]['DirectCost_AvgPerVeh'] \
#                                                                  + direct_costs_veh_dict[(0, rc, ft)]['DirectCost_AvgPerVeh']
#     # now concatenate everything in one direct_costs dataframe
#     for vehicle in vehicles:
#         direct_costs_fleet_df = pd.concat([direct_costs_fleet_df, direct_costs_veh_dict[vehicle]], axis=0, ignore_index=True)
#     return direct_costs_fleet_df, direct_costs_veh_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_classes import Moves
    from cti_bca_tool.project_fleet import project_fleet

    project_fleet_df = Moves(settings.moves).project_fleet_df(settings.moves_adjustments)
    vehicles = pd.Series(project_fleet_df['alt_rc_ft'].unique())
    project_regclass_sales_dict = Moves(settings.moves).project_regclass_sales_dict(settings.moves_adjustments)
    max_year = project_fleet_df['modelYearID'].max()
    per_veh_dc_by_year_by_step_dict, per_veh_dc_by_year_dict = per_veh_direct_costs_by_year(settings, vehicles, project_regclass_sales_dict, max_year)

    # per_veh_direct_costs_dict = dict()
    # for vehicle, step in product(vehicles, settings.cost_steps):
    #     for model_year in range(int(step), max_year + 1):
    #         pkg_cost, cumulative_sales = tech_pkg_cost_withlearning_2(vehicle, step, model_year, project_regclass_sales_dict,
    #                                                                   settings.regclass_costs, settings.regclass_learningscalers,
    #                                                                   settings.learning_rate)
    #         per_veh_direct_costs_dict[((vehicle), model_year, int(step))] = {'CumulativeSales': cumulative_sales, 'DirectCost_AvgPerVeh': pkg_cost}
    #
    #
    df = pd.DataFrame(per_veh_dc_by_year_by_step_dict).transpose()
    df.reset_index(inplace=True)
    df.rename(columns={'level_0': 'alt_rc_ft', 'level_1': 'modelYearID', 'level_2': 'cost_step'}, inplace=True)
    df.to_csv(settings.path_project / 'test/per_veh_direct_costs_by_year_by_step.csv', index=False)

    df = pd.DataFrame(per_veh_dc_by_year_dict, index=['DirectCost_AvgPerVeh']).transpose()
    df.reset_index(inplace=True)
    df.rename(columns={'level_0': 'alt_rc_ft', 'level_1': 'modelYearID', 'level_2': 'cost_step'}, inplace=True)
    df.to_csv(settings.path_project / 'test/per_veh_direct_costs_by_year.csv', index=False)


    # per_veh_direct_costs_by_year_by_step_df = pd.DataFrame(per_veh_dc_by_year_by_step_dict).transpose()
    # per_veh_direct_costs_by_year_by_step_df.reset_index(inplace=True)
    # per_veh_direct_costs_by_year_by_step_df.rename(columns={'level_0': 'alt_rc_ft', 'level_1': 'modelYearID', 'level_2': 'cost_step'}, inplace=True)
    # s = pd.Series(per_veh_direct_costs_df['alt_rc_ft'])
    # per_veh_direct_costs_df.insert(0, 'fuelTypeID', 0)
    # per_veh_direct_costs_df.insert(0, 'regClassID', 0)
    # per_veh_direct_costs_df.insert(0, 'optionID', 0)
    # for idx, value in enumerate(s):
    #     alt, rc, ft = s[idx]
    #     per_veh_direct_costs_df['optionID'][idx] = alt
    #     per_veh_direct_costs_df['regClassID'][idx] = rc
    #     per_veh_direct_costs_df['fuelTypeID'][idx] = ft

    # per_veh_direct_costs_df.to_csv(settings.path_project / 'test/per_veh_direct_costs.csv', index=False)
    # per_veh_direct_costs = dict()
    # for k, v in per_veh_direct_costs_dict.items():
