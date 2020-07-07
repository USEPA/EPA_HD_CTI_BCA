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
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year discounts to the start of the year
        (i.e., costs begin at time t=0) and end-year discounts to the end of the year (i.e., costs begin at time t=1).

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
        (present value) if that annual value were discounted at a given discount rate. Note that the exponent on the (1+rate) term is meant to represent the period. Given that the term is
        calculated here as the yearID less the year to which to discount, the +1 is included so that period 1 will not be calculated as 0 in the event that yearID=2027 & discount_to=2027.
        The discount_offset is then added to the result to reflect costs beginning at the start of the year or the end of the year.
        The equation used here is shown below.

        AC = PV * DR * (1+DR)^(period) / [(1+DR)^(period+Offset) - 1]

        where,\n
        AC = Annualized Cost\n
        PV = Present Value (here, the cumulative summary of discounted annual values)\n
        DR = Discount Rate\n
        CY = Calendar Year (yearID)\n
        period = the current CY - the year to which to discount values + discount_offset\n
        Offset = 1 for costs at the start of the year, 0 for cost at the end of the year

        :param metrics_cumsum: A list of cumulative summed metrics for which annualized values are to be calculated.
        :param year_min: Values will be annualized beginning in year_min.
        :param costs_start: The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year discounts to the start of the year (i.e., costs begin at time t=0) and end-year discounts to the end of the year (i.e., costs begin at time t=1).
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
