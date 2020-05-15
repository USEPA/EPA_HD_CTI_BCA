class DiscountValues:
    """The DiscountValues class takes a source DataFrame, a discount rate and a year to which to discount and discounts all values.

    :param source_df: A DataFrame containing monetized values to be discounted.
    :param metrics: The list of metrics (monetized values) to be discounted.
    :param discrate: The discount rate.
    :param discount_to_cy:  The year to which to discount values.
    :param costs_start: The point in the discount_to_cy to which to discount (start of year, mid-year, end of year)
    """
    def __init__(self, source_df, metrics, discrate, discount_to_cy, costs_start):
        self.source_df = source_df
        self.metrics = metrics
        self.discrate = discrate
        self.discount_to_cy = discount_to_cy
        self.costs_start = costs_start

    def discount(self):
        """
        The discount method takes the list of metrics to be discounted and does the discounting calculation to a given year and point within that year.
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year', 'mid-year' or 'end-year', where start-year discounts to the start of the year
        (i.e., costs begin at time t=0) and end-year discounts to the end of the year (i.e., costs begin at time t=1).

        :return: A DataFrame containing the passed list of monetized values after discounting.
        """
        destination_df = self.source_df.copy()
        for metric in self.metrics:
            if self.costs_start == 'start-year':
                discount_offset = 0
            if self.costs_start == 'mid-year':
                discount_offset = 0.5
            if self.costs_start == 'end-year':
                discount_offset = 1
            destination_df[metric] = self.source_df[metric] / ((1 + self.discrate) ** (self.source_df['yearID'] - self.discount_to_cy + discount_offset))
        destination_df.insert(0, 'DiscountRate', self.discrate)
        return destination_df
