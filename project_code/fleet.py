"""
fleet.py

Contains the Fleet class.

"""

import pandas as pd


class Fleet:
    """
    The Fleet class creates vehicle identifiers used by the Vehicle class. It also returns a fleet consisting of sales (ageID=0) data only.
    The Fleet class also takes in zero/low gram tech data and adjusts MOVES populations and VMT accordingly.

    :param fleet: A DataFrame representing a fleet of vehicles and associated data.
    """

    def __init__(self, fleet):
        self.fleet = fleet
        
    def define_bca_regclass(self):
        """

        :return: Add an identifier column to the passed fleet DataFrame consisting of a tuple providing optionID, regClassID, fuelTypeID.
        """
        self.fleet.insert(0, 'alt_rc_ft', pd.Series(zip(self.fleet['optionID'], self.fleet['regClassID'], self.fleet['fuelTypeID'])))
        return self.fleet

    def define_bca_sourcetype(self):
        """

        :return: Add identifier column to the passed fleet DataFrame consisting of a tuple providing optionID, sourcetypeID, regClassID, fuelTypeID.
        """
        self.fleet.insert(0, 'alt_st_rc_ft', pd.Series(zip(self.fleet['optionID'], self.fleet['sourceTypeID'], self.fleet['regClassID'], self.fleet['fuelTypeID'])))
        return self.fleet

    def sales(self):
        """

        :return: A new DataFrame consisting of only sales from the passed fleet DataFrame (i.e., ageID=0).
        """
        _sales = self.fleet.loc[self.fleet['ageID'] == 0, :]
        _sales.reset_index(drop=True, inplace=True)
        return _sales

    def sales_by_alt_rc_ft(self):
        """

        :return: A DataFrame of sales of vehicles by optionID, regClassID, fuelTypeID along with yearID for use in the DirectCost class.
        """
        _sales = Fleet(self.fleet).sales() # the sales method returns ageID=0 only
        groupby_metrics = ['optionID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID', 'ageID', 'alt_rc_ft']
        sales_rcid_ftid = _sales[groupby_metrics + ['VPOP']].groupby(by=groupby_metrics, as_index=False).sum()
        sales_rcid_ftid.reset_index(drop=True, inplace=True)
        return sales_rcid_ftid

    def insert_option_name(self, options_dict, number_alts):
        """

        :param options_dict: A dictionary providing the OptionName for each optionID.
        :param number_alts: The maximum number of options or alternatives in the fleet input file.
        :return: The passed fleet DataFrame with a new and populated column called OptionName.
        """
        self.fleet.insert(1, 'OptionName', '')
        for option in range(0, number_alts):
            self.fleet.loc[self.fleet['optionID'] == option, 'OptionName'] = options_dict[option]['OptionName']
        return self.fleet

    def adjust_moves(self, moves_adjustments_df):
        """

        :param moves_adjustments_df: A DataFrame of adjustments to be made to MOVES values
        :return: The MOVES fleet adjusted to account for the adjustments needed in the analysis.
        """
        moves_df = self.fleet.copy()
        for index, row in moves_adjustments_df.iterrows():
            veh = row['alt_rc_ft']
            percent_adjustment = row['percent']
            for metric in ['VPOP', 'VMT', 'Gallons']:
                moves_df.loc[moves_df['alt_rc_ft'] == veh, metric] = moves_df[metric] * percent_adjustment
        return moves_df
