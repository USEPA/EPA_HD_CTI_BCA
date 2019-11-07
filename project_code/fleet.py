"""The fleet module contains the Fleet class."""

import pandas as pd


class Fleet:
    """
    The Fleet class creates vehicle identifiers used by the Vehicle class. It also returns a fleet consisting of sales (ageID=0) data only.
    The Fleet class also takes in zero/low gram tech data and adjusts MOVES populations and VMT accordingly.
    """

    def __init__(self, fleet):
        self.fleet = fleet
        
    def define_bca_regclass(self):
        """Add identifier column to the passed fleet dataframe consisting of a tuple providing optionID, regClassID, fuelTypeID."""
        self.fleet.insert(0, 'alt_rc_ft', pd.Series(zip(self.fleet['optionID'], self.fleet['regClassID'], self.fleet['fuelTypeID'])))
        return self.fleet

    def define_bca_sourcetype(self):
        """Add identifier column to the passed fleet dataframe consisting of a tuple providing optionID, sourcetypeID, regClassID, fuelTypeID."""
        self.fleet.insert(0, 'alt_st_rc_ft', pd.Series(zip(self.fleet['optionID'], self.fleet['sourcetypeID'], self.fleet['regClassID'], self.fleet['fuelTypeID'])))
        return self.fleet

    def define_bca_sourcetype_zg(self):
        """Add identifier column to the passed fleet dataframe consisting of a tuple providing optionID, sourcetypeID, regClassID, fuelTypeID, zgtechID."""
        self.fleet.insert(0, 'alt_st_rc_ft_zg', pd.Series(zip(self.fleet['optionID'], self.fleet['sourcetypeID'], self.fleet['regClassID'], self.fleet['fuelTypeID'], self.fleet['zerogramTechID'])))
        return self.fleet

    def sales(self):
        """

        :return: A new DataFrame consisting of only sales from the passed fleet DataFrame (ageID=0).
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

        :param _zgtech: from the inputs providing direct costs for different sourcetypes and zero/low gram techs
        :type _zgtech: dataframe

        :param _zgtech_max: the maximum number of zero/low gram techs being considered (may be zero)
        :type _zgtech_max: float
        """
        pd.set_option('mode.chained_assignment', 'raise')

        fleet_zgtech = dict()
        for tech in range(0, _zgtech_max + 1):
            _zgtech_bytech = _zgtech.loc[_zgtech['zerogramTechID'] == tech, ['optionID', 'sourcetypeID', 'regClassID', 'fuelTypeID',
                                                                             'alt_rc_ft', 'alt_st_rc_ft', 'TechPackageDescription',
                                                                             'percent', 'growth', 'SeedVolumeFactor']]
            year_min = int(_zgtech.loc[_zgtech['zerogramTechID'] == tech, 'yearID'].min())
            fleet_zgtech[tech] = self.fleet.merge(_zgtech_bytech, on=['optionID', 'sourcetypeID', 'regClassID', 'fuelTypeID',
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
            fleet_with_zgtech = fleet_with_zgtech.append(fleet_zgtech[tech], ignore_index=True, sort=False)
        fleet_with_zgtech.reset_index(drop=True, inplace=True)
        # fleet_with_zgtech['VMT'] = fleet_with_zgtech['VMT/vehicle'] * fleet_with_zgtech['VPOP'] # this correctly sets VMT to zero where VPOP is zero, but leaves VMT/vehicle=moves
        # fleet_with_zgtech.loc[fleet_with_zgtech['VMT'] == 0, 'VMT/vehicle'] = 0 # this sets VMT/vehicle = 0 where VMT=0
        # fleet_with_zgtech['Gallons'] = fleet_with_zgtech['Gallons/mile'] * fleet_with_zgtech['VMT']
        # fleet_with_zgtech.loc[fleet_with_zgtech['Gallons'] == 0, 'Gallons/mile'] = 0
        return fleet_with_zgtech

    def insert_option_name(self, _options, _number_alts):
        """Return a new column called OptionName in the passed fleet dataframe and populate with the name associated with the optionID column of the passed fleet.

        :param _options: from the input file providing optionID and OptionName
        :type _options: dataframe

        :param _number_alts: the maximum number of options or alternatives in the MOVES input file
        :type _number_alts: int
        """
        # First create a dictionary of options from the dataframe of options.
        options_dict = dict()
        for index, row in _options.iterrows():
            key = row['optionID']
            value = row['OptionName']
            options_dict[key] = value
        # This dictionary will work nicely in the following loop. But first insert the new column to be populated in the loop.
        self.fleet.insert(1, 'OptionName', '')
        for option in range(0, _number_alts):
            self.fleet.loc[self.fleet['optionID'] == option, 'OptionName'] = options_dict[option]
        return self.fleet
