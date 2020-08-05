"""
emission_cost.py

Contains the EmissionCost class.

"""

import pandas as pd
from itertools import product


class EmissionCost:
    """
    The EmissionCost class calculates the monetized damages from pollutants.

    :param fleet_df: The fleet data that provides pollutant inventories.
    :param cost_df: The pollution damage costs in dollars per ton.
    """

    def __init__(self, fleet_df, cost_df):
        self.fleet_df = fleet_df
        self.cost_df = cost_df

    def calc_criteria_emission_costs_df(self):
        """

        :return: The DataFrame passed to the EmissionCost class after adding the criteria emission damage costs broken out in all ways.
        """
        df = self.fleet_df.copy()
        df_fuel = dict()
        fuel_ids = pd.Series(self.cost_df['fuelTypeID'].unique())
        for fuel_id in fuel_ids:
            df_fuel[fuel_id] = pd.DataFrame(df.loc[df['fuelTypeID'] == fuel_id, :])
        for dr, pollutant, source, mortality_est in product([0.03, 0.07], ['PM25', 'NOx'], ['onroad'], ['low', 'high']):
            key = pollutant + '_' + source + '_' + mortality_est + '_' + str(dr)
            cost_pollutant = pd.DataFrame(self.cost_df.loc[self.cost_df['Key'] == key],
                                          columns=['yearID', 'fuelTypeID', 'USDpUSton'])
            for fuel_id in fuel_ids:
                df_fuel[fuel_id] = df_fuel[fuel_id].merge(cost_pollutant, on=['yearID', 'fuelTypeID'], how='left')
                df_fuel[fuel_id]['USDpUSton'].fillna(method='ffill', inplace=True)
                new_metric_series = pd.Series(df_fuel[fuel_id][[f'{pollutant}_{source}', 'USDpUSton']].product(axis=1), name=key)
                df_fuel[fuel_id] = pd.concat([df_fuel[fuel_id], new_metric_series], axis=1)
                df_fuel[fuel_id].rename(columns={key: f'{pollutant}Cost_{source}_{mortality_est}_{dr}'}, inplace=True)
                df_fuel[fuel_id].rename(columns={'USDpUSton': f'{key}_USDpUSton'}, inplace=True)
        df_return = pd.DataFrame()
        for fuel_id in fuel_ids:
            df_return = pd.concat([df_return, df_fuel[fuel_id]], axis=0, ignore_index=True, sort=False)
        for dr, mortality_est in product([0.03, 0.07], ['low', 'high']):
            # for mortality_est in ['low', 'high']:
            cols = [col for col in df_return.columns if f'{mortality_est}_{dr}' in col and 'USDpUSton' not in col]
            df_return.insert(len(df_return.columns), f'CriteriaCost_{mortality_est}_{dr}', df_return[cols].sum(axis=1))
        return df_return
