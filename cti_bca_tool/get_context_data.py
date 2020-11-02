"""
get_context_data.py

Contains the GetFuelPrices & GetDeflators classes.

"""

import pandas as pd
import sys


class GetFuelPrices:
    """
    The GetFuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.
    """
    def __init__(self, path_project, aeo_case, id_col, *fuels):
        """

        :param path_project: The path of the project (the 'working directory') and the parent of the aeo directory.
        :param aeo_case: From the BCA inputs sheet - the AEO fuel case to use (a CSV of fuel prices must exist in the aeo directory).
        :param id_col: The column name where id data can be found.
        :param fuels: Descriptor for gasoline and diesel fuels (e.g., Motor Gasoline, Diesel).
        """
        self.path_project = path_project
        self.aeo_case = aeo_case
        self.aeo = path_project / 'aeo'
        self.id_col = id_col
        self.fuels = fuels
        self.fuel_price_metrics = ['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax']
        self.fuel_prices_file = self.aeo / f'Components_of_Selected_Petroleum_Product_Prices.csv'
        self.fuel_dict = {'Motor Gasoline': 1,
                          'Diesel': 2,
                          'CNG': 3,
                          }

    def __repr__(self):
        return f'\nGetFuelPrices: AEO {self.aeo_case}'

    def read_aeo_file(self):
        """

        :return: A DataFrame of the fuel prices in the csv file, if found, contained in the aeo folder.
        """
        try:
            pd.read_csv(self.fuel_prices_file, skiprows=4)
            print(f'Fuel prices file for AEO {self.aeo_case}.......FOUND.')
            return pd.read_csv(self.fuel_prices_file, skiprows=4, error_bad_lines=False).dropna().reset_index(drop=True)
        except FileNotFoundError:
            print(f'Fuel prices file for AEO {self.aeo_case}......NOT FOUND in {self.aeo} folder.')
            sys.exit()

    def aeo_dollars(self):
        """

        :return: The dollar basis of the AEO report.
        """
        return int(self.read_aeo_file().at[0, 'units'][0: 4])

    def select_aeo_table_rows(self, df_source, row):
        """

        :param df_source: The DataFrame of AEO fuel prices.
        :param row: The specific row to select.
        :return: A DataFrame of the specific fuel price row.
        """
        df_return = df_source.loc[df_source[self.id_col] == row[self.id_col], :]
        df_return = df_return.iloc[:, :-1]
        return df_return

    def row_dict(self, fuel):
        """

        :param fuel: The fuel (gasoline/diesel).
        :return: A dictionary of fuel prices.
        """
        return_dict = dict()
        return_dict['retail_prices'] = {self.id_col: f'Price Components: {fuel}: End-User Price: {self.aeo_case}'}
        return_dict['distribution_costs'] = {self.id_col: f'Price Components: {fuel}: End-User Price: Distribution Costs: {self.aeo_case}'}
        return_dict['wholesale_price'] = {self.id_col: f'Price Components: {fuel}: End-User Price: Wholesale Price: {self.aeo_case}'}
        # return_dict['tax_allowance'] = {self.id_col: f'Price Components: {fuel}: End-User Price: Tax/Allowance: {self.aeo_case}'}
        return return_dict

    def melt_df(self, df, value_name):
        """

        :param df: The DataFrame of fuel prices to melt.
        :param value_name: The name of the melted values.
        :return: A DataFrame of melted value_name data by year.
        """
        df = pd.melt(df, id_vars=[self.id_col], value_vars=[col for col in df.columns if '20' in col], var_name='yearID', value_name=value_name)
        df['yearID'] = df['yearID'].astype(int)
        return df

    def get_prices(self):
        """

        :return: A DataFrame of fuel prices for the given AEO case.
        """
        prices_full = self.read_aeo_file()
        fuel_prices_dict = dict()
        fuel_prices_df = pd.DataFrame()
        for fuel in self.fuels:
            retail_prices = self.select_aeo_table_rows(prices_full, self.row_dict(fuel)['retail_prices'])
            fuel_prices_dict[fuel] = self.melt_df(retail_prices, 'retail_fuel_price')

            distribution_costs = self.select_aeo_table_rows(prices_full, self.row_dict(fuel)['distribution_costs'])
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(self.melt_df(distribution_costs, 'distribution_costs'), on='yearID')

            wholesale_price = self.select_aeo_table_rows(prices_full, self.row_dict(fuel)['wholesale_price'])
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(self.melt_df(wholesale_price, 'wholesale_price'), on='yearID')

            # tax_allowance = self.select_aeo_table_rows(prices_full, self.row_dict(fuel)['tax_allowance'])
            # fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(self.melt_df(tax_allowance, 'tax_allowance'), on='yearID')

            fuel_prices_dict[fuel].insert(len(fuel_prices_dict[fuel].columns),
                                          'pretax_fuel_price',
                                          fuel_prices_dict[fuel]['distribution_costs'] + fuel_prices_dict[fuel]['wholesale_price'])
            fuel_prices_dict[fuel].insert(0, 'fuelTypeID', self.fuel_dict[fuel])
            fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict[fuel]], ignore_index=True, axis=0)
        fuel_prices_dict['CNG'] = fuel_prices_dict['Motor Gasoline'].copy()
        fuel_prices_dict['CNG']['fuelTypeID'] = self.fuel_dict['CNG']
        fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict['CNG']], ignore_index=True, axis=0)
        fuel_prices_df = fuel_prices_df[['yearID', 'fuelTypeID', 'retail_fuel_price', 'pretax_fuel_price']]
        return fuel_prices_df


