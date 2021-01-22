

# create some dictionaries for storing data
cumulative_sales_dict = dict()
pkg_cost_dict = dict()
costs_by_year_by_step_dict = dict()
costs_by_year_dict = dict()
regclass_yoy_costs_per_step_dict = dict()


def tech_package_cost(costs_df, vehicle, cost_step):
    """
    :param: costs_df: A DataFrame of individual tech costs by regclass and fueltype.
    :return: A tech package cost (a single float value).
    """
    pkg_cost_dict_key = ((vehicle), cost_step)
    if pkg_cost_dict_key in pkg_cost_dict.keys():
        pkg_cost = pkg_cost_dict[pkg_cost_dict_key]
    else:
        alt, rc, ft = vehicle
        techs_on_veh = costs_df.loc[(costs_df['optionID'] == alt)
                                    & (costs_df['regClassID'] == rc)
                                    & (costs_df['fuelTypeID'] == ft),
                                    ['TechPackageDescription', cost_step]]
        pkg_cost = techs_on_veh[cost_step].sum(axis=0)
        pkg_cost_dict[pkg_cost_dict_key] = pkg_cost
    return pkg_cost


def calc_cumulative_sales_by_step(vehicle, model_year, cost_step, regclass_sales_dict):
    cumulative_sales_dict_id = ((vehicle), model_year, cost_step)
    if cumulative_sales_dict_id in cumulative_sales_dict.keys():
        cumulative_sales = cumulative_sales_dict[cumulative_sales_dict_id]
    else:
        cumulative_sales = 0
        for year in range(int(cost_step), model_year + 1):
            cumulative_sales += regclass_sales_dict[((vehicle), year)]['VPOP']
        cumulative_sales_dict[cumulative_sales_dict_id] = cumulative_sales
    return cumulative_sales


def tech_pkg_cost_withlearning(settings, vehicle, model_year, cost_step, regclass_sales_dict):
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
    sales_year1 = regclass_sales_dict[((vehicle), int(cost_step))]['VPOP']
    cumulative_sales = calc_cumulative_sales_by_step(vehicle, model_year, cost_step, regclass_sales_dict)
    seedvolume_factor = settings.seedvol_factor_dict[vehicle]['SeedVolumeFactor']
    pkg_cost = tech_package_cost(settings.regclass_costs, vehicle, cost_step)
    pkg_cost_learned = pkg_cost \
                       * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** settings.learning_rate)
    return pkg_cost_learned, cumulative_sales


def calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict):
    """
    Calculate the year-over-year costs for each alt_rc_ft vehicle and for each standard implementation step.
    :param settings:
    :param project_sales_dict:
    :return:
    """
    for key in regclass_sales_dict.keys():
        vehicle, model_year = key[0], key[1]
        for cost_step in settings.cost_steps:
            if model_year >= int(cost_step):
                pkg_cost, cumulative_sales = tech_pkg_cost_withlearning(settings, vehicle, model_year, cost_step, regclass_sales_dict)
                regclass_yoy_costs_per_step_dict[((vehicle), model_year, cost_step)] = {'CumulativeSales': cumulative_sales, 'DirectCost_AvgPerVeh': pkg_cost}
    return regclass_yoy_costs_per_step_dict


def calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step_dict, fleet_averages_dict):
    for key in fleet_averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if age_id == 0:
            print(f'Calculating per vehicle direct costs for {vehicle}, MY {model_year}.')
            if alt == 0:
                model_year_cost = regclass_yoy_costs_per_step_dict[((alt, rc, ft), model_year, settings.cost_steps[0])]['DirectCost_AvgPerVeh']
            else:
                model_year_cost = regclass_yoy_costs_per_step_dict[((0, rc, ft), model_year, settings.cost_steps[0])]['DirectCost_AvgPerVeh']
                for cost_step in settings.cost_steps:
                    if model_year >= int(cost_step):
                        model_year_cost += regclass_yoy_costs_per_step_dict[((alt, rc, ft), model_year, cost_step)]['DirectCost_AvgPerVeh']
            fleet_averages_dict[key].update({'DirectCost_AvgPerVeh': model_year_cost})
    return fleet_averages_dict


def calc_direct_costs(fleet_totals_dict, fleet_averages_dict):
    print('\nCalculating total direct costs.\n')
    for key in fleet_totals_dict.keys():
        age_id = key[2]
        if age_id == 0:
            cost_per_veh = fleet_averages_dict[key]['DirectCost_AvgPerVeh']
            sales = fleet_totals_dict[key]['VPOP']
            fleet_totals_dict[key].update({'DirectCost': cost_per_veh * sales})
    return fleet_totals_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)

    regclass_yoy_costs_per_step_dict = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)
    fleet_averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step_dict, fleet_averages_dict)
    fleet_totals_dict = calc_direct_costs(fleet_totals_dict, fleet_averages_dict)

    # save dicts to csv
    save_dict_to_csv(regclass_yoy_costs_per_step_dict, settings.path_project / 'test/regclass_direct_costs_by_year_by_step', 'vehicle', 'modelYearID', 'cost_step')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')


