from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages


def discount_values(settings, dict_of_values, program, arg):
    """
    The discount function determines metrics appropriate for discounting (those contained in dict_of_values) and does the discounting
    calculation to a given year and point within that year.

    Parameters:
        settings: The SetInputs class.\n
        dict_of_values: Dictionary; provides values to be discounted with keys consisting of vehicle, model_year, age_id and discount rate.\n
        program: String; indicates what program is being passed.
        arg: String; indicates whether totals or averages are being discounted.

    Returns:
        The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at the same rate as the discount rate of the input stream of values.

    Note:
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs
        starting at time t=0 (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year
        costs are discounted).

    """
    print(f'\nDiscounting values for {program} {arg}...')
    if arg == 'totals': calcs = FleetTotals(dict_of_values)
    else: calcs = FleetAverages(dict_of_values)

    # get cost attributes
    d = [nested_dict for key, nested_dict in dict_of_values.items()][0]
    all_costs = [k for k, v in d.items() if 'Cost' in k]
    emission_cost_args_25 = [item for item in all_costs if '_0.025' in item]
    emission_cost_args_3 = [item for item in all_costs if '_0.03' in item]
    emission_cost_args_5 = [item for item in all_costs if '_0.05' in item]
    emission_cost_args_7 = [item for item in all_costs if '_0.07' in item]
    non_emission_cost_args = [item for item in all_costs if '_0.0' not in item]

    if settings.costs_start == 'start-year': discount_offset = 0
    elif settings.costs_start == 'end-year': discount_offset = 1
    discount_to_year = settings.discount_to_yearID

    for key in dict_of_values.keys():
        vehicle, alt, model_year, age_id, rate = key
        if rate == 0:
            pass # no need to discount undiscounted values with 0 percent discount rate
        else:
            year = model_year + age_id

            temp_dict = dict()

            for arg in non_emission_cost_args:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + rate) ** (year - discount_to_year + discount_offset))
                temp_dict[arg] = arg_value_discounted

            emission_rate = 0.025
            for arg in emission_cost_args_25:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                temp_dict[arg] = arg_value_discounted

            emission_rate = 0.03
            for arg in emission_cost_args_3:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                temp_dict[arg] = arg_value_discounted

            emission_rate = 0.05
            for arg in emission_cost_args_5:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                temp_dict[arg] = arg_value_discounted

            emission_rate = 0.07
            for arg in emission_cost_args_7:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                temp_dict[arg] = arg_value_discounted

            calcs.update_dict(key, temp_dict)

    return dict_of_values


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

    def create_data_df(dr):
        _data_df = pd.DataFrame({'vehicle': [(vehicle, alt, my, 0, dr), (vehicle, alt, my, 1, dr), (vehicle, alt, my, 2, dr),
                                            (vehicle, alt, my, 3, dr), (vehicle, alt, my, 4, dr), (vehicle, alt, my, 5, dr),
                                            (vehicle, alt, my, 6, dr), (vehicle, alt, my, 7, dr), (vehicle, alt, my, 8, dr),
                                            (vehicle, alt, my, 9, dr), (vehicle, alt, my, 10, dr)],
                                'Cost': [cost * (1 + growth) ** 0, cost * (1 + growth) ** 1, cost * (1 + growth) ** 2,
                                         cost * (1 + growth) ** 3,
                                         cost * (1 + growth) ** 4, cost * (1 + growth) ** 5, cost * (1 + growth) ** 6,
                                         cost * (1 + growth) ** 7,
                                         cost * (1 + growth) ** 8, cost * (1 + growth) ** 9, cost * (1 + growth) ** 10]})
        return _data_df

    dr = 0
    data_df = create_data_df(dr)
    data_df.set_index('vehicle', inplace=True)
    print('\n\nData\n', data_df)

    settings.costs_start = 'start-year'
    dr = 0.03
    settings.social_discount_rate_1, settings.social_discount_rate_2 = dr, dr
    data_df = create_data_df(dr)
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
