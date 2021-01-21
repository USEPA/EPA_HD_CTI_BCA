"""
calc_deltas.py

Contains the CalcDeltas class.

"""
import pandas as pd


def calc_deltas(settings, dict_for_deltas, no_action_alt=0):
    no_action_name = settings.options_dict[no_action_alt]['OptionName']
    update_dict = dict()
    for key in dict_for_deltas.keys():
        vehicle, model_year, age_id, discount_rate = key[0], key[1], key[2], key[3]
        alt, st, rc, ft = vehicle
        print(f'Calculating deltas for {vehicle}, MY {model_year}, age {age_id}, DR {discount_rate}')
        id_args = [k for k, v in dict_for_deltas[key].items() if 'ID' in k or 'Name' in k]
        args_to_delta = [k for k, v in dict_for_deltas[key].items() if k not in id_args]
        if alt != no_action_alt:
            action_name = settings.options_dict[alt]['OptionName']
            delta_name = f'{action_name}_minus_{no_action_name}'
            delta_alt = f'{alt}{no_action_alt}'
            delta_alt = int(delta_alt)
            delta_dict = dict()
            for arg in args_to_delta:
                arg_value = dict_for_deltas[key][arg] - dict_for_deltas[((no_action_alt, st, rc, ft), model_year, age_id, discount_rate)][arg]
                delta_dict.update({'OptionName': delta_name, arg: arg_value})
                # delta_dict.update({'optionID': delta_alt, 'OptionName': delta_name, arg: arg_value})
            for arg in id_args:
                arg_value = dict_for_deltas[key][arg]
                delta_dict.update({'OptionName': delta_name, arg: arg_value})
                # delta_dict.update({'optionID': delta_alt, 'OptionName': delta_name, arg: arg_value})
            delta_dict.update({'optionID': delta_alt})
            update_dict[((delta_alt, st, rc, ft), model_year, age_id, discount_rate)] = delta_dict
    dict_for_deltas.update(update_dict)
    return dict_for_deltas



class CalcDeltas:
    """The CalcDelta class calculates the deltas (more stringent option minus option 0, as written)

    :param data: DataFrame being passed on which deltas or reductions are to be calculated.
    :param list_for_deltas: List of metrics for which to calculate deltas.
    """
    def __init__(self, data):
        self.data = data

    def calc_delta_and_new_alt_id(self, *args):
        """

        :param args: Metrics for which deltas or reductions are sought.
        :return: A new DataFrame consisting of the deltas for each scenario in the passed data.
        """
        return_df = pd.DataFrame()
        alternative = dict()
        alternative[0] = self.data.loc[self.data['optionID'] == 0, :]
        alternative[0].reset_index(drop=True, inplace=True)
        alt0_name = alternative[0].at[0, 'OptionName']
        alts = pd.Series(self.data['optionID'].unique())
        for idx, alt in enumerate(alts[1:]):
            alternative[alt] = self.data.loc[self.data['optionID'] == alt, :]
            alternative[alt].reset_index(drop=True, inplace=True)
            alt_name = alternative[alt].at[0, 'OptionName']
            alt_delta = int(alt * 10)
            alternative[alt_delta] = pd.DataFrame(alternative[alt].copy())
            alternative[alt_delta]['optionID'] = alt_delta
            alternative[alt_delta]['OptionName'] = str(f'{alt_name}_minus_{alt0_name}')
        for idx, alt in enumerate(alts[1:]):
            alt_delta = int(alt * 10)
            for arg in args:
                alternative[alt_delta][arg] = alternative[alt][arg] - alternative[0][arg]
            return_df = return_df.append(alternative[alt_delta], ignore_index=True, sort=False)
        return return_df

    def calc_delta_and_keep_alt_id(self, *args):
        """

        :param args: Metrics for which deltas or reductions are sought.
        :return: The passed DataFrame with metrics in list_for_deltas showing as reductions from baseline rather than the values contained in the passed DataFrame
        """
        return_df = pd.DataFrame(self.data.loc[self.data['optionID'] == 0, :])
        alternative = dict()
        alternative[0] = pd.DataFrame(self.data.loc[self.data['optionID'] == 0, :])
        alternative[0].reset_index(drop=True, inplace=True)
        alts = pd.Series(self.data['optionID'].unique())
        for idx, alt in enumerate(alts[1:]):
            alternative[alt] = pd.DataFrame(self.data.loc[self.data['optionID'] == alt, :])
            alternative[alt].reset_index(drop=True, inplace=True)
            for arg in args:
                alternative[alt][arg] = alternative[0][arg] - alternative[alt][arg]
            return_df = return_df.append(alternative[alt], ignore_index=True, sort=False)
        for arg in args:
            return_df.rename(columns={arg: f'{arg}_Reductions'}, inplace=True)
            return_df.loc[return_df['optionID'] == 0, f'{arg}_Reductions'] = 0
        return return_df


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
    from cti_bca_tool.discounting import discount_values
    from cti_bca_tool.general_functions import save_dict_to_csv, convert_dict_to_df

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

    # fleet_totals_dict_3 = create_fleet_totals_dict(project_fleet_df, rate=0.03)
    fleet_totals_dict_3 = discount_values(settings, fleet_totals_dict, 0.03)
    fleet_totals_dict_7 = discount_values(settings, fleet_totals_dict, 0.07)

    # now prep for deltas
    fleet_totals_df = convert_dict_to_df(fleet_totals_dict, 0, 'vehicle', 'modelYearID', 'ageID')

    # now calc deltas
    fleet_totals_dict_deltas = calc_deltas(settings, fleet_totals_dict, no_action_alt=0)
    fleet_totals_dict_3_deltas = calc_deltas(settings, fleet_totals_dict_3, no_action_alt=0)

    print(fleet_totals_dict_deltas)
