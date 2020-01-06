import pandas as pd
from pathlib import Path, PurePath

fuel_price_metrics = ['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax']


class GetFuelPrices(object):
    """
    The GetFuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.

    :param _path_project: Well, this is the path of the project and the parent of the aeo directory.
    """
    def __init__(self, _path_project):
        self.path_project = _path_project
        self.aeo = _path_project.joinpath('aeo')

    def get_fuel_prices(self, _aeo_case):
        """

        :param _aeo_case: From the BCA inputs sheet - the AEO fuel case to use (a CSV of fuel prices must exist in the aeo directory).
        :param _metrics: A list of fuel prices to gather (i.e., gasoline, diesel, retail, pre-tax, etc.)
        :return: A fuel_prices DataFrame.
        """
        fuel_prices_file = PurePath(str(self.aeo) + '/Components_of_Selected_Petroleum_Product_Prices_' + _aeo_case + '.csv')
        fuel_prices_full = pd.read_csv(fuel_prices_file, skiprows=4)
        fuel_prices_full = fuel_prices_full[fuel_prices_full.columns[:-1]]
        fuel_prices_full.drop(labels=['full name', 'api key', 'units'], axis=1, inplace=True)
        _fuel_prices = fuel_prices_full.dropna(axis=0, how='any')
        diesel = _fuel_prices.loc[_fuel_prices['Unnamed: 0'].str.contains('diesel', case=False)]
        gasoline = _fuel_prices.loc[_fuel_prices['Unnamed: 0'].str.contains('gasoline', case=False)]
        _fuel_prices = gasoline.append(diesel)
        _fuel_prices.rename(columns={'Unnamed: 0': ''}, inplace=True)
        _fuel_prices.set_index(keys=[''], inplace=True)
        _fuel_prices = _fuel_prices.transpose()
        _fuel_prices.insert(0, 'yearID', _fuel_prices.index)
        _fuel_prices['yearID'] = pd.to_numeric(_fuel_prices['yearID'])
        _fuel_prices.reset_index(drop=True, inplace=True)
        for fuel in ['gasoline', 'diesel']:
            _fuel_prices.insert(len(_fuel_prices.columns), fuel + '_pretax', _fuel_prices[fuel + '_distribution'] + _fuel_prices[fuel + '_wholesale'])
        _fuel_prices = _fuel_prices[['yearID'] + fuel_price_metrics]
        return _fuel_prices
