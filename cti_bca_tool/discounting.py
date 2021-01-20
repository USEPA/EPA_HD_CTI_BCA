"""
discounting.py

Contains the DiscountValues class.

"""
import copy


def discount_values(settings, dict_of_values, rate):
    discounted_dict = copy.deepcopy(dict_of_values) # deepcopy is required due to multilevel dictionary being passed
    if settings.costs_start == 'start-year': discount_offset = 0
    elif settings.costs_start == 'end-year': discount_offset = 1
    discount_to_year = settings.discount_to_yearID

    for key in discounted_dict.keys():
        print(f'Discounting values for {key}')
        vehicle, model_year, age_id = key[0], key[1], key[2]
        year = model_year + age_id
        args = [k for k, v in discounted_dict[key].items() if 'Cost' in k]
        # args = [k for k, v in discounted_dict[key].items()]
        for arg in args:
            discounted_arg = discounted_dict[key][arg] / ((1 + rate) ** (year - discount_to_year + discount_offset))
            discounted_dict[key].update({'DiscountRate': rate, arg: discounted_arg})
    return discounted_dict


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
    print(fleet_totals_dict_3)