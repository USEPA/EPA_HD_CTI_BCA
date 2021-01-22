import pandas as pd
from itertools import product


# create some dictionaries for storing data
scaled_markups_dict = dict()
project_markups_dict = dict()


def calc_project_markup_value(settings, vehicle, markup_factor, model_year):
    alt, rc, ft = vehicle
    scaled_markups_dict_id = ((vehicle), markup_factor, model_year)
    scaling_metric = settings.indirect_cost_scaling_metric
    if scaled_markups_dict_id in scaled_markups_dict:
        project_markup_value = scaled_markups_dict[scaled_markups_dict_id]
    else:
        input_markup_value, scaler, scaled_by = settings.markup_inputs_dict[(ft, markup_factor)]['Value'], \
                                                settings.markup_inputs_dict[(ft, markup_factor)]['Scaler'], \
                                                settings.markup_inputs_dict[(ft, markup_factor)]['Scaled_by']
        if scaler == 'Absolute':
            project_markup_value = \
                (settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)][f'{model_year}']
                 / settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)]['2024']) \
                * input_markup_value
        if scaler == 'Relative':
            project_markup_value = \
                (settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)][f'{model_year}']
                 / settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)][str(int(model_year) - 3)]) \
                * input_markup_value
        if scaler == 'None':
            project_markup_value = input_markup_value
        scaled_markups_dict[scaled_markups_dict_id] = project_markup_value
    return project_markup_value


def per_veh_project_markups(settings, vehicles):
    """
    This method is for use in testing to get an output CSV that shows the markups used within the project.
    :param settings:
    :param markup_factors:
    :param vehicles:
    :param scaling_dict:
    :param markups_dict:
    :return:
    """
    for vehicle, model_year in product(vehicles, settings.years):
        for markup_factor in settings.markup_factors:
            markup_value = calc_project_markup_value(settings, vehicle, markup_factor, model_year)
            if markup_factor == settings.markup_factors[0]:
                project_markups_dict[((vehicle), model_year)] = {markup_factor: markup_value}
            else:
                project_markups_dict[((vehicle), model_year)].update({markup_factor: markup_value})
    return project_markups_dict


def calc_per_veh_indirect_costs(settings, fleet_averages_dict):
    print('\nCalculating per vehicle indirect costs\n')

    for key in fleet_averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if age_id == 0:
            print(f'Calculating per vehicle direct costs for {vehicle}, MY {model_year}.')
            ic_sum = 0
            for markup_factor in settings.markup_factors:
                markup_value = calc_project_markup_value(settings, (alt, rc, ft), markup_factor, model_year)
                per_veh_direct_cost = fleet_averages_dict[key]['DirectCost_AvgPerVeh']
                fleet_averages_dict[key].update({f'{markup_factor}Cost_AvgPerVeh': markup_value * per_veh_direct_cost})
                ic_sum += markup_value * per_veh_direct_cost
            fleet_averages_dict[key].update({'IndirectCost_AvgPerVeh': ic_sum})
    return fleet_averages_dict


def calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict):
    print('\nCalculating total indirect costs.\n')
    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    markup_factors.append('Indirect')
    for key in fleet_totals_dict.keys():
        age = key[2]
        if age == 0:
            for markup_factor in markup_factors:
                cost_per_veh = fleet_averages_dict[key][f'{markup_factor}Cost_AvgPerVeh']
                sales = fleet_totals_dict[key]['VPOP']
                fleet_totals_dict[key].update({f'{markup_factor}Cost': cost_per_veh * sales})
    return fleet_totals_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    per_veh_markups_by_year_dict = per_veh_project_markups(settings, vehicles_rc)

    per_veh_markups_by_year_df = pd.DataFrame(per_veh_markups_by_year_dict)

    # create project fleet data structures, both a DataFrame and a dictionary of regclass based sales
    project_fleet_df = create_fleet_df(settings)

    # create a sales (by regclass) and fleet dictionaries
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    # calculate direct costs per reg class based on cumulative regclass sales (learning is applied to cumulative reg class sales)
    regclass_yoy_costs_per_step = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)

    # calculate total direct costs and then per vehicle costs (per sourcetype)
    fleet_averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step, fleet_averages_dict)
    fleet_totals_dict = calc_direct_costs(fleet_totals_dict, fleet_averages_dict)

    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)

    # save dicts to csv
    save_dict_to_csv(per_veh_markups_by_year_df, settings.path_project / 'test/per_veh_markups_by_year', 'vehicle', 'modelYearID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')



# """
# indirect_cost.py
#
# Contains the IndirectCost class and the IndirectCostScalers class.
#
# """
#
# import pandas as pd
#
#
# class IndirectCost:
#     """
#
#     The IndirectCost class takes a DataFrame of direct costs and applies markups as provided by the merge_markups_and_directcosts method
#     and provided in the markup_factors list.
#
#     :param directcosts_df: A DataFrame of all direct manufacturing costs, year-over-year for all vehicles and alternatives.
#     :param markups: A DataFrame of the indirect cost markup factors by fuelTypeID.
#     """
#     def __init__(self, directcosts_df, markups):
#         self.directcosts_df = directcosts_df
#         self.markups = markups
#
#     def markup_factors(self):
#         """
#
#         :return: A list of the markup factors included in the indirect cost input file (excluding "IndirectCost").
#         """
#         return [item for item in self.markups['Markup_Factor'].unique() if 'Indirect' not in item]
#
#     def markup_factors_with_scalers(self):
#         """
#
#         :return: A list of the markup factors that are to be scaled according to the BCA Inputs scale_indirect_costs_by entry.
#         """
#         df = pd.DataFrame(self.markups.loc[self.markups['Scaler'] == 'Y', 'Markup_Factor'])
#         return [item for item in df['Markup_Factor'].unique() if 'Indirect' not in item]
#
#     def get_markups(self, fueltype_markups):
#         """
#
#         :param fueltype_markups: A DataFrame of indirect cost markup factors for a specific fuel.
#         :return: The passed DataFrame with markup factors inserted.
#         """
#         for markup_factor in self.markup_factors():
#             temp = pd.DataFrame(fueltype_markups.loc[fueltype_markups['Markup_Factor'] == markup_factor])
#             temp.reset_index(drop=True, inplace=True)
#             self.directcosts_df.insert(len(self.directcosts_df.columns), markup_factor, temp.at[0, 'Value'])
#         return self.directcosts_df
#
#     def merge_markup_scalers(self, alt_rc_ft_scalers, *args):
#         """
#
#         :param alt_rc_ft_scalers: A DataFrame of markup scalars for the given optionID_regclass_fueltype vehicle.
#         :param args: The metrics on which to merge the scalars into the passed direct cost DataFrame.
#         :return: The passed DataFrame into which the markup scaling factors (for those markups with scaling factors) have been merged.
#         """
#         merge_metrics = [arg for arg in args]
#         for markup_factor in self.markup_factors_with_scalers():
#             temp = pd.DataFrame(alt_rc_ft_scalers.loc[alt_rc_ft_scalers['Markup_Factor'] == markup_factor])
#             self.directcosts_df = self.directcosts_df.merge(temp[['yearID', 'Value']], on=merge_metrics, how='left')
#             self.directcosts_df.rename(columns={'Value': f'{markup_factor}_scaler'}, inplace=True)
#         return self.directcosts_df
#
#     def indirect_cost_unscaled(self, markups_and_scalers):
#         """
#
#         :param markups_and_scalers: A DataFrame of indirect cost markup factors & scalers in the shape of the direct cost DataFrame.
#         :return: A DataFrame of indirect costs per vehicle and total costs for those indirect costs that do not scale with VMT.
#         """
#         temp = [item for item in self.markup_factors() if item not in self.markup_factors_with_scalers()]
#         for factor in temp:
#             self.directcosts_df.insert(len(self.directcosts_df.columns),
#                                        f'{factor}Cost_AvgPerVeh',
#                                        self.directcosts_df['DirectCost_AvgPerVeh'] * markups_and_scalers[factor])
#         return self.directcosts_df
#
#     def indirect_cost_scaled(self, merged_df, factor, vmt_share):
#         """
#
#         :param merged_df: A DataFrame of indirect cost markup factors & scalers in the shape of the direct cost DataFrame.
#         :param factor: A given indirect cost factor, e.g., warranty or R&D.
#         :param vmt_share: A factor established in the main inputs file to represent the percentage of warranty costs that scale with VMT (vs. age or other metric).
#         :return: A DataFrame of indirect costs per vehicle and total costs with VMT scalers applied.
#         """
#         self.directcosts_df.insert(len(self.directcosts_df.columns),
#                                    f'{factor}Cost_AvgPerVeh',
#                                    self.directcosts_df['DirectCost_AvgPerVeh']
#                                    * (merged_df[factor] * (1 - vmt_share) + merged_df[factor] * vmt_share * merged_df[f'{factor}_scaler']))
#         return self.directcosts_df
#
#     def indirect_cost_sum(self):
#         """
#
#         :return: A DataFrame of full tech costs with direct and indirect costs per vehicle and in total.
#         """
#         self.directcosts_df.insert(len(self.directcosts_df.columns),
#                                    'IndirectCost_AvgPerVeh',
#                                    self.directcosts_df[[f'{item}Cost_AvgPerVeh' for item in self.markup_factors()]].sum(axis=1))
#         return self.directcosts_df
#
#
# class IndirectCostScalers:
#     """
#     The IndirectCostScalers class calculates the scaling factors to be applied to indirect cost contributors. The scaling factors can be absolute
#     or relative to the prior scaling factor.
#
#     :param: input_df: A DataFrame of warranty or useful life miles and ages by optionID.
#     :param identifier: String; "Warranty" or "UsefulLife" expected.
#     :param period: String; "Miles" or "Ages" expected via input cell in the BCA_Inputs sheet contained in the inputs folder.
#     """
#
#     def __init__(self, input_df, identifier, period):
#         """
#
#         :param input_df: A DataFrame of warranty or useful life miles and ages by optionID.
#         :param identifier: String; "Warranty" or "UsefulLife" expected.
#         :param period: String; "Miles" or "Age" expected via input cell in the BCA_Inputs sheet contained in the inputs folder; this
#         specifies scaling by Miles or by Age.
#         """
#         self.input_df = input_df
#         self.identifier = identifier
#         self.period = period
#
#     def calc_scalers_absolute(self):
#         """
#
#         :return: DatFrame of scaling factors that scale on absolute terms.
#         """
#         scaling_inputs = pd.DataFrame(self.input_df.loc[self.input_df['period'] == self.period])
#         return_df = scaling_inputs.copy()
#         cols = [col for col in return_df.columns if '20' in col]
#         for col in cols[1:]:
#             return_df[col] = return_df[col] / return_df[cols[0]]
#         return_df[cols[0]] = 1.0
#         return_df.insert(1, 'Markup_Factor', self.identifier)
#         return return_df
#
#     def calc_scalers_relative(self):
#         """
#
#         :return: DatFrame of scaling factors that scale relative to the prior year.
#         """
#         scaling_inputs = pd.DataFrame(self.input_df.loc[self.input_df['period'] == self.period])
#         return_df = scaling_inputs.copy()
#         cols = [col for col in return_df.columns if '20' in col]
#         for col_number, col in enumerate(cols):
#             return_df[cols[col_number]] = return_df[cols[col_number]] / scaling_inputs[cols[col_number - 1]]
#         return_df[cols[0]] = 1.0
#         return_df.insert(1, 'Markup_Factor', self.identifier)
#         return return_df
