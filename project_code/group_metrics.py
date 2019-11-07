class GroupMetrics:
    """The GroupMetrics class conducts groupby methods to get results by yearID and more."""
    def __init__(self, data, row_header):
        self.data = data
        self.row_header = row_header

    def group_sum(self, metrics_sum):
        print('Doing groupby.sum')
        df_sum = self.data[self.row_header + metrics_sum].groupby(by=self.row_header, as_index=False).sum()
        return df_sum

    def group_mean(self, metrics_mean):
        df_mean = self.data[self.row_header + metrics_mean].groupby(by=self.row_header, as_index=False).mean()
        return df_mean

    def group_cumsum(self, metrics_cumsum):
        print('Doing groupby.cumsum')
        df_cumsum = self.data[self.row_header + metrics_cumsum].groupby(by=self.row_header, as_index=False).cumsum()
        for metric in metrics_cumsum:
            df_cumsum.rename(columns={metric: metric + '_CumSum'}, inplace=True)
        return df_cumsum

    def annualize_cumsum(self, metrics_cumsum, _year_min):
        for metric in metrics_cumsum:
            self.data.insert(len(self.data.columns), metric + '_Annualized', self.data[metric + '_CumSum'] / (self.data['yearID'] - _year_min + 1))
        return self.data
