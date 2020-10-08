"""
emission_cost.py

Contains the EmissionCost class.

"""

import pandas as pd
from itertools import product


class EmissionCost:
    """
    
    The EmissionCost class calculates the monetized damages from pollutants.
    """

    def __init__(self, inventory_df, cost_per_ton_df):
        """
        
        :param inventory_df: The DataFrame that provides pollutant inventories.
        :param cost_per_ton_df: A DataFrame that provides the pollution damage costs in dollars per ton.
        """
        self.inventory_df = inventory_df
        self.cost_per_ton_df = cost_per_ton_df

    def fuel_ids(self):
        """

        :return: The fuelTypeIDs present in the cost/ton input file.
        """
        return pd.Series(self.cost_per_ton_df['fuelTypeID'].unique())

    def calc_emission_costs_df(self):
        """

        :return: The inventory_df DataFrame after adding the criteria emission damage costs broken out in all ways.
        """
        # df = self.inventory_df.copy()
        df_fuel = dict()
        # fuel_ids = pd.Series(self.cost_per_ton_df['fuelTypeID'].unique())
        for fuel_id in self.fuel_ids():
            df_fuel[fuel_id] = pd.DataFrame(self.inventory_df.loc[self.inventory_df['fuelTypeID'] == fuel_id, :])
        for dr, pollutant, source, mortality_est in product([0.03, 0.07], ['PM25', 'NOx'], ['onroad'], ['low', 'high']):
            key = f'{pollutant}_{source}_{mortality_est}_{str(dr)}'
            cost_pollutant = pd.DataFrame(self.cost_per_ton_df.loc[self.cost_per_ton_df['Key'] == key],
                                          columns=['yearID', 'fuelTypeID', 'USDpUSton'])
            for fuel_id in self.fuel_ids():
                print(f'EmissionCost: fuelTypeID {fuel_id}, Discount Rate {dr}, Pollutant {pollutant}, Source {source}, Mortality Estimate {mortality_est}')
                df_fuel[fuel_id] = df_fuel[fuel_id].merge(cost_pollutant, on=['yearID', 'fuelTypeID'], how='left')
                df_fuel[fuel_id]['USDpUSton'].fillna(method='ffill', inplace=True)
                new_metric_series = pd.Series(df_fuel[fuel_id][[f'{pollutant}_{source}', 'USDpUSton']].product(axis=1), name=key)
                df_fuel[fuel_id] = pd.concat([df_fuel[fuel_id], new_metric_series], axis=1)
                df_fuel[fuel_id].rename(columns={key: f'{pollutant}Cost_{source}_{mortality_est}_{dr}'}, inplace=True)
                df_fuel[fuel_id].rename(columns={'USDpUSton': f'{key}_USDpUSton'}, inplace=True)
        df_return = pd.DataFrame()
        for fuel_id in self.fuel_ids():
            df_return = pd.concat([df_return, df_fuel[fuel_id]], axis=0, ignore_index=True, sort=False)
        return df_return

    def calc_criteria_costs_df(self):
        for dr, mortality_est in product([0.03, 0.07], ['low', 'high']):
            cols = [col for col in self.inventory_df.columns if f'{mortality_est}_{dr}' in col and 'USDpUSton' not in col]
            self.inventory_df.insert(len(self.inventory_df.columns),
                                     f'CriteriaCost_{mortality_est}_{dr}',
                                     self.inventory_df[cols].sum(axis=1))
        return self.inventory_df
