"""The fleet module contains the Fleet class."""

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

    def define_bca_sourcetype_zg(self):
        """

        :return: Add identifier column to the passed fleet DataFrame consisting of a tuple providing optionID, sourcetypeID, regClassID, fuelTypeID, zgtechID.
        """
        self.fleet.insert(0, 'alt_st_rc_ft_zg', pd.Series(zip(self.fleet['optionID'], self.fleet['sourceTypeID'], self.fleet['regClassID'], self.fleet['fuelTypeID'], self.fleet['zerogramTechID'])))
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
        _sales = Fleet(self.fleet).sales()
        groupby_metrics = ['optionID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID', 'ageID', 'alt_rc_ft']
        sales_rcid_ftid = _sales[groupby_metrics + ['VPOP']].groupby(by=groupby_metrics, as_index=False).sum()
        sales_rcid_ftid.reset_index(drop=True, inplace=True)
        return sales_rcid_ftid
    
    def fleet_with_0gtech(self, _zgtech, _zgtech_max):
        """Return fleet with MOVES results shifted from ICE-only and into zero gram techs according to the percentages and growths provided in the inputs.

        :param _zgtech: A DataFrame providing direct costs for different sourcetypes and zero/low gram techs
        :param _zgtech_max: The maximum number of zero/low gram techs being considered (may be zero)
        :return: A fleet DataFrame with ICE sales dispersed into various zerogram tech sales.
        """
        pd.set_option('mode.chained_assignment', 'raise')

        fleet_zgtech = dict()
        for tech in range(0, _zgtech_max + 1):
            _zgtech_bytech = _zgtech.loc[_zgtech['zerogramTechID'] == tech, ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID',
                                                                             'alt_rc_ft', 'alt_st_rc_ft', 'TechPackageDescription',
                                                                             'percent', 'growth', 'SeedVolumeFactor']]
            year_min = int(_zgtech.loc[_zgtech['zerogramTechID'] == tech, 'yearID'].min())
            fleet_zgtech[tech] = self.fleet.merge(_zgtech_bytech, on=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID',
                                                                      'alt_rc_ft', 'alt_st_rc_ft'], how='left', sort=False)
            for metric in ['percent', 'growth']:
                fleet_zgtech[tech][metric].fillna(0, inplace=True)
            fleet_zgtech[tech].loc[fleet_zgtech[tech]['modelYearID'] < year_min, 'percent'] = 0
            fleet_zgtech[tech].loc[fleet_zgtech[tech]['modelYearID'] < year_min, 'growth'] = 0
            fleet_zgtech[tech]['zerogramTechID'] = tech
            fleet_zgtech[tech]['zerogramTechID'] = fleet_zgtech[tech]['zerogramTechID'].astype('int32')
            if tech > 0:
                fleet_zgtech[tech]['VPOP'] = fleet_zgtech[tech]['VPOP'] * fleet_zgtech[tech]['percent'] * (1 + fleet_zgtech[tech]['growth']) ** (fleet_zgtech[tech]['yearID'] - year_min)
            fleet_zgtech[tech].drop(columns=['percent', 'growth'], inplace=True)
        fleet_with_zgtech = pd.DataFrame(fleet_zgtech[0])
        for tech in range(1, _zgtech_max + 1):
            fleet_with_zgtech['VPOP'] = fleet_with_zgtech['VPOP'] - fleet_zgtech[tech]['VPOP']
        for tech in range(1, _zgtech_max + 1):
            fleet_with_zgtech = pd.concat([fleet_with_zgtech, fleet_zgtech[tech]], axis=0, ignore_index=True)
        fleet_with_zgtech.reset_index(drop=True, inplace=True)
        fleet_with_zgtech['VMT'] = fleet_with_zgtech['VMT_AvgPerVeh'] * fleet_with_zgtech['VPOP'] # this correctly sets VMT to zero where VPOP is zero, but leaves VMT/vehicle=moves
        fleet_with_zgtech.loc[fleet_with_zgtech['VMT'] == 0, 'VMT_AvgPerVeh'] = 0 # this sets VMT/vehicle = 0 where VMT=0
        fleet_with_zgtech['Gallons'] = fleet_with_zgtech['VMT'] / fleet_with_zgtech['MPG_AvgPerVeh']
        fleet_with_zgtech.loc[fleet_with_zgtech['Gallons'] == 0, 'MPG_AvgPerVeh'] = 0
        return fleet_with_zgtech

    def insert_option_name(self, options, number_alts):
        """

        :param options: A DataFrame providing the OptionName for each optionID.
        :param number_alts: The maximum number of options or alternatives in the fleet input file.
        :return: The passed fleet DataFrame with a new and populated column called OptionName.
        """
        # First create a dictionary of options from the dataframe of options.
        options_dict = dict()
        for index, row in options.iterrows():
            key = row['optionID']
            value = row['OptionName']
            options_dict[key] = value
        # This dictionary will work nicely in the following loop. But first insert the new column to be populated in the loop.
        self.fleet.insert(1, 'OptionName', '')
        for option in range(0, number_alts):
            self.fleet.loc[self.fleet['optionID'] == option, 'OptionName'] = options_dict[option]
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
