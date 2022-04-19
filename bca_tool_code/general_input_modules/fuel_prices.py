import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class FuelPrices:
    """

    The FuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a
    fuel_prices DataFrame for use in operating costs. The class also converts AEO fuel prices to dollar_basis_analysis
    dollars and provides methods to query contents.

    Note:
         This class assumes a file structured like those published by the Energy Information Administration in the
         Annual Energy Outlook (AEO).

    """
    def __init__(self):
        self._dict = dict()
        self.fuel_prices_in_analysis_dollars = pd.DataFrame()
        self.fuel_id_dict = {'Motor Gasoline': 1,
                             'Diesel': 2,
                             'CNG': 3,
                             }

    def init_from_file(self, filepath, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.\n
            general_inputs: object; the GeneralInputs class object.\n
            deflators: object; the Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=4, reset_index=True)

        df = self.get_prices_from_file(general_inputs, df, 'full name', 'Motor Gasoline', 'Diesel')

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'retail_fuel_price', 'pretax_fuel_price')

        key = pd.Series(zip(df['yearID'], df['fuelTypeID']))
        df.set_index(key, inplace=True)

        self.fuel_prices_in_analysis_dollars = df.copy()

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_price(self, yearID, fuelTypeID, *series):
        """

        Parameters:
            yearID: int; the calendar year.\n
            fuelTypeID: int; 1, 2, or 3 for gasoline, diesel, or CNG, respectively.\n
            series: str; 'retail_fuel_price' and/or 'pretax_fuel_price.

        Returns:
            A list of the price(s) sought expressed in dollar_basis_analysis dollars.

        """
        prices = [item for item in series]
        price_list = list()
        for price in prices:
            price_list.append(self._dict[yearID, fuelTypeID][price])
        return price_list

    @staticmethod
    def aeo_dollars(df):
        """

        Parameters:
            df: DataFrame; the AEO fuel prices as read from the CSV file.

        Returns:
            An integer value representing the dollar basis of the AEO report.

        """
        return int(df.at[0, 'units'][0: 4])

    @staticmethod
    def select_aeo_table_rows(df_source, row, id_col):
        """

        Parameters:
            df_source: DataFrame; contains the AEO fuel prices.\n
            row: str; the specific row to select.\n
            id_col: str; the name of the column from which to find data (e.g., 'full name').

        Returns:
            A DataFrame of the specific fuel price row.

        """
        df_return = df_source.loc[df_source[id_col] == row[id_col], :]
        df_return = df_return.iloc[:, :-1]

        return df_return

    @staticmethod
    def row_dict(general_inputs, id_col, fuel):
        """

        Parameters:
            general_inputs: object; the GeneralInputs class object.\n
            id_col: str; the name of the column from which to find data (e.g., 'full name').\n
            fuel: str; the fuel (e.g., gasoline or diesel).

        Returns:
            A dictionary of fuel prices.

        """
        return_dict = dict()
        price_case = general_inputs.get_attribute_value('aeo_fuel_price_case')
        return_dict['retail_prices'] = {id_col: f'Price Components: {fuel}: End-User Price: {price_case}'}
        return_dict['distribution_costs'] = {id_col: f'Price Components: {fuel}: End-User Price: Distribution Costs: {price_case}'}
        return_dict['wholesale_price'] = {id_col: f'Price Components: {fuel}: End-User Price: Wholesale Price: {price_case}'}

        return return_dict

    @staticmethod
    def melt_df(df, id_col, value_name):
        """

        Parameters:
            df: DataFrame; the fuel prices to melt.\n
            id_col: str; the name of the column from which to find data (e.g., 'full name').\n
            value_name: str; the name of the melted values.

        Returns:
            A DataFrame of melted value_name data by year.

        """
        df = pd.melt(df,
                     id_vars=[id_col],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='yearID',
                     value_name=value_name)
        df['yearID'] = df['yearID'].astype(int)
        df.drop(columns=[id_col], inplace=True)

        return df

    def get_prices_from_file(self, general_inputs, df, id_col, *fuels):
        """

        Parameters:
            general_inputs: object; the GeneralInputs class object.\n
            df: DataFrame; the fuel prices.\n
            id_col: str; the name of the column from which to find data (e.g., 'full name').\n
            fuels: str(s); the fuels to include in the returned DataFrame.

        Returns:
            A DataFrame of fuel prices for the given AEO case with fueltype_id data included. Note that CNG prices are
            set equivalent to gasoline prices.

        """
        fuel_prices_dict = dict()
        fuel_prices_df = pd.DataFrame()

        for fuel in fuels:
            rows = self.row_dict(general_inputs, id_col, fuel)

            retail_prices = self.select_aeo_table_rows(df, rows['retail_prices'], id_col)
            fuel_prices_dict[fuel] = self.melt_df(retail_prices, id_col, 'retail_fuel_price')

            distribution_costs = self.select_aeo_table_rows(df, rows['distribution_costs'], id_col)
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(
                self.melt_df(distribution_costs, id_col, 'distribution_costs'), on='yearID')

            wholesale_price = self.select_aeo_table_rows(df, rows['wholesale_price'], id_col)
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(
                self.melt_df(wholesale_price, id_col, 'wholesale_price'), on='yearID')

            fuel_prices_dict[fuel].insert(len(fuel_prices_dict[fuel].columns),
                                          'pretax_fuel_price',
                                          fuel_prices_dict[fuel]['distribution_costs']
                                          + fuel_prices_dict[fuel]['wholesale_price'])
            fuel_prices_dict[fuel].insert(0, 'fuelTypeID', self.fuel_id_dict[fuel])
            fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict[fuel]], ignore_index=True, axis=0)

        fuel_prices_dict['CNG'] = fuel_prices_dict['Motor Gasoline'].copy()
        fuel_prices_dict['CNG']['fuelTypeID'] = self.fuel_id_dict['CNG']
        fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict['CNG']], ignore_index=True, axis=0)
        fuel_prices_df = fuel_prices_df[['yearID', 'fuelTypeID', 'retail_fuel_price', 'pretax_fuel_price']]

        fuel_prices_df.insert(fuel_prices_df.columns.get_loc('yearID') + 1,
                              'DollarBasis',
                              self.aeo_dollars(df))
        fuel_prices_df.insert(fuel_prices_df.columns.get_loc('yearID') + 1,
                              'AEO Case',
                              general_inputs.get_attribute_value('aeo_fuel_price_case'))

        return fuel_prices_df
