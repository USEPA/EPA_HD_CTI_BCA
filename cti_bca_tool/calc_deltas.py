"""
calc_deltas.py

Contains the CalcDeltas class.

"""
import pandas as pd


class CalcDeltas:
    """The CalcDelta class calculates the deltas (more stringent option minus option 0, as written)

    :param data: DataFrame being passed on which deltas or reductions are to be calculated.
    :param list_for_deltas: List of metrics for which to calculate deltas.
    """
    def __init__(self, data):
        self.data = data

    def calc_delta_and_new_alt_id(self, *args):
        """

        :param args: Metrics for which deltas or reductions are sought.
        :return: A new DataFrame consisting of the deltas for each scenario in the passed data.
        """
        return_df = pd.DataFrame()
        alternative = dict()
        alternative[0] = self.data.loc[self.data['optionID'] == 0, :]
        alternative[0].reset_index(drop=True, inplace=True)
        alt0_name = alternative[0].at[0, 'OptionName']
        alts = pd.Series(self.data['optionID'].unique())
        for alt in range(1, len(alts)):
            alternative[alt] = self.data.loc[self.data['optionID'] == alt, :]
            alternative[alt].reset_index(drop=True, inplace=True)
            alt_name = alternative[alt].at[0, 'OptionName']
            alt_delta = int(alt * 10)
            alternative[alt_delta] = pd.DataFrame(alternative[alt].copy())
            alternative[alt_delta]['optionID'] = alt_delta
            alternative[alt_delta]['OptionName'] = str(f'{alt_name}_minus_{alt0_name}')
        for alt in range(1, len(alts)):
            alt_delta = int(alt * 10)
            for arg in args:
                alternative[alt_delta][arg] = alternative[alt][arg] - alternative[0][arg]
            return_df = return_df.append(alternative[alt_delta], ignore_index=True, sort=False)
        return return_df

    def calc_delta_and_keep_alt_id(self, *args):
        """

        :param args: Metrics for which deltas or reductions are sought.
        :return: The passed DataFrame with metrics in list_for_deltas showing as reductions from baseline rather than the values contained in the passed DataFrame
        """
        return_df = pd.DataFrame(self.data.loc[self.data['optionID'] == 0, :])
        alternative = dict()
        alternative[0] = pd.DataFrame(self.data.loc[self.data['optionID'] == 0, :])
        alternative[0].reset_index(drop=True, inplace=True)
        alts = pd.Series(self.data['optionID'].unique())
        for alt in range(1, len(alts)):
            alternative[alt] = pd.DataFrame(self.data.loc[self.data['optionID'] == alt, :])
            alternative[alt].reset_index(drop=True, inplace=True)
            for arg in args:
                alternative[alt][arg] = alternative[0][arg] - alternative[alt][arg]
            return_df = return_df.append(alternative[alt], ignore_index=True, sort=False)
        for arg in args:
            return_df.rename(columns={arg: f'{arg}_Reductions'}, inplace=True)
            return_df.loc[return_df['optionID'] == 0, f'{arg}_Reductions'] = 0
        return return_df


if __name__ == '__main__':
    """
    This tests the CalcDeltas class to ensure that things are working properly.
    If run as a script (python -m cti_bca_tool.calc_deltas) the first DataFrame should show metric_Reductions values of 0 for optionID 0 and 100 
    for optionID 1 and the second DataFrame should show metric values of -100 for optionID 10.

    """
    import pandas as pd

    df = pd.DataFrame({'optionID': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,],
                       'OptionName': ['Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1',],
                       'modelYearID': [2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028, 2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028,],
                       'regClassID': [46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47,],
                       'fuelTypeID': [1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2,],
                       'metric': [200, 200, 200, 200, 300, 300, 300, 300, 100, 100, 100, 100, 200, 200, 200, 200,]})

    df1 = CalcDeltas(df).calc_delta_and_keep_alt_id('metric')
    print(f'\nFirst DataFrame should show metric_Reductions values of 0 for optionID 0 and 100 for optionID 1\n{df1}')

    df2 = pd.concat([df, CalcDeltas(df).calc_delta_and_new_alt_id('metric')], axis=0, ignore_index=True) # modelYearID=2027,2028,2029; metric=400,800,1200
    print(f'\nSecond DataFrame should show metric values of -100 for optionID 10\n{df2}')
