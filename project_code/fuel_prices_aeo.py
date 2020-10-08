"""
fuel_prices_aeo.py

Contains the GetFuelPrices class.

"""

import pandas as pd
import sys


fuel_dict = {'Motor Gasoline': 1,
             'Diesel': 2}


class GetFuelPrices:
    """
    The GetFuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.

    :param path_project: Well, this is the path of the project and the parent of the aeo directory.
    :param aeo_case: From the BCA inputs sheet - the AEO fuel case to use (a CSV of fuel prices must exist in the aeo directory).
    """
    def __init__(self, path_project, aeo_case, *fuels):
        self.path_project = path_project
        self.aeo_case = aeo_case
        self.aeo = path_project / 'aeo'
        self.fuels = fuels
        self.fuel_price_metrics = ['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax']
        self.fuel_prices_file = self.aeo / f'Components_of_Selected_Petroleum_Product_Prices.csv'

    def __repr__(self):
        return f'\nGetFuelPrices: AEO {self.aeo_case}'

    def read_aeo_file(self):
        """

        :return:
        """
        try:
            pd.read_csv(self.fuel_prices_file, skiprows=4)
            print(f'Fuel prices file for AEO {self.aeo_case}.......FOUND.')
            fuel_prices_full = pd.read_csv(self.fuel_prices_file, skiprows=4)
            return fuel_prices_full
        except FileNotFoundError:
            print(f'Fuel prices file for AEO {self.aeo_case}......NOT FOUND in {self.aeo} folder.')
            sys.exit()

    def select_aeo_table_rows(self, df_source, row):
        """

        :param df_source:
        :param df_return:
        :param row:
        :return:
        """
        df_return = df_source.loc[df_source['full name'] == row['full name'], :]
        df_return = df_return.iloc[:, :-1]
        return df_return

    def row_dict(self, fuel):
        return_dict = dict()
        return_dict['retail_prices'] = {'full name': f'Price Components: {fuel}: End-User Price: {self.aeo_case}'}
        return_dict['distribution_costs'] = {'full name': f'Price Components: {fuel}: End-User Price: Distribution Costs: {self.aeo_case}'}
        return_dict['wholesale_price'] = {'full name': f'Price Components: {fuel}: End-User Price: Wholesale Price: {self.aeo_case}'}
        # return_dict['tax_allowance'] = {'full name': f'Price Components: {fuel}: End-User Price: Tax/Allowance: {self.aeo_case}'}
        return return_dict

    def melt_df(self, df, value_name):
        df = pd.melt(df, id_vars=['full name'], value_vars=[col for col in df.columns if '20' in col], var_name='yearID', value_name=value_name)
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
            fuel_prices_dict[fuel].insert(0, 'fuelTypeID', fuel_dict[fuel])
            fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict[fuel]], ignore_index=True, axis=0)
        fuel_prices_dict['CNG'] = fuel_prices_dict['Diesel'].copy()
        fuel_prices_dict['CNG']['fuelTypeID'] = 3
        fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict['CNG']], ignore_index=True, axis=0)
        fuel_prices_df = fuel_prices_df[['yearID', 'fuelTypeID', 'retail_fuel_price', 'pretax_fuel_price']]
        return fuel_prices_df


if __name__ == '__main__':
    from pathlib import Path

    path_project = Path.cwd()
    aeo_case = 'Reference case'
    fuel_prices_obj = GetFuelPrices(path_project, aeo_case, 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()
    fuel_prices.to_csv(path_project / f'dev/fuel_prices_{aeo_case}.csv', index=False)

    aeo_case = 'High oil price'
    fuel_prices_obj = GetFuelPrices(path_project, aeo_case, 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()
    fuel_prices.to_csv(path_project / f'dev/fuel_prices_{aeo_case}.csv', index=False)
