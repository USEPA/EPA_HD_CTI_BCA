from bca_tool_code.fleet_dicts_cap import FleetTotalsCAP, FleetAveragesCAP
from bca_tool_code.fleet_dicts_ghg import FleetTotalsGHG, FleetAveragesGHG


def discount_values(settings, dict_of_values, program, arg):
    """The discount function determines metrics appropriate for discounting (those contained in dict_of_values) and does the discounting
    calculation to a given year and point within that year.

    Parameters:
        settings: The SetInputs class.\n
        dict_of_values: A dictionary of values to be discounted with keys consisting of vehicle, model_year, age_id and discount rate.\n
        program: A string indicating what program is being passed.
        arg: A string indicating whether totals or averages are being discounted.

    Returns:
        The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at their internally consistent discount rate.

    Note:
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs
        starting at time t=0 (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year
        costs are discounted).

    """
    print(f'\nDiscounting values for {program} {arg}...')

    if program == 'CAP':
        if arg == 'totals': calcs = FleetTotalsCAP(dict_of_values)
        else: calcs = FleetAveragesCAP(dict_of_values)
    else:
        if arg == 'totals': calcs = FleetTotalsGHG(dict_of_values)
        else: calcs = FleetAveragesGHG(dict_of_values)

    for key, value in dict_of_values.items():
        all_costs = [k for k, v in value.items() if 'Cost' in k]
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

            for arg in non_emission_cost_args:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + rate) ** (year - discount_to_year + discount_offset))
                calcs.update_dict(key, arg, arg_value_discounted)

            emission_rate = 0.025
            for arg in emission_cost_args_25:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                calcs.update_dict(key, arg, arg_value_discounted)

            emission_rate = 0.03
            for arg in emission_cost_args_3:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                calcs.update_dict(key, arg, arg_value_discounted)

            emission_rate = 0.05
            for arg in emission_cost_args_5:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                calcs.update_dict(key, arg, arg_value_discounted)

            emission_rate = 0.07
            for arg in emission_cost_args_7:
                arg_value = calcs.get_attribute_value(key, arg)
                arg_value_discounted = arg_value / ((1 + emission_rate) ** (year - discount_to_year + discount_offset))
                calcs.update_dict(key, arg, arg_value_discounted)

    return dict_of_values
