import pandas as pd


class RegClassSales:
    """

    The RegClassSales class creates the regclass sales by cost step and provides methods to query its data.

    """
    def __init__(self):
        self._dict = dict()
        self.age0_keys = None

    def create_regclass_sales_dict(self, df, cost_steps):
        """

        This method simply generates sales by regclass via Pandas which is faster than summing via dictionary.

        Parameters:
            df: DataFrame; the project fleet.
            cost_steps: List; steps of newly added costs, e.g., '2027', '2031'.

        Returns:
            A dictionary of the fleet having keys of (engine, alt, modelYearID) where engine is a tuple representing
            a regclass_fueltype, and values representing sales (sales=VPOP at ageID=0) for each key by model year.

        """
        _df = df.copy()
        _df = pd.DataFrame(_df.loc[(_df['ageID'] == 0) & (_df['DiscountRate'] == 0),
                                   ['optionID', 'regClassID', 'fuelTypeID', 'modelYearID',
                                    'ageID', 'VPOP']]).reset_index(drop=True)

        _df = _df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID'], as_index=False).sum()

        key = pd.Series(
            zip(zip(_df['regClassID'], _df['fuelTypeID']), _df['optionID'], _df['modelYearID']))
        _df.set_index(key, inplace=True)

        # calc cumulative sales by step
        for cost_step in cost_steps:
            cost_step = pd.to_numeric(cost_step)
            temp = _df.loc[_df['modelYearID'] >= cost_step, ['optionID', 'regClassID', 'fuelTypeID', 'VPOP']]
            temp = temp.groupby(by=['optionID', 'regClassID', 'fuelTypeID'], as_index=False).cumsum()
            temp.rename(columns={'VPOP': f'VPOP_Cumulative_{cost_step}'}, inplace=True)
            temp.insert(len(temp.columns), f'Cost_PerVeh_{cost_step}', 0)
            _df = _df.merge(temp, left_index=True, right_index=True, how='outer')

        _df.fillna(0, inplace=True)

        self._dict = _df.to_dict('index')

        # set keys
        self.age0_keys = tuple([k for k, v in self._dict.items() if v['ageID'] == 0])

    def get_attribute_value(self, key, attribute_name):
        """

        Args:
            key:
            attribute_name:

        Returns:

        """
        return self._dict[key][attribute_name]

    def update_dict(self, key, input_dict):
        """

        Parameters:
            key: Tuple; the Dictionary key. \n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        """
        for attribute, value in input_dict.items():

            self._dict[key][attribute] = value
