"""
group_metrics.py

Contains the GroupMetrics class.

"""


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
            df_cumsum.rename(columns={metric: f'{metric}_CumSum'}, inplace=True)
        return df_cumsum


if __name__ == '__main__':
    """
    This tests the GroupMetrics class to ensure that things are working properly.
    If run as a script (python -m project_code.group_metrics) the created DataFrames should show values of
    400, 800, 1200
    100, 200, 300
    400, 1200, 2400.

    """
    import pandas as pd

    df = pd.DataFrame({'optionID': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                       'modelYearID': [2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028, 2029, 2029, 2029, 2029,],
                       'regClassID': [46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47,],
                       'fuelTypeID': [1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2,],
                       'metric': [100, 100, 100, 100, 200, 200, 200, 200, 300, 300, 300, 300,]})
    row_header = ['optionID', 'modelYearID']
    df_sum = GroupMetrics(df, row_header).group_sum(['metric']) # modelYearID=2027,2028,2029; metric=400,800,1200
    print(df_sum)
    df_mean = GroupMetrics(df, row_header).group_mean(['metric']) # modelYearID=2027,2028,2029; metric=100,200,300
    print(df_mean)
    row_header = ['optionID']
    df_cumsum = df_sum.join(GroupMetrics(df_sum, row_header).group_cumsum(['metric'])) # modelYearID=2027,2028,2029; metric_sum=400,1200,2400
    print(df_cumsum)
