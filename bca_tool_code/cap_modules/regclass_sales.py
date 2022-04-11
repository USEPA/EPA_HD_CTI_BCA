import pandas as pd


class RegClassSales:

    _dict = dict()

    @staticmethod
    def create_regclass_sales_dict(df, cost_steps):
        """

        This method simply generates sales by regclass via Pandas which is faster than summing via dictionary.

        Parameters:
            df: DataFrame; the project fleet.
            cost_steps: List; steps of newly added costs, e.g., '2027', '2031'.

        Returns:
            A dictionary of the fleet having keys of (engine, alt, modelYearID) where engine is a tuple representing
            a regclass_fueltype, and values representing sales (sales=VPOP at ageID=0) for each key by model year.

        """
        RegClassSales._dict.clear()
        _df = df.copy()
        _df = pd.DataFrame(_df.loc[(_df['ageID'] == 0) & (_df['DiscountRate'] == 0),
                                   ['optionID', 'regClassID', 'fuelTypeID', 'modelYearID',
                                    'ageID', 'VPOP', 'VPOP_withTech']]).reset_index(drop=True)

        _df = _df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID'], as_index=False).sum()

        key = pd.Series(
            zip(zip(_df['regClassID'], _df['fuelTypeID']), _df['optionID'], _df['modelYearID']))
        _df.set_index(key, inplace=True)

        # calc cumulative sales by step
        for cost_step in cost_steps:
            cost_step = pd.to_numeric(cost_step)
            temp = _df.loc[_df['modelYearID'] >= cost_step, ['optionID', 'regClassID', 'fuelTypeID', 'VPOP_withTech']]
            temp = temp.groupby(by=['optionID', 'regClassID', 'fuelTypeID'], as_index=False).cumsum()
            temp.rename(columns={'VPOP_withTech': f'VPOP_withTech_Cumulative_{cost_step}'}, inplace=True)
            temp.insert(len(temp.columns), f'Cost_PerVeh_{cost_step}', 0)
            _df = _df.merge(temp, left_index=True, right_index=True, how='outer')

        _df.fillna(0, inplace=True)

        RegClassSales._dict = _df.to_dict('index')

    @staticmethod
    def get_attribute_value(key, attribute_name):
        """

        Args:
            key:
            attribute_name:

        Returns:

        """
        return RegClassSales._dict[key][attribute_name]

    @staticmethod
    def update_dict(key, input_dict):
        """

        Parameters:
            key: Tuple; the Dictionary key. \n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        """
        for attribute, value in input_dict.items():

            RegClassSales._dict[key][attribute] = value
