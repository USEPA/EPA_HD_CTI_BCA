import pandas as pd


def discount_values(settings, data_object):
    """

    The discount function determines metrics appropriate for discounting (those contained in data_object dictionary)
    and does the discounting calculation to a given year and point within that year.

    Parameters:
        settings: object; the SetInputs class object.\n
        data_object: object; the fleet data object.

    Returns:
        Updates the data_object dictionary with new key, value pairs where keys stipulate the discount rate and
        monetized values are discounted at the same rate as the discount rate of the input stream of values.

    Note:
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where
        start-year represents costs starting at time t=0 (i.e., first year costs are undiscounted), and end-year
        represents costs starting at time t=1 (i.e., first year costs are discounted).

    """
    print(f'\nDiscounting values...')

    # get cost attributes
    nested_dict = [n_dict for key, n_dict in data_object.results.items()][0]
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
    non0_dr_keys = [k for k, v in data_object.results.items() if v['DiscountRate'] != 0]
    for key in non0_dr_keys:
        vehicle_id, option_id, modelyear_id, age_id, rate = key
        year = modelyear_id + age_id

        update_dict = dict()

        for arg in non_emission_cost_args:
            arg_value = data_object.results[key][arg]
            arg_value_discounted = discount_value(arg_value, rate, year, discount_to_year, discount_offset)
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.025
        for arg in emission_cost_args_25:
            arg_value = data_object.results[key][arg]
            arg_value_discounted = discount_value(arg_value, emission_rate, year, discount_to_year, discount_offset)
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.03
        for arg in emission_cost_args_3:
            arg_value = data_object.results[key][arg]
            arg_value_discounted = discount_value(arg_value, emission_rate, year, discount_to_year, discount_offset)
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.05
        for arg in emission_cost_args_5:
            arg_value = data_object.results[key][arg]
            arg_value_discounted = discount_value(arg_value, emission_rate, year, discount_to_year, discount_offset)
            update_dict[arg] = arg_value_discounted

        emission_rate = 0.07
        for arg in emission_cost_args_7:
            arg_value = data_object.results[key][arg]
            arg_value_discounted = discount_value(arg_value, emission_rate, year, discount_to_year, discount_offset)
            update_dict[arg] = arg_value_discounted

        data_object.update_object_dict(key, update_dict)


def discount_value(arg_value, rate, year, discount_to, offset):
    """

    Parameters:
        arg_value: Numeric; the value to be discounted.\n
        rate: Numeric; the discount rate to use.\n
        year: int; the calendar year associated with arg_value.\n
        discount_to: int; the calendar year to which to discount the value.\n
        offset: int; 0 or 1 reflecting whether costs are assumed to occur at the start of the year or the end of the
        year.

    Returns:
        A single value representing arg_value discounted to the year discount_to at rate.

    """
    return arg_value / ((1 + rate) ** (year - discount_to + offset))


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

    class Data:
        _dict = dict()
        non0_dr_keys = list()

        def create_dict(self, dr):
            _dict_df = pd.DataFrame({'vehicle': [(vehicle, alt, my, 0, dr), (vehicle, alt, my, 1, dr), (vehicle, alt, my, 2, dr),
                                                (vehicle, alt, my, 3, dr), (vehicle, alt, my, 4, dr), (vehicle, alt, my, 5, dr),
                                                (vehicle, alt, my, 6, dr), (vehicle, alt, my, 7, dr), (vehicle, alt, my, 8, dr),
                                                (vehicle, alt, my, 9, dr), (vehicle, alt, my, 10, dr)],
                                    'Cost': [cost * (1 + growth) ** 0, cost * (1 + growth) ** 1, cost * (1 + growth) ** 2,
                                             cost * (1 + growth) ** 3,
                                             cost * (1 + growth) ** 4, cost * (1 + growth) ** 5, cost * (1 + growth) ** 6,
                                             cost * (1 + growth) ** 7,
                                             cost * (1 + growth) ** 8, cost * (1 + growth) ** 9, cost * (1 + growth) ** 10]})
            _dict_df.set_index('vehicle', drop=False, inplace=True)
            self._dict = _dict_df.to_dict('index')
            self.non0_dr_keys = tuple([k for k, v in self._dict.items()])

        def get_attribute_value(self, key, attribute_name):
            return self._dict[key][attribute_name]

        def update_dict(self, key, input_dict):
            for attribute_name, attribute_value in input_dict.items():
                self._dict[key][attribute_name] = attribute_value


    dr = 0
    data_object = Data()
    data_object.create_dict(dr)
    df = pd.DataFrame(data_object._dict).transpose()
    print('\n\nData\n', df)

    dr = 0.03
    data_object = Data()
    data_object.create_dict(dr)
    discount_values(settings, data_object)
    discounted_df = pd.DataFrame(data_object._dict).transpose()

    print(f'\n\nDiscounted Data\n', discounted_df)

