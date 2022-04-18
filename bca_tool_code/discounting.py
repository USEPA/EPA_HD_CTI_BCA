import pandas as pd


def discount_values(settings, data_object):
    """
    The discount function determines metrics appropriate for discounting (those contained in dict_of_values) and does the discounting
    calculation to a given year and point within that year.

    Parameters:
        settings: Object; The SetInputs class object.\n
        data_object: Object; the fleet data object.

    Returns:
        The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at the same rate as the discount rate of the input stream of values.

    Note:
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs
        starting at time t=0 (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year
        costs are discounted).

    """
    print(f'\nDiscounting values...')

    # get cost attributes
    nested_dict = [n_dict for key, n_dict in data_object._dict.items()][0]
    all_costs = tuple([k for k, v in nested_dict.items() if 'Cost' in k])
    emission_cost_args_25 = tuple([item for item in all_costs if '_0.025' in item])
    emission_cost_args_3 = tuple([item for item in all_costs if '_0.03' in item])
    emission_cost_args_5 = tuple([item for item in all_costs if '_0.05' in item])
    emission_cost_args_7 = tuple([item for item in all_costs if '_0.07' in item])
    non_emission_cost_args = tuple([item for item in all_costs if '_0.0' not in item])

    costs_start = settings.general_inputs.get_attribute_value('costs_start')
    discount_to_year = pd.to_numeric(settings.general_inputs.get_attribute_value('discount_to_yearID'))
    discount_offset = 0
    if costs_start == 'end-year':
        discount_offset = 1
    else:
        print('costs_start entry in General Inputs file not set properly.')

    # Note: there is no need to discount values where the discount rate is 0

    for key in data_object.non0_dr_keys:
        vehicle, alt, model_year, age_id, rate = key
        year = model_year + age_id

        update_dict = dict()

        for arg in non_emission_cost_args:
            arg_value = data_object.get_attribute_value(key, arg)
            arg_value_discounted = arg_value / ((1 + rate) ** (year - discount_to_year + discount_offset))
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.025
        for arg in emission_cost_args_25:
            arg_value = data_object.get_attribute_value(key, arg)
            arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.03
        for arg in emission_cost_args_3:
            arg_value = data_object.get_attribute_value(key, arg)
            arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.05
        for arg in emission_cost_args_5:
            arg_value = data_object.get_attribute_value(key, arg)
            arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.07
        for arg in emission_cost_args_7:
            arg_value = data_object.get_attribute_value(key, arg)
            arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
            update_dict[arg] = arg_value_discounted

        data_object.update_dict(key, update_dict)


if __name__ == '__main__':
    import pandas as pd
    from bca_tool_code.tool_setup import SetInputs
    from bca_tool_code.discounting import discount_values

    settings = SetInputs()
    vehicle = (0)
    alt = 0
    my = 2027
    cost = 100
    growth = 0.5

    def create_dict_df(dr):
        _dict_df = pd.DataFrame({'vehicle': [(vehicle, alt, my, 0, dr), (vehicle, alt, my, 1, dr), (vehicle, alt, my, 2, dr),
                                            (vehicle, alt, my, 3, dr), (vehicle, alt, my, 4, dr), (vehicle, alt, my, 5, dr),
                                            (vehicle, alt, my, 6, dr), (vehicle, alt, my, 7, dr), (vehicle, alt, my, 8, dr),
                                            (vehicle, alt, my, 9, dr), (vehicle, alt, my, 10, dr)],
                                'Cost': [cost * (1 + growth) ** 0, cost * (1 + growth) ** 1, cost * (1 + growth) ** 2,
                                         cost * (1 + growth) ** 3,
                                         cost * (1 + growth) ** 4, cost * (1 + growth) ** 5, cost * (1 + growth) ** 6,
                                         cost * (1 + growth) ** 7,
                                         cost * (1 + growth) ** 8, cost * (1 + growth) ** 9, cost * (1 + growth) ** 10]})
        return _dict_df

    dr = 0
    data_df = create_dict_df(dr)
    data_df.set_index('vehicle', inplace=True)
    print('\n\nData\n', data_df)

    settings.costs_start = 'start-year'
    dr = 0.03
    settings.social_discount_rate_1, settings.social_discount_rate_2 = dr, dr
    data_df = create_dict_df(dr)
    data_df.set_index('vehicle', inplace=True)
    data_dict = data_df.to_dict('index')
    discounted_dict = discount_values(settings, data_dict, 'CAP', 'totals')
    discounted_df = pd.DataFrame(discounted_dict).transpose()

    print(f'\n\nDiscounted Data, {settings.costs_start}\n', discounted_df)

    settings.costs_start = 'end-year'
    data_dict = data_df.to_dict('index')
    discounted_dict = discount_values(settings, data_dict, 'CAP', 'totals')
    discounted_df = pd.DataFrame(discounted_dict).transpose()

    print(f'\n\nDiscounted Data, {settings.costs_start}\n', discounted_df)
