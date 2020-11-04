"""
data_table.py
"""

import pandas as pd


class DataTable:
    """

    :param source_df: The source of data for which a data table is sought.
    :param args: The list of metrics for inclusion in the data table.
    """
    def __init__(self, source_df, *args):
        self.source_df = source_df
        self.args = args

    def data_table(self):
        """

        :return: A DataFrame containing the specific metrics passed.
        """
        data_table = pd.DataFrame(self.source_df[[arg for arg in self.args]])
        data_table.reset_index(drop=True, inplace=True)
        return data_table
