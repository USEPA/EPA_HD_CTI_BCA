import pandas as pd


class EmissionCost:
    """The EmissionCost class calculates the monetized damages from pollutants.

    :param _fleet: The fleet data that provides pollutant inventories.
    :type _fleet: DataFrame
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
        for dr in [0.03, 0.07]:
            for pollutant in ['PM25', 'NOx']:
                for source in ['tailpipe']: # place 'upstream' here if upstream calcs are desired
                    for mortality_est in ['low', 'high']:
                        key = pollutant + '_' + source + '_' + mortality_est + '_' + str(dr)
                        cost_pollutant = pd.DataFrame(cost_df.loc[cost_df['Key'] == key],
                                                      columns=['yearID', 'USDpShortTon'])
                        df = df.merge(cost_pollutant, on='yearID', how='left')
                        df['USDpShortTon'].fillna(method='ffill', inplace=True)
                        new_metric_series = pd.Series(df[[pollutant + '_' + source, 'USDpShortTon']].product(axis=1), name=key)
                        df = pd.concat([df, new_metric_series], axis=1)
                        df.drop(columns='USDpShortTon', inplace=True)
        for dr in [0.03, 0.07]:
            for mortality_est in ['low', 'high']:
                cols = [col for col in df.columns if mortality_est + '_' + str(dr) in col]
                df.insert(len(df.columns), 'Criteria_Damage_' + mortality_est + '_' + str(dr), df[cols].sum(axis=1))
        return df

    def calc_criteria_damage_costs(self, cost_df):
        """

        :param cost_df: The pollution damage costs in dollars per ton.
        :type cost_df: DataFrame
        :return: The DataFrame passed to the EmissionCost class after adding the criteria emission damage costs.
        """
        df = self._fleet.copy()
        for dr in [0.03, 0.07]:
            for pollutant in ['PM25', 'NOx']:
                for source in ['tailpipe']: # place 'upstream' here if upstream calcs are desired
                    for mortality_est in ['low', 'average', 'high']:
                        key = pollutant + '_' + source + '_' + mortality_est + '_' + str(dr)
                        cost_pollutant = pd.DataFrame(cost_df.loc[cost_df['Key'] == key],
                                                      columns=['yearID', 'USDpShortTon'])
                        df = df.merge(cost_pollutant, on='yearID', how='left')
                        df['USDpShortTon'].fillna(method='ffill', inplace=True)
                        new_metric_series = pd.Series(df[[pollutant + '_' + source, 'USDpShortTon']].product(axis=1), name=key)
                        df = pd.concat([df, new_metric_series], axis=1)
                        df.drop(columns='USDpShortTon', inplace=True)
        df2 = self._fleet.copy()
        for dr in [0.03, 0.07]:
            for mortality_est in ['low', 'average', 'high']:
                cols = [col for col in df.columns if mortality_est + '_' + str(dr) in col]
                df2.insert(len(df2.columns), 'Criteria_Damage_' + mortality_est + '_' + str(dr), df[cols].sum(axis=1))
        return df2