class GetDeflators:
    """
    The GetDeflators class returns the GDP Implicit Price Deflators for use in adjusting monetized values to a consistent cost basis.
    """
    def __init__(self, path_project, id_col, id_value, skiprows=4):
        """

        :param path_project: The path of the project and the parent of the aeo directory.
        :param id_col: The column name where id data can be found.
        :param id_value: The value within id_col to return.
        :param skiprows: The number of rows to skip when reading the file.
        """
        self.path_project = path_project
        self.id_col = id_col
        self.id_value = id_value
        self.bea = path_project / 'bea'
        self.skiprows = skiprows
        self.deflators_file = self.bea / 'Table_1.1.9_ImplicitPriceDeflators.csv'

    def __repr__(self):
        return f'GetDeflators: {self.id_value}'

    def read_table(self):
        """

        :return: A DataFrame of the raw GDP deflators file.
        """
        try:
            pd.read_csv(self.deflators_file, skiprows=4)
            print(f'BEA GDP deflators file.......FOUND.')
            return pd.read_csv(self.deflators_file, skiprows=self.skiprows, error_bad_lines=False).dropna()
        except FileNotFoundError:
            print(f'BEA GDP deflators file......NOT FOUND in {self.bea} folder.')
            sys.exit()

    def deflator_df(self):
        """

        :return: A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed from the 'full name' column entries.
        """
        df_return = pd.DataFrame(self.read_table())
        df_return = pd.DataFrame(df_return.loc[df_return[self.id_col].str.endswith(f'{self.id_value}'), :]).reset_index(drop=True)
        df_return.replace({self.id_col: f': {self.id_value}'}, {self.id_col: ''}, regex=True, inplace=True)
        return df_return

    def melt_df(self, value_name, drop_col=None):
        """

        :param value_name: The name for the resultant data column.
        :param drop_col: The name of any columns to be dropped after melt.
        :return: The melted DataFrame with a column of data named value_name.
        """
        deflator_df = self.deflator_df()
        melt_df = pd.melt(deflator_df, id_vars=[self.id_col], value_vars=[col for col in deflator_df.columns if '20' in col], var_name='yearID', value_name=value_name)
        melt_df['yearID'] = melt_df['yearID'].astype(int)
        if drop_col:
            melt_df.drop(columns=drop_col, inplace=True)
        return melt_df

    def calc_adjustment_factors(self, dollar_basis):
        """

        :param dollar_basis: The dollar basis for the analysis which is determined in-code using the AEO file.
        :return: A dictionary of deflators and adjustment_factors to apply to monetized values to put them all on a consistent dollar basis.
        """
        deflators = self.melt_df('price_deflator', self.id_col)
        deflators['price_deflator'] = deflators['price_deflator'].astype(float)
        basis_factor_df = pd.DataFrame(deflators.loc[deflators['yearID'] == dollar_basis, 'price_deflator']).reset_index(drop=True)
        basis_factor = basis_factor_df.at[0, 'price_deflator']
        deflators.insert(len(deflators.columns),
                         'adjustment_factor',
                         basis_factor / deflators['price_deflator'])
        deflators = deflators.set_index('yearID')
        deflators_dict = deflators.to_dict('index')
        return deflators_dict


if __name__ == '__main__':
    from pathlib import Path

    path_project = Path.cwd()
    path_dev = path_project / 'dev'
    path_dev.mkdir(exist_ok=True)

    aeo_case_1 = 'Reference case'
    fuel_prices_obj = GetFuelPrices(path_project, aeo_case_1, 'full name', 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()
    fuel_prices.to_csv(path_project / f'dev/fuel_prices_{aeo_case_1}.csv', index=False)

    aeo_case_2 = 'High oil price'
    fuel_prices_obj = GetFuelPrices(path_project, aeo_case_2, 'full name', 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()
    fuel_prices.to_csv(path_project / f'dev/fuel_prices_{aeo_case_2}.csv', index=False)

    deflators_obj = GetDeflators(path_project, 'Unnamed: 1', 'Gross domestic product')
    dollar_basis = 2017
    deflators = deflators_obj.calc_adjustment_factors(dollar_basis)
    deflators = pd.DataFrame(deflators)
    deflators.to_csv(path_project / f'dev/gdp_deflators.csv', index=False)

    print(f'\nfuel_prices_{aeo_case_1}.csv, fuel_prices_{aeo_case_2}.csv & gdp_deflators.csv (dollar basis = {dollar_basis}) have been saved to the {path_dev} folder.')
