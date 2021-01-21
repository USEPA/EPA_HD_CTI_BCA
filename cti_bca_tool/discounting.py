"""
discounting.py

Contains the DiscountValues class.

"""
# TODO Do I need an annualization method?

def discount_values(settings, dict_of_values, *discount_rates):
    """
    The discount method takes the list of metrics to be discounted and does the discounting calculation to a given year and point within that year.
    The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs starting at time t=0
    (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year costs are discounted).

    Args:
        settings: The SetInputs class.
        dict_of_values: A dictionary of values to be discounted with keys consisting of vehicle, model_year, age_id and discount rate.
        *discount_rates: The discount rates (as floats and excluding 0%, a 3% discount rate would be entered as 0.03) to be used for discounting.

    Returns: The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at that rate.

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
                # rate_dict.update({'DiscountRate': discount_rate, arg: arg_value})
                rate_dict.update({arg: arg_value})
            for arg in id_args:
                arg_value = dict_of_values[key][arg]
                # rate_dict.update({'DiscountRate': discount_rate, arg: arg_value})
                rate_dict.update({arg: arg_value})
            update_dict[((vehicle), model_year, age_id, discount_rate)] = rate_dict
    dict_of_values.update(update_dict)
    return dict_of_values


class DiscountValues:
    """The DiscountValues class takes a source DataFrame, a discount rate and a year to which to discount and discounts all values.

    :param source_df: A DataFrame containing monetized values to be discounted.
    :param discount_to_cy:  The year to which to discount values.
    :param costs_start: The point in the discount_to_cy to which to discount (start of year, mid-year, end of year)
    :param args: The metrics (arguments, i.e., monetized values) to be discounted or annualized.
    """
    def __init__(self, source_df, discount_to_cy, costs_start, *args):
        self.source_df = source_df
        self.discount_to_cy = discount_to_cy
        self.costs_start = costs_start
        self.args = args

    def discount(self, discrate):
        """
        The discount method takes the list of metrics to be discounted and does the discounting calculation to a given year and point within that year.
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs starting at time t=0
        (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year costs are discounted).

        :return: A DataFrame containing the passed list of monetized values after discounting.
        """
        destination_df = self.source_df.copy()
        if self.costs_start == 'start-year':
            discount_offset = 0
        if self.costs_start == 'end-year':
            discount_offset = 1
        for arg in self.args:
            discounted_years = self.source_df['yearID'] - self.discount_to_cy + discount_offset
            destination_df[arg] = self.source_df[arg] / ((1 + discrate) ** discounted_years)
        destination_df.insert(0, 'DiscountRate', discrate)
        return destination_df

    def annualize(self):
        """

        See EPA Economic Guidelines (updated May 2014), Section 6.1.2, Equations 3 & 4.
        This method makes use of the CumSum which, in this case is a running present value, and then determines the annual value that equates to that CumSum
        (present value) if that annual value were discounted at a given discount rate. The Offset is included to reflect costs beginning at the start of the year (Offset=1) or the end of the year
        (Offset=0).
        The equation used here is shown below.

        AC = PV * DR * (1+DR)^(period) / [(1+DR)^(period+Offset) - 1]

        where,\n
        AC = Annualized Cost\n
        PV = Present Value (here, the cumulative summary of discounted annual values)\n
        DR = Discount Rate\n
        CY = Calendar Year (yearID)\n
        period = the current CY minus the year to which to discount values + a discount_offset value where discount_offset equals the costs_start input value\n
        Offset = 1 for costs at the start of the year, 0 for cost at the end of the year

        :return: The passed DataFrame with annualized values having been added.
        """
        if self.costs_start == 'start-year':
            discount_offset = 0
            annualized_offset = 1
        if self.costs_start == 'end-year':
            discount_offset = 1
            annualized_offset = 0
        for arg in self.args:
            self.source_df.insert(len(self.source_df.columns), f'{arg}_Annualized', 0)
            periods = self.source_df['yearID'] - self.discount_to_cy + discount_offset
            self.source_df.loc[self.source_df['DiscountRate'] != 0, [f'{arg}_Annualized']] = \
                self.source_df[f'{arg}_CumSum'] * self.source_df['DiscountRate'] * (1 + self.source_df['DiscountRate']) ** periods \
                / ((1 + self.source_df['DiscountRate']) ** (periods + annualized_offset) - 1)
        return self.source_df


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
    from cti_bca_tool.general_functions import save_dict_to_csv

    # create project fleet data structures, both a DataFrame and a dictionary of regclass based sales
    project_fleet_df = create_fleet_df(settings)

    # create a sales (by regclass) and fleet dictionaries
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(settings, project_fleet_df, 0)
    fleet_averages_dict = create_fleet_averages_dict(settings, project_fleet_df, 0)

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
