class DiscountValues:
    """The DiscountValues class takes a source DataFrame, a discount rate and a year to which to discount and discounts all values.

    :param _source_df: A DataFrame containing monetized values to be discounted.
    :param _discrate: The discount rate.
    :param _discount_to_cy:  The year to which to discount values.
    :param _discount_to: The point in the discount_to_cy to which to discount (start of year, mid-year, end of year)
    """
    def __init__(self, _source_df, _discrate, _discount_to_cy, _discount_to):
        self._source_df = _source_df
        self._discrate = _discrate
        self._discount_to_cy = _discount_to_cy
        self._discount_to = _discount_to

    def discount(self, _metrics):
        """
        The discount method takes the list of metrics to be discounted and does the discounting calculation to a given year and point within that year.
        The discount_to entry of the BCA_General_Inputs file should be set to 'start-year', 'mid-year' or 'end-year', where start-year discounts to the start of the year
        and end-year discounts to the end of the year.

        :param _metrics: The list of metrics (monetized values) to be discounted.
        :return: A DataFrame containing the passed list of monetized values after discounting.
        """
        destination_df = self._source_df.copy()
        for _metric in _metrics:
            if self._discount_to == 'start-year':
                discount_offset = 1
            if self._discount_to == 'mid-year':
                discount_offset = 0.5
            if self._discount_to == 'end-year':
                discount_offset = 0
            destination_df[_metric] = self._source_df[_metric] / ((1 + self._discrate) ** (self._source_df['yearID'] - self._discount_to_cy + discount_offset))
        destination_df.insert(0, 'DiscountRate', self._discrate)
        return destination_df
