

def calc_deltas(settings, dict_for_deltas):
    """This function calculates deltas for action alternatives relative to the no action alternative set via the General Inputs.

    Args:
        settings: The SetInputs class.
        dict_for_deltas: The dictionary containing values for calculating deltas.

    Returns: An updated dictionary containing deltas relative to the no_action_alt. OptionIDs for the deltas will be the alt_id followed by the no_action_alt.
        For example, deltas for optionID=1 relative to optionID=0 would have optionID=10. OptionNames will also show as 'OptionID=1_name minus OptionID=0_name'.

    """
    no_action_name = settings.options_dict[settings.no_action_alt]['OptionName']
    update_dict = dict()
    for key in dict_for_deltas.keys():
        vehicle, model_year, age_id, discount_rate = key[0], key[1], key[2], key[3]
        alt, st, rc, ft = vehicle
        print(f'Calculating deltas for {vehicle}, MY {model_year}, age {age_id}, DR {discount_rate}')
        id_args = [k for k, v in dict_for_deltas[key].items() if 'ID' in k or 'Name' in k]
        args_to_delta = [k for k, v in dict_for_deltas[key].items() if k not in id_args]
        if alt != settings.no_action_alt:
            action_name = settings.options_dict[alt]['OptionName']
            delta_name = f'{action_name}_minus_{no_action_name}'
            delta_alt = f'{alt}{settings.no_action_alt}'
            delta_alt = int(delta_alt)
            delta_dict = dict()
            for arg in args_to_delta:
                arg_value = dict_for_deltas[key][arg] - dict_for_deltas[((settings.no_action_alt, st, rc, ft), model_year, age_id, discount_rate)][arg]
                delta_dict.update({'OptionName': delta_name, arg: arg_value})
            for arg in id_args:
                arg_value = dict_for_deltas[key][arg]
                delta_dict.update({'OptionName': delta_name, arg: arg_value})
            delta_dict.update({'optionID': delta_alt})
            update_dict[((delta_alt, st, rc, ft), model_year, age_id, discount_rate)] = delta_dict
    dict_for_deltas.update(update_dict)
    return dict_for_deltas


def calc_deltas_weighted(settings, dict_for_deltas, weighted_arg):
    """This function calculates deltas for action alternatives relative to the passed no action alternative specifically for the weighted cost per mile dictionaries.
    Note that there is no age_id or discount rate in the key for the passed weighted dictionaries.

    Args:
        settings: The SetInputs class.
        dict_for_deltas: The dictionary containing values for calculating deltas.
        weighted_arg: The parameter for calculating deltas.

    Returns: An updated dictionary containing deltas relative to the no_action_alt. OptionIDs for the deltas will be the alt_id followed by the no_action_alt.
        For example, deltas for optionID=1 relative to optionID=0 would have optionID=10.

    """
    update_dict = dict()
    for key in dict_for_deltas.keys():
        vehicle, model_year = key[0], key[1]
        alt, st, rc, ft = vehicle
        print(f'Calculating weighted {weighted_arg} deltas for {vehicle}, MY {model_year}')
        id_args = [k for k, v in dict_for_deltas[key].items() if 'ID' in k or 'Name' in k]
        args_to_delta = [k for k, v in dict_for_deltas[key].items() if k not in id_args]
        if alt != settings.no_action_alt:
            delta_alt = f'{alt}{settings.no_action_alt}'
            delta_alt = int(delta_alt)
            delta_dict = dict()
            for arg in args_to_delta:
                arg_value = dict_for_deltas[key][arg] - dict_for_deltas[((settings.no_action_alt, st, rc, ft), model_year)][arg]
                delta_dict.update({arg: arg_value})
            for arg in id_args:
                arg_value = dict_for_deltas[key][arg]
                delta_dict.update({arg: arg_value})
            delta_dict.update({'optionID': delta_alt})
            update_dict[((delta_alt, st, rc, ft), model_year)] = delta_dict
    dict_for_deltas.update(update_dict)
    return dict_for_deltas


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs
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
    fleet_totals_dict_deltas = calc_deltas(settings, fleet_totals_dict)
    fleet_totals_dict_3_deltas = calc_deltas(settings, fleet_totals_dict_3)

    print(fleet_totals_dict_deltas)
