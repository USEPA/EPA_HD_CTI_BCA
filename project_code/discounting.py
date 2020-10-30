"""
discounting.py

Contains the DiscountValues class.

"""


class DiscountValues:
    """The DiscountValues class takes a source DataFrame, a discount rate and a year to which to discount and discounts all values.

    :param source_df: A DataFrame containing monetized values to be discounted.
    :param metrics: The list of metrics (monetized values) to be discounted or annualized.
    :param discount_to_cy:  The year to which to discount values.
    :param costs_start: The point in the discount_to_cy to which to discount (start of year, mid-year, end of year)
    """
    def __init__(self, source_df, metrics, discount_to_cy, costs_start):
        self.source_df = source_df
        self.metrics = metrics
        self.discount_to_cy = discount_to_cy
        self.costs_start = costs_start

    def discount(self, discrate):
        """
        The discount method takes the list of metrics to be discounted and does the discounting calculation to a given year and point within that year.
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs starting at time t=0
        (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year costs are discounted).

        :param discrate: The discount rate.
        :return: A DataFrame containing the passed list of monetized values after discounting.
        """
        destination_df = self.source_df.copy()
        if self.costs_start == 'start-year':
            discount_offset = 0
        if self.costs_start == 'end-year':
            discount_offset = 1
        for metric in self.metrics:
            discounted_years = self.source_df['yearID'] - self.discount_to_cy + discount_offset
            destination_df[metric] = self.source_df[metric] / ((1 + discrate) ** discounted_years)
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
        for metric in self.metrics:
            self.source_df.insert(len(self.source_df.columns), f'{metric}_Annualized', 0)
            periods = self.source_df['yearID'] - self.discount_to_cy + discount_offset
            self.source_df.loc[self.source_df['DiscountRate'] != 0, [f'{metric}_Annualized']] = \
                self.source_df[f'{metric}_CumSum'] * self.source_df['DiscountRate'] * (1 + self.source_df['DiscountRate']) ** periods \
                / ((1 + self.source_df['DiscountRate']) ** (periods + annualized_offset) - 1)
        return self.source_df


if __name__ == '__main__':
    """
    This tests the discounting and annualizing methods to ensure that things are working properly.
    If run as a script (python -m project_code.discounting) the annualized values in the two created DataFrames should be 100.
    
    """
    import pandas as pd
    from project_code.group_metrics import GroupMetrics

    df = pd.DataFrame({'yearID': [2027, 2028, 2029, 2030, 2031, 2032],
                       'cost': [100, 100, 100, 100, 100, 100]})
    df.insert(0, 'option', 0)
    discrate = 0.03
    discount_to_cy = 2027

    costs_start = 'start-year'
    df_startyear = DiscountValues(df, ['cost'], discount_to_cy, costs_start).discount(discrate)
    df_startyear = df_startyear.join(GroupMetrics(df_startyear, ['option']).group_cumsum(['cost']))
    DiscountValues(df_startyear, ['cost'], discount_to_cy, costs_start).annualize()
    print(f'\nIf costs occur at time t=0, or {costs_start}.\n')
    print(df_startyear)

    costs_start = 'end-year'
    df_endyear = DiscountValues(df, ['cost'], discount_to_cy, costs_start).discount(discrate)
    df_endyear = df_endyear.join(GroupMetrics(df_endyear, ['option']).group_cumsum(['cost']))
    DiscountValues(df_endyear, ['cost'], discount_to_cy, costs_start).annualize()
    print(f'\nIf costs occur at time t=1, or {costs_start}.\n')
    print(df_endyear)
