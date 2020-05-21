class GroupMetrics:
    """The GroupMetrics class conducts groupby methods to get results by yearID and more.

    :param data: A DataFrame of values to be grouped.
    :param row_header: The row headers on which to group the passed DataFrame.
    """

    def __init__(self, data, row_header):
        self.data = data
        self.row_header = row_header

    def group_sum(self, metrics_sum):
        """

        :param metrics_sum: A list of metrics to be grouped and summed.
        :return: A DataFrame of values grouped by the passed row header and summed.
        """
        # print('Doing groupby.sum')
        df_sum = self.data[self.row_header + metrics_sum].groupby(by=self.row_header, as_index=False).sum()
        return df_sum

    def group_mean(self, metrics_mean):
        """

        :param metrics_mean: A list of metrics to be grouped and averaged.
        :return: A DataFrame of values grouped by the passed row header and averaged.
        """
        df_mean = self.data[self.row_header + metrics_mean].groupby(by=self.row_header, as_index=False).mean()
        return df_mean

    def group_cumsum(self, metrics_cumsum):
        """

        :param metrics_cumsum: A list of metrics to be grouped and for which cumulative sums are to be calculated.
        :return: A DataFrame of values grouped by the passed row header and cumulative summed.
        """
        # print('Doing groupby.cumsum')
        df_cumsum = self.data[self.row_header + metrics_cumsum].groupby(by=self.row_header, as_index=False).cumsum()
        for metric in metrics_cumsum:
            df_cumsum.rename(columns={metric: metric + '_CumSum'}, inplace=True)
        return df_cumsum

    def annualize_cumsum(self, metrics_cumsum, year_min, costs_start):
        """

        See EPA Economic Guidelines (updated May 2014), Section 6.1.2, Equations 3 & 4.
        This method could fit under both discounting and grouping since it involves the CumSum which, in this case is a running present value, and then determining
        the annual value that equates to that CumSum (present value) if that annual value were discounted at a given discount rate. So, it could fit in either place.
        Note that the exponent on the (1+rate) term is meant to represent the period, so year 1 would be period 1, etc. Given that the term is calculated here
        as the yearID less the start year, the +1 is included so that period 1 will not be calculated as 0 (i.e., if period 1 is yearID=2027 & start_year=2027,
        the period would equate to 0 without the +1). The discount_offset is then added to the result to reflect costs beginning at the start of the year or the end
        of the year. The equation used here is shown below.

        AC = PV * DR * (1+DR)^(CY-InitialCY+1) / [(1+DR)^(CY-InitialCY+1+Discount_Offset) - 1]

        where,\n
        AC = Annualized Cost\n
        PV = Present Value (here, the cumulative summary of discounted annual values)\n
        DR = Discount Rate\n
        CY = Calendar Year (yearID)\n
        InitialCY = Implementation Year (yearID=2027 in CTI proposal)\n
        Discount_Offset = 0 for costs at the start of the year, 1 for cost at the end of the year

        :param metrics_cumsum: A list of cumulative summed metrics for which annualized values are to be calculated.
        :param year_min: Values will be annualized beginning in year_min.
        :param costs_start: The costs_start entry of the BCA_General_Inputs file should be set to 'start-year', 'mid-year' or 'end-year', where start-year discounts to the start of the year (i.e., costs begin at time t=0) and end-year discounts to the end of the year (i.e., costs begin at time t=1).
        :return: The passed DataFrame with annualized values having been added.
        """
        if costs_start == 'start-year':
            discount_offset = 0
        if costs_start == 'mid-year':
            discount_offset = 0.5
        if costs_start == 'end-year':
            discount_offset = 1
        for metric in metrics_cumsum:
            self.data.insert(len(self.data.columns), metric + '_Annualized', 0)
            self.data.loc[self.data['DiscountRate'] != 0, [metric + '_Annualized']] = \
                self.data[metric + '_CumSum'] * self.data['DiscountRate'] * (1 + self.data['DiscountRate']) ** (self.data['yearID'] - year_min + 1) \
                / ((1 + self.data['DiscountRate']) ** (self.data['yearID'] - year_min + 1 + discount_offset) - 1)
        return self.data