# """
# direct_cost.py
#
# Contains the DirectCost class.
#
# """
#
# import pandas as pd
#
#
# class DirectCost:
#     """
#
#     The DirectCost class brings together the various elements: package costs; seed volumes; and, vehicle populations (specifically vehicle sales_df).
#
#     :param _veh: A tuple representing the given vehicle.
#     :param step: The given implementation step (e.g., the CTI proposal called for new standards in 2027 and then a second set of new standards in 2030; these would be two separate implementation steps.
#     :param costs_df: A DataFrame containing the individual tech costs for all vehicles and for each implementation step.
#     :param seedvol_df: A DataFrame containing the learning-related seed volumes for all vehicles.
#     :param sales_df: A DataFrame containing the sales for all vehicles.
#     :param tech_apply_learning_dict: A dictionary of individual technologies by fuelTypeID that make up the package of technologies on vehicles of that fuelTypeID.
#     """
#     def __init__(self, _veh, step, costs_df, seedvol_df, sales_df):
#         self._veh = _veh
#         self.step = step
#         self.costs_df = costs_df
#         self.seedvol_df = seedvol_df
#         self.sales_df = sales_df
#         self.tech_apply_learning_common = ['EngineHardware', 'CDA']
#         self.tech_apply_learning_dict = {1: self.tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
#                                          2: self.tech_apply_learning_common + ['CDPF', 'DOC', 'SCR', 'HCdosing', 'Canning', 'ClosedCrankcase'],
#                                          3: self.tech_apply_learning_common + ['Aftertreatment'],
#                                          5: self.tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
#                                          9: '',
#                                          }
#
#     def __repr__(self):
#         return f'{self.__class__.__name__}: Vehicle {self._veh}, Step {self.step}'
#
#     def package_of_techs_on_vehicle(self):
#         """
#
#         :return: A DataFrame of the techs on the given vehicle in the given implementation step.
#         """
#         techs_on_veh = self.costs_df.loc[self.costs_df['alt_rc_ft'] == self._veh, ['TechPackageDescription', self.step]]
#         techs_on_veh = techs_on_veh.set_index('TechPackageDescription')
#         return techs_on_veh
#
#     def cost_of_package_on_vehicle(self):
#         """
#
#         :return: A float of the summation of tech costs into a package cost for the given vehicle in the given implementation step.
#         """
#         pkg_cost_on_veh = 0
#         tech_apply_learning = self.tech_apply_learning_dict[self._veh[2]]
#         for tech in tech_apply_learning:
#             pkg_cost_on_veh += self.package_of_techs_on_vehicle().at[tech, self.step]
#         return pkg_cost_on_veh
#
#     def seedvol_factor_regclass(self):
#         """
#
#         :return:  A single seed volume factor for use in calculating learning effects for the given vehicle in the given implementation step.
#         """
#         _pkg_seedvol_df = pd.DataFrame(self.seedvol_df.loc[self.seedvol_df['alt_rc_ft'] == self._veh, 'SeedVolumeFactor'])
#         _pkg_seedvol_df.reset_index(drop=True, inplace=True)
#         _pkg_seedvol = _pkg_seedvol_df['SeedVolumeFactor'][0]
#         return _pkg_seedvol
#
#     def vehicle_sales_for_step(self):
#         """
#
#         :return: A DataFrame that provides the sales_df for the given vehicle in the years following the given implementation step.
#         """
#         veh_sales_for_step = pd.DataFrame(self.sales_df.loc[(self.sales_df['alt_rc_ft'] == self._veh) &
#                                                             (self.sales_df['modelYearID'] >= pd.to_numeric(self.step)) &
#                                                             (self.sales_df['ageID'] == 0), :])
#         return veh_sales_for_step
#
#     def pkg_cost_regclass_withlearning(self, _learning_rate):
#         """
#
#         :param _learning_rate: The learning rate entered in the BCA inputs sheet.
#         :return: A DataFrame of learned, year-over-year direct manufacturer package costs for the given vehicle in the given implementation step.
#         """
#         df = self.vehicle_sales_for_step().copy()
#         df.reset_index(drop=True, inplace=True)
#         # get VPOP at age0 for use in learning calc later
#         vpop_age0 = pd.Series(df['VPOP'])[0]
#         # insert some new columns, set to zero or empty string, then calc desired results
#         new_metric_numeric = [f'Sales_RegClass-FuelType_Cumulative_{self.step}', 'SeedVolumeFactor',
#                               f'DirectCost_AvgPerVeh_{self.step}']
#         for metric in new_metric_numeric:
#             df.insert(len(df.columns), metric, 0)
#         # now calculate results for these new metrics
#         df[f'Sales_RegClass-FuelType_Cumulative_{self.step}'] = df['VPOP'].cumsum()
#         df['SeedVolumeFactor'] = self.seedvol_factor_regclass()
#         df[f'DirectCost_AvgPerVeh_{self.step}'] = self.cost_of_package_on_vehicle() \
#                                                   * (((df[f'Sales_RegClass-FuelType_Cumulative_{self.step}']
#                                                        + (vpop_age0 * self.seedvol_factor_regclass()))
#                                                       / (vpop_age0 + (vpop_age0 * self.seedvol_factor_regclass()))) ** _learning_rate)
#         return df
