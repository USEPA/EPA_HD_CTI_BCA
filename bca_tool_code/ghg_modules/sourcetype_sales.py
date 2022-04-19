import pandas as pd


class SourceTypeSales:
    """

    The SourceTypeSales class creates the sourcetype sales by cost step and provides methods to query its data.

    """
    def __init__(self):
        self._dict = dict()
        self.age0_keys = None

    def create_sourcetype_sales_dict(self, data_object, cost_steps):
        """

        This method simply generates sales by sourcetype via Pandas which is faster than summing via dictionary.

        Parameters:
            data_object: object; the fleet data object.\n
            cost_steps: List; steps of newly added costs, e.g., '2027', '2031'.

        Returns:
            Creates a dictionary of the fleet having keys of (engine, alt, modelYearID) where engine is a
            tuple (sourcetype_id, regclass_id, fueltype_id), and values representing sales (sales=VPOP at ageID=0) for
            each key by model year; creates other attributes specified in the class __init__.

        """
        _df = data_object.fleet_df.copy()
        _df = pd.DataFrame(_df.loc[(_df['ageID'] == 0) & (_df['DiscountRate'] == 0),
                                   ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID',
                                    'ageID', 'VPOP', 'VPOP_withTech']]).reset_index(drop=True)

        _df = _df.groupby(by=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID'],
                          as_index=False).sum()

        key = pd.Series(
            zip(zip(_df['sourceTypeID'], _df['regClassID'], _df['fuelTypeID']), _df['optionID'], _df['modelYearID']))
        _df.set_index(key, inplace=True)

        # calc cumulative sales by step
        for cost_step in cost_steps:
            cost_step = pd.to_numeric(cost_step)
            temp = _df.loc[_df['modelYearID'] >= cost_step, ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID',
                                                             'VPOP_withTech']]
            temp = temp.groupby(by=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID'], as_index=False).cumsum()
            temp.rename(columns={'VPOP_withTech': f'VPOP_withTech_Cumulative_{cost_step}'}, inplace=True)
            temp.insert(len(temp.columns), f'Cost_PerVeh_{cost_step}', 0)
            _df = _df.merge(temp, left_index=True, right_index=True, how='outer')

        _df.fillna(0, inplace=True)

        self._dict = _df.to_dict('index')

        # set keys
        self.age0_keys = tuple([k for k, v in self._dict.items() if v['ageID'] == 0])

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: tuple; ((sourcetype_id, regclass_id, fueltype_id), option_id, model year). \n
            attribute_name: str; the attribute for which a value is sought.

        Returns:
            The value of the attribute name for the given key.

        """
        return self._dict[key][attribute_name]

    def update_dict(self, key, input_dict):
        """

        Parameters:
            key: tuple; ((sourcetype_id, regclass_id, fueltype_id), option_id, model year). \n
            input_dict: Dictionary; represents the attribute_name-attribute_value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        """
        for attribute, value in input_dict.items():

            self._dict[key][attribute] = value
