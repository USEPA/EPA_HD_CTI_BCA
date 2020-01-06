import pandas as pd


class CalcDeltas:
    """The CalcDelta class calculates the deltas (more stringent option minus option 0, as written)

    :param data: Data being passed on which deltas are to be calculated.
    :type data: DataFrame
    """
    def __init__(self, data):
        self.data = data

    def calc_delta(self, _number_alts, _list):
        """

        :param _number_alts: The number of alternatives, or options, being considered in the data.
        :type _number_alts: Integer
        :param _list: List of metrics for which to calculate deltas.
        :type _list: List
        :return: A new DataFrame consisting of the passed DataFrame appended with deltas for each scenario in the passed data.
        """
        return_df = pd.DataFrame()
        alternative = dict()
        alternative[0] = self.data.loc[self.data['optionID'] == 0, :]
        alternative[0].reset_index(drop=True, inplace=True)
        alt0_name = alternative[0].at[0, 'OptionName']
        for alt in range(1, _number_alts):
            alternative[alt] = self.data.loc[self.data['optionID'] == alt, :]
            alternative[alt].reset_index(drop=True, inplace=True)
            alt_name = alternative[alt].at[0, 'OptionName']
            alt_delta = int(alt * 10)
            alternative[alt_delta] = pd.DataFrame(alternative[alt].copy())
            alternative[alt_delta]['optionID'] = alt_delta
            alternative[alt_delta]['OptionName'] = alt_name + '_minus_' + alt0_name
        for alt in range(1, _number_alts):
            alt_delta = int(alt * 10)
            for item in _list:
                alternative[alt_delta][item] = alternative[alt][item] - alternative[0][item]
            return_df = return_df.append(alternative[alt_delta], ignore_index=True, sort=False)
        return return_df
