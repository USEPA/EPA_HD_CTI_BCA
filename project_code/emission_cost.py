import pandas as pd


class EmissionCost:
    """
    The EmissionCost class calculates the monetized damages from pollutants.

    :param _fleet: The fleet data that provides pollutant inventories.
    """

    def __init__(self, _fleet):
        self._fleet = _fleet

    def calc_criteria_emission_costs_df(self, cost_df):
        """

        :param cost_df: The pollution damage costs in dollars per ton.
        :type cost_df: DataFrame
        :return: The DataFrame passed to the EmissionCost class after adding the criteria emission damage costs broken out in all ways.
        """
        df = self._fleet.copy()
        df_fuel = dict()
        fuel_ids = pd.Series(cost_df['fuelTypeID'].unique())
        for fuel_id in fuel_ids:
            df_fuel[fuel_id] = pd.DataFrame(df.loc[df['fuelTypeID'] == fuel_id, :])
        for dr in [0.03, 0.07]:
            for pollutant in ['PM25', 'NOx']:
                for source in ['onroad']: # place 'upstream' here if upstream calcs are desired
                    for mortality_est in ['low', 'high']:
                        key = pollutant + '_' + source + '_' + mortality_est + '_' + str(dr)
                        cost_pollutant = pd.DataFrame(cost_df.loc[cost_df['Key'] == key],
                                                      columns=['yearID', 'fuelTypeID', 'USDpUSton'])
                        for fuel_id in fuel_ids:
                            df_fuel[fuel_id] = df_fuel[fuel_id].merge(cost_pollutant, on=['yearID', 'fuelTypeID'], how='left')
                            df_fuel[fuel_id]['USDpUSton'].fillna(method='ffill', inplace=True)
                            new_metric_series = pd.Series(df_fuel[fuel_id][[pollutant + '_' + source, 'USDpUSton']].product(axis=1), name=key)
                            df_fuel[fuel_id] = pd.concat([df_fuel[fuel_id], new_metric_series], axis=1)
                            df_fuel[fuel_id].rename(columns={key: pollutant + 'Cost_' + source + '_' + mortality_est + '_' + str(dr)}, inplace=True)
                            df_fuel[fuel_id].rename(columns={'USDpUSton': key + '_USDpUSton'}, inplace=True)
        df_return = pd.DataFrame()
        for fuel_id in fuel_ids:
            df_return = pd.concat([df_return, df_fuel[fuel_id]], axis=0, ignore_index=True, sort=False)
        for dr in [0.03, 0.07]:
            for mortality_est in ['low', 'high']:
                cols = [col for col in df_return.columns if mortality_est + '_' + str(dr) in col]
                df_return.insert(len(df_return.columns), 'CriteriaCost_' + mortality_est + '_' + str(dr), df_return[cols].sum(axis=1))
        return df_return
