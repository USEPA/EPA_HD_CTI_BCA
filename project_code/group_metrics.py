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

    def annualize_cumsum(self, metrics_cumsum, _year_min):
        """

        :param metrics_cumsum: A list of cumulative summed metrics for which annualized values are to be calculated.
        :param _year_min: Values will be annualized beginning in year_min.
        :return: The passed DataFrame with annualized values having been added.
        """
        for metric in metrics_cumsum:
            self.data.insert(len(self.data.columns), metric + '_Annualized', self.data[metric + '_CumSum'] / (self.data['yearID'] - _year_min + 1))
        return self.data
