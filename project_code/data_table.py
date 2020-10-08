"""
data_table.py
"""

import pandas as pd


class DataTable:
    def __init__(self, source_df, *args):
        """

        :param source_df:
        :param args:
        """
        self.source_df = source_df
        self.args = args

    def data_table(self):
        """

        :return:
        """
        data_table = pd.DataFrame(self.source_df[[arg for arg in self.args]])
        data_table.reset_index(drop=True, inplace=True)
        return data_table
