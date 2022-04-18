import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Deflators:
    """

    The Deflators class reads the GDP Implicit Price Deflators file and generates factors for use in adjusting monetized
    values to a consistent cost basis.

    Note:
         This class assumes a file structured like those published by the Bureau of Economic Analysis.

    """
    def __init__(self):
        self._dict = dict()
        self.deflators_and_adj_factors = pd.DataFrame()

    def init_from_file(self, filepath, general_inputs):
        """

        Parameters:
            filepath: Path to the specified file.
            general_inputs: The GeneralInputs class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=4, reset_index=True)

        df = self.deflator_df(df, 'Unnamed: 1', 'Gross domestic product')

        df = self.calc_adjustment_factors(general_inputs, df)

        key = df['yearID']
        df.set_index(key, inplace=True)

        self.deflators_and_adj_factors = df.copy()

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    @staticmethod
    def deflator_df(df, id_col, id_value):
        """

        Parameters:
            df: DataFrame; price deflator data.\n
            id_col: String; the column name where id data can be found.\n
            id_value: the value within id_col to return.
        Returns:
            A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed
            from the 'full name' column entries.

        """
        df_return = df.copy()
        df_return = pd.DataFrame(df_return.loc[df_return[id_col].str.endswith(f'{id_value}'), :]).reset_index(drop=True)
        df_return.replace({id_col: f': {id_value}'}, regex=True, inplace=True)

        df_return = pd.melt(df_return,
                            id_vars=[id_col],
                            value_vars=[col for col in df_return.columns if '20' in col],
                            var_name='yearID',
                            value_name='price_deflator')

        df_return['yearID'] = df_return['yearID'].astype(int)
        df_return['price_deflator'] = df_return['price_deflator'].astype(float)

        return df_return

    @staticmethod
    def calc_adjustment_factors(general_inputs, df):
        """

        Parameters:
            df: DataFrame; price deflator data.

        Returns:
            A dictionary of deflators and adjustment_factors to apply to monetized values to put them all on a consistent dollar basis.

        """
        dollar_basis_analysis = int(general_inputs.get_attribute_value('dollar_basis_analysis'))
        basis_factor_df = pd.DataFrame(df.loc[df['yearID'] == dollar_basis_analysis, 'price_deflator']).reset_index(drop=True)
        basis_factor = basis_factor_df.at[0, 'price_deflator']

        df_return = df.copy()
        df_return.insert(len(df_return.columns),
                         'adjustment_factor',
                         basis_factor / df_return['price_deflator'])

        return df_return

    def convert_dollars_to_analysis_basis(self, general_inputs, df, *args):
        """
        This function converts dollars into a consistent dollar basis as set via the General Inputs file.

        Parameters:
            df: DataFrame; contains the monetized values and their associated input cost basis.\n
            args: String(s); the attributes within the passed df to be adjusted into 'dollar_basis' dollars.

        Returns:
            The passed DataFrame will all args adjusted into dollar_basis dollars.

        """
        dollar_basis_analysis = int(general_inputs.get_attribute_value('dollar_basis_analysis'))
        dollar_years = pd.Series(pd.DataFrame(df.loc[df['DollarBasis'] > 1])['DollarBasis'].unique())
        for year in dollar_years:
            for arg in args:
                df.loc[df['DollarBasis'] == year, arg] = df[arg] * self._dict[year]['adjustment_factor']
            df.loc[df['DollarBasis'] == year, 'DollarBasis'] = dollar_basis_analysis

        return df
