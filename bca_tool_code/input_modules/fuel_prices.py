import pandas as pd

from bca_tool_code.input_modules.deflators import Deflators
from bca_tool_code.input_modules.general_functions import read_input_file


class FuelPrices:
    """
    The FuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.
    The class also converts AEO fuel prices to dollar_basis_analysis dollars.

    Note:
         This class assumes a file structured like those published by the Bureau of Economic Analysis.

    """

    _data = dict()

    fuel_dict = {'Motor Gasoline': 1,
                 'Diesel': 2,
                 'CNG': 3,
                 }

    @staticmethod
    def init_from_file(filepath, general_inputs):

        FuelPrices._data.clear()

        df = read_input_file(filepath, skiprows=4, reset_index=True)

        df = FuelPrices.get_prices_from_file(general_inputs, df, 'full name', 'Motor Gasoline', 'Diesel')

        key = pd.Series(zip(df['yearID'], df['fuelTypeID']))
        df.set_index(key, inplace=True)

        FuelPrices._data = df.to_dict('index')

    @staticmethod
    def get_price(yearID, fuelTypeID, *series):
        """

        Parameters:
            yearID: Int; the calendar year.\n
            fuelTypeID: Int; 1, 2, or 3 for gasoline, diesel, or CNG.\n
            series: String; 'retail_fuel_price' and/or 'pretax_fuel_price

        Returns:
            A list of the price(s) sought expressed in dollar_basis_analysis dollars.

        """
        prices = [item for item in series]
        price_list = list()
        for price in prices:
            price_list.append(FuelPrices._data[yearID, fuelTypeID][price])
        return price_list

    @staticmethod
    def aeo_dollars(df):
        """

        Returns:
            An integer value representing the dollar basis of the AEO report.

        """
        return int(df.at[0, 'units'][0: 4])

    @staticmethod
    def select_aeo_table_rows(df_source, row, id_col):
        """

        Parameters:
            df_source: DataFrame; contains the AEO fuel prices.\n
            row: String; the specific row to select.

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
            fuel: String; the fuel (gasoline/diesel).

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
            value_name: String; the name of the melted values.

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

    @staticmethod
    def get_prices_from_file(general_inputs, df, id_col, *fuels):
        """

        Parameters:
            df: DataFrame; the fuel prices.\n

        Returns:
            A DataFrame of fuel prices for the given AEO case. Note that CNG prices are set equivalent to gasoline prices.

        """
        fuel_prices_dict = dict()
        fuel_prices_df = pd.DataFrame()

        for fuel in fuels:
            rows = FuelPrices.row_dict(general_inputs, id_col, fuel)

            retail_prices = FuelPrices.select_aeo_table_rows(df, rows['retail_prices'], id_col)
            fuel_prices_dict[fuel] = FuelPrices.melt_df(retail_prices, id_col, 'retail_fuel_price')

            distribution_costs = FuelPrices.select_aeo_table_rows(df, rows['distribution_costs'], id_col)
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(
                FuelPrices.melt_df(distribution_costs, id_col, 'distribution_costs'), on='yearID')

            wholesale_price = FuelPrices.select_aeo_table_rows(df, rows['wholesale_price'], id_col)
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(
                FuelPrices.melt_df(wholesale_price, id_col, 'wholesale_price'), on='yearID')

            fuel_prices_dict[fuel].insert(len(fuel_prices_dict[fuel].columns),
                                          'pretax_fuel_price',
                                          fuel_prices_dict[fuel]['distribution_costs']
                                          + fuel_prices_dict[fuel]['wholesale_price'])
            fuel_prices_dict[fuel].insert(0, 'fuelTypeID', FuelPrices.fuel_dict[fuel])
            fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict[fuel]], ignore_index=True, axis=0)

        fuel_prices_dict['CNG'] = fuel_prices_dict['Motor Gasoline'].copy()
        fuel_prices_dict['CNG']['fuelTypeID'] = FuelPrices.fuel_dict['CNG']
        fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict['CNG']], ignore_index=True, axis=0)
        fuel_prices_df = fuel_prices_df[['yearID', 'fuelTypeID', 'retail_fuel_price', 'pretax_fuel_price']]

        fuel_prices_df.insert(fuel_prices_df.columns.get_loc('yearID') + 1,
                              'DollarBasis',
                              FuelPrices.aeo_dollars(df))
        fuel_prices_df.insert(fuel_prices_df.columns.get_loc('yearID') + 1,
                              'AEO Case',
                              general_inputs.get_attribute_value('aeo_fuel_price_case'))

        fuel_prices_df = Deflators.convert_dollars_to_analysis_basis(general_inputs, fuel_prices_df,
                                                                     'retail_fuel_price', 'pretax_fuel_price')

        return fuel_prices_df
