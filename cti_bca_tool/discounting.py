import pandas as pd


def discount_values(settings, dict_of_values, *discount_rates):
    """The discount function determines metrics appropriate for discounted (those contained in dict_of_values) and does the discounting
    calculation to a given year and point within that year.

    Parameters:
        settings: The SetInputs class.\n
        dict_of_values: A dictionary of values to be discounted with keys consisting of vehicle, model_year, age_id and discount rate.\n
        discount_rates: The discount rates (as floats and excluding 0%, a 3% discount rate would be entered as 0.03) to be used for discounting.

    Returns:
        The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at that rate.

    Note:
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs
        starting at time t=0 (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year
        costs are discounted).

    """
    if settings.costs_start == 'start-year': discount_offset = 0
    elif settings.costs_start == 'end-year': discount_offset = 1
    discount_to_year = settings.discount_to_yearID
    update_dict = dict()
    for key in dict_of_values.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        print(f'Discounting values for {vehicle}, MY {model_year}, age {age_id}')
        year = model_year + age_id
        id_args = [k for k, v in dict_of_values[key].items() if 'ID' in k or 'Name' in k]
        non_emission_cost_args = [k for k, v in dict_of_values[key].items() if 'Cost' in k and '_0.0' not in k]
        for discount_rate in discount_rates:
            emission_cost_args = [k for k, v in dict_of_values[key].items() if str(discount_rate) in k]
            args_to_discount = non_emission_cost_args + emission_cost_args
            rate_dict = dict()
            for arg in args_to_discount:
                arg_value = dict_of_values[key][arg] / ((1 + discount_rate) ** (year - discount_to_year + discount_offset))
                rate_dict.update({arg: arg_value})
            for arg in id_args:
                arg_value = dict_of_values[key][arg]
                rate_dict.update({arg: arg_value})
            update_dict[((vehicle), model_year, age_id, discount_rate)] = rate_dict
    dict_of_values.update(update_dict)
    return dict_of_values


def annualize_values(settings, input_df):
    """This function determines the annual value that equates to a present value if that annual value were discounted at a given discount rate.
    See EPA Economic Guidelines (updated May 2014), Section 6.1.2, Equations 3 & 4.

    Parameters:
        settings: The SetInputs class.\n
        input_df: A DataFrame of annual values containing optionID, yearID, DiscountRate and Cost arguments.

    Returns:
        A DataFrame of the passed Cost arguments annualized by optionID in each of the passed yearIDs and at each discount rate.

    Note:
        This function makes use of a cumulative sum of annual discounted values. As such, the cumulative sums represent a present value
        through the given calendar year. The Offset is included to reflect costs beginning at the start of the year (Offset=1)
        or the end of the year (Offset=0).\n
        The equation used here is shown below.

        AC = PV * DR * (1+DR)^(period) / [(1+DR)^(period+Offset) - 1]

        where,\n
        AC = Annualized Cost\n
        PV = Present Value (here, the cumulative summary of discounted annual values)\n
        DR = Discount Rate\n
        CY = Calendar Year (yearID)\n
        period = the current CY minus the year to which to discount values + a discount_offset value where discount_offset equals the costs_start input value\n
        Offset = 1 for costs at the start of the year, 0 for cost at the end of the year

    """
    if settings.costs_start == 'start-year':
        discount_offset = 0
        annualized_offset = 1
    elif settings.costs_start == 'end-year': 
        discount_offset = 1
        annualized_offset = 0
    discount_to_year = settings.discount_to_yearID
    cost_args = [arg for arg in input_df.columns if 'Cost' in arg and 'PresentValue' not in arg]
    input_df.insert(input_df.columns.get_loc('DiscountRate') + 1, 'periods', input_df['yearID'] - discount_to_year + discount_offset)
    for cost_arg in cost_args:
        input_df.insert(len(input_df.columns),
                  f'{cost_arg}_Annualized',
                  input_df[f'{cost_arg}_PresentValue'] * input_df['DiscountRate'] * (1 + input_df['DiscountRate']) ** input_df['periods']
                  / ((1 + input_df['DiscountRate']) ** (input_df['periods'] + annualized_offset) - 1))
    return input_df


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs
    from cti_bca_tool.general_functions import save_dict_to_csv

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

    fleet_totals_dict = discount_values(settings, fleet_totals_dict, 0.03, 0.07)
    fleet_averages_dict = discount_values(settings, fleet_averages_dict, 0.03, 0.07)
    # save dicts to csv
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
