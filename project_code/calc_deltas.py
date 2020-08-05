"""
calc_deltas.py

Contains the CalcDeltas class.

"""


class CalcDeltas:
    """The CalcDelta class calculates the deltas (more stringent option minus option 0, as written)

    :param data: DataFrame being passed on which deltas are to be calculated.
    :param number_of_alts: The number of alternatives, or options, being considered in data.
    :param list_for_deltas: List of metrics for which to calculate deltas.
    """
    def __init__(self, data, number_of_alts, list_for_deltas):
        self.data = data
        self.number_of_alts = number_of_alts
        self.list_for_deltas = list_for_deltas

    def calc_delta_and_new_alt_id(self):
        """

        :return: A new DataFrame consisting of the passed DataFrame appended with deltas for each scenario in the passed data.
        """
        return_df = pd.DataFrame()
        alternative = dict()
        alternative[0] = self.data.loc[self.data['optionID'] == 0, :]
        alternative[0].reset_index(drop=True, inplace=True)
        alt0_name = alternative[0].at[0, 'OptionName']
        for alt in range(1, self.number_of_alts):
            alternative[alt] = self.data.loc[self.data['optionID'] == alt, :]
            alternative[alt].reset_index(drop=True, inplace=True)
            alt_name = alternative[alt].at[0, 'OptionName']
            alt_delta = int(alt * 10)
            alternative[alt_delta] = pd.DataFrame(alternative[alt].copy())
            alternative[alt_delta]['optionID'] = alt_delta
            alternative[alt_delta]['OptionName'] = str(f'{alt_name}_minus_{alt0_name}')
        for alt in range(1, self.number_of_alts):
            alt_delta = int(alt * 10)
            for item in self.list_for_deltas:
                alternative[alt_delta][item] = alternative[alt][item] - alternative[0][item]
            return_df = return_df.append(alternative[alt_delta], ignore_index=True, sort=False)
        return return_df

    def calc_delta_and_keep_alt_id(self):
        """

        :return: The passed DataFrame with metrics in list_for_deltas showing as reductions from baseline rather than the values contained in the passed DataFrame
        """
        return_df = pd.DataFrame(self.data.loc[self.data['optionID'] == 0, :])
        alternative = dict()
        alternative[0] = pd.DataFrame(self.data.loc[self.data['optionID'] == 0, :])
        alternative[0].reset_index(drop=True, inplace=True)
        for alt in range(1, self.number_of_alts):
            alternative[alt] = pd.DataFrame(self.data.loc[self.data['optionID'] == alt, :])
            alternative[alt].reset_index(drop=True, inplace=True)
            for item in self.list_for_deltas:
                alternative[alt][item] = alternative[0][item] - alternative[alt][item]
            return_df = return_df.append(alternative[alt], ignore_index=True, sort=False)
        for item in self.list_for_deltas:
            return_df.loc[return_df['optionID'] == 0, item] = 0
            # return_df.rename(columns={item: f'{item}_Reductions'}, inplace=True)
        return return_df


if __name__ == '__main__':
    """
    This tests the CalcDeltas class to ensure that things are working properly.
    If run as a script (python -m project_code.group_metrics) the created DataFrames should show metric values of -100 for optionID 10
    and then metric_reductions values of 0 for optionID 0 and 100 for optionID 1.

    """
    import pandas as pd

    df = pd.DataFrame({'optionID': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,],
                       'OptionName': ['Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1',],
                       'modelYearID': [2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028, 2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028,],
                       'regClassID': [46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47,],
                       'fuelTypeID': [1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2,],
                       'metric': [200, 200, 200, 200, 300, 300, 300, 300, 100, 100, 100, 100, 200, 200, 200, 200,]})
    number_alts = int(df['optionID'].max()) + 1
    df = pd.concat([df, CalcDeltas(df, number_alts, ['metric']).calc_delta_and_new_alt_id()], axis=0, ignore_index=True) # modelYearID=2027,2028,2029; metric=400,800,1200
    print(df)

    df.insert(df.columns.get_loc('metric') + 1, 'metric_reductions', df['metric'])
    df = CalcDeltas(df, number_alts, ['metric_reductions']).calc_delta_and_keep_alt_id()
    print(df)
