"""
fuel_prices_aeo.py

Contains the GetFuelPrices class.

"""

import pandas as pd
from pathlib import PurePath


class GetFuelPrices:
    """
    The GetFuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.

    :param path_project: Well, this is the path of the project and the parent of the aeo directory.
    :param aeo_case: From the BCA inputs sheet - the AEO fuel case to use (a CSV of fuel prices must exist in the aeo directory).
    """
    def __init__(self, path_project, aeo_case):
        self.path_project = path_project
        self.aeo_case = aeo_case
        self.aeo = path_project.joinpath('aeo')
        self.fuel_price_metrics = ['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax']

    def get_fuel_prices(self):
        """

        :return: A fuel_prices DataFrame.
        """
        fuel_prices_file = PurePath(str(self.aeo) + '/Components_of_Selected_Petroleum_Product_Prices_' + self.aeo_case + '.csv')
        try:
            pd.read_csv(fuel_prices_file, skiprows=4)
            fuel_prices_full = pd.read_csv(fuel_prices_file, skiprows=4)
        except FileNotFoundError:
            print(f'File {fuel_prices_file} not found.')
        fuel_prices_full = fuel_prices_full[fuel_prices_full.columns[:-1]]
        fuel_prices_full.drop(labels=['full name', 'api key', 'units'], axis=1, inplace=True)
        fuel_df = fuel_prices_full.dropna(axis=0, how='any')
        diesel = fuel_df.loc[fuel_df['Unnamed: 0'].str.contains('diesel', case=False)]
        gasoline = fuel_df.loc[fuel_df['Unnamed: 0'].str.contains('gasoline', case=False)]
        fuel_df = gasoline.append(diesel)
        fuel_df.rename(columns={'Unnamed: 0': ''}, inplace=True)
        fuel_df.set_index(keys=[''], inplace=True)
        fuel_df = fuel_df.transpose()
        fuel_df.insert(0, 'yearID', fuel_df.index)
        fuel_df['yearID'] = pd.to_numeric(fuel_df['yearID'])
        fuel_df.reset_index(drop=True, inplace=True)
        for fuel in ['gasoline', 'diesel']:
            fuel_df.insert(len(fuel_df.columns), fuel + '_pretax', fuel_df[fuel + '_distribution'] + fuel_df[fuel + '_wholesale'])
        fuel_df = fuel_df[['yearID'] + self.fuel_price_metrics]
        return fuel_df
