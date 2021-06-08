

def calc_deltas(settings, dict_for_deltas):
    """This function calculates deltas for action alternatives relative to the no action alternative set via the General Inputs.

    Parameters:
        settings: The SetInputs class \n
        dict_for_deltas: The dictionary containing values for calculating deltas

    Returns:
        An updated dictionary containing deltas relative to the no_action_alt. OptionIDs for the deltas will be the alt_id followed by the no_action_alt. \n
        For example, deltas for optionID=1 relative to optionID=0 would have optionID=10. OptionNames will also show as 'OptionID=1_name minus OptionID=0_name'.

    """
    update_dict = dict()
    for key in dict_for_deltas.keys():
        vehicle, model_year, age_id, discount_rate = key[0], key[1], key[2], key[3]
        alt, st, rc, ft = vehicle
        print(f'Calculating deltas for {vehicle}, MY {model_year}, age {age_id}, DR {discount_rate}')
        args_to_delta = [k for k, v in dict_for_deltas[key].items()]
        if alt != settings.no_action_alt:
            delta_alt = f'{alt}{settings.no_action_alt}'
            delta_alt = int(delta_alt)
            delta_dict = dict()
            for arg in args_to_delta:
                arg_value = dict_for_deltas[key][arg] - dict_for_deltas[((settings.no_action_alt, st, rc, ft), model_year, age_id, discount_rate)][arg]
                delta_dict.update({arg: arg_value})
            update_dict[((delta_alt, st, rc, ft), model_year, age_id, discount_rate)] = delta_dict
    dict_for_deltas.update(update_dict)
    return dict_for_deltas


def calc_deltas_weighted(settings, dict_for_deltas, weighted_arg):
    """This function calculates deltas for action alternatives relative to the passed no action alternative specifically for the weighted cost per mile dictionaries.

    Parameters:
        settings: The SetInputs class \n
        dict_for_deltas: The dictionary containing values for calculating deltas \n
        weighted_arg: The parameter for calculating deltas

    Returns:
        An updated dictionary containing deltas relative to the no_action_alt. OptionIDs for the deltas will be the alt_id followed by the no_action_alt. \n
        For example, deltas for optionID=1 relative to optionID=0 would have optionID=10.

    Note:
        There is no age_id or discount rate in the key for the passed weighted dictionaries.

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
    from bca_tool_code.tool_setup import SetInputs as settings
    from bca_tool_code.general_functions import convert_dict_to_df

    data = {((0, 1, 1, 1), 2027, 0, 0): {'A': 100, 'B': 200},
            ((0, 1, 1, 1), 2027, 1, 0): {'A': 150, 'B': 250},
            ((1, 1, 1, 1), 2027, 0, 0): {'A': 50, 'B': 150},
            ((1, 1, 1, 1), 2027, 1, 0): {'A': 100, 'B': 200}}

    data = calc_deltas(settings, data)

    data_df = convert_dict_to_df(data, 'vehicle', 'model_year', 'age', 'discount_rate')

    print(data_df) # delta values should all be -50
