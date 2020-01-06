import pandas as pd

# list of metrics to which to applying learning
tech_apply_learning_common = ['EngineHardware', 'CDA']
tech_apply_learning_dict = {1: tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
                            2: tech_apply_learning_common + ['CDPF', 'DOC', 'SCR', 'HCdosingCanning'],
                            3: tech_apply_learning_common + ['CDPF', 'DOC', 'SCR'],
                            5: tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
                            9: '',
                            }


class DirectCost:
    """The DirectCost class brings together the various elements: package costs; techpens; seed volumes; and, vehicle populations (specifically vehicle sales).
    A single vehicle is the object of the class and the class methods bring in the appropriate costing elements.

    :param _veh: A unique vehicle object.
    :type _veh: tuple of 3 to 5 integers, where the first entry is always the optionID.
    """
    def __init__(self, _veh):
        self._veh = _veh
    
    def pkg_cost_vehicle_regclass1(self, _pkg_costs, step):
        """
        :param _pkg_costs: The direct cost inputs by reg class.
        :type _pkg_costs: DataFrame
        :return: A single package cost value for a specific optionID-regclassID-fueltypeID vehicle. This method is used if tech cost inputs DO NOT use the rollup approach.
        """
        pkg_cost = _pkg_costs.loc[_pkg_costs['alt_rc_ft'] == self._veh, ['TechPackageDescription', step]]
        pkg_cost = pkg_cost.set_index('TechPackageDescription')
        pkg_cost_veh_regclass = 0
        tech_apply_learning = tech_apply_learning_dict[self._veh[2]]
        for tech in tech_apply_learning:
            pkg_cost_veh_regclass += pkg_cost.at[tech, step]
        return pkg_cost_veh_regclass

    def pkg_cost_vehicle_regclass2(self, _pkg_costs):
        """
        :param _pkg_costs: The direct cost inputs by reg class.
        :type _pkg_costs: DataFrame
        :return: A single package cost value for a specific optionID-regclassID-fueltypeID vehicle. This method is used if tech cost inputs DO use the rollup approach.
        """
        pkg_cost = _pkg_costs.loc[_pkg_costs['alt_rc_ft'] == self._veh, ['TechPackageDescription', 'TechPackageCost']]
        pkg_cost = pkg_cost.set_index('TechPackageDescription')
        pkg_cost_veh_regclass = pkg_cost.at['Rollup', 'TechPackageCost']
        return pkg_cost_veh_regclass

    def pkg_cost_vehicle_zgtech(self, _zgtech):
        """
        :param _zgtech: The direct cost inputs by sourcetype.
        :type _zgtech: DataFrame
        :return: A single zgtech package cost value and the seed volume for a specific optionID-sourcetypeID-regclassID-fueltypeID-zgtechID vehicle.
        """
        pkg_cost_veh = _zgtech.loc[_zgtech['alt_st_rc_ft_zg'] == self._veh, :]
        pkg_cost_veh.reset_index(drop=True, inplace=True)
        _pkg_cost_veh = pkg_cost_veh['TechPackageCost'][0]
        _pkg_seedvol = pkg_cost_veh['SeedVolumeFactor'][0]
        return _pkg_cost_veh, _pkg_seedvol

    def pkg_techpen_vehicle(self, _pkg_techpens):
        """
        :param _pkg_techpens: The tech penetration (or phase-in) inputs by reg class.
        :type _pkg_techpens: DataFrame
        :return: A dataframe containing the tech pens by year for a specific optionID-regclassID-fueltypeID vehicle.
        """
        pkg_techpen_veh = _pkg_techpens.loc[_pkg_techpens['alt_rc_ft'] == self._veh, :]
        return pkg_techpen_veh

    def seedvol_factor_regclass(self, _seed_vols):
        """
        :param _seed_vols: The seed volume factors input file by reg class.
        :type _seed_vols: DataFrame
        :return:  A single seed volume factor for use in calculating learning effects for a specific optionID-regclassID-fueltypeID vehicle.
        """
        _pkg_seedvol_df = _seed_vols.loc[_seed_vols['alt_rc_ft'] == self._veh, :]
        _pkg_seedvol_df.reset_index(drop=True, inplace=True)
        _pkg_seedvol = _pkg_seedvol_df['SeedVolumeFactor'][0]
        return _pkg_seedvol

    def cumulative_sales_scalar_regclass(self, _seed_vols):
        """
        :param _seed_vols: The seed volume factors input file by reg class.
        :type _seed_vols: DataFrame
        :return:  A single cumulative sales volume scalar for use in calculating learning effects for a specific optionID-regclassID-fueltypeID vehicle.
        """
        _pkg_seedvol_df = _seed_vols.loc[_seed_vols['alt_rc_ft'] == self._veh, :]
        _pkg_seedvol_df.reset_index(drop=True, inplace=True)
        _pkg_sales_vol_scalar = _pkg_seedvol_df['CumulativeSalesScalar'][0]
        return _pkg_sales_vol_scalar

    def pkg_cost_regclass_withlearning(self, _sales, step, _pkg_cost_veh, _pkg_seedvol, _pkg_sales_vol_scalar, _learning_rate):
        """
        :param _sales: The sales by year for the fleet being considered; the first year of sales must correspond to the implementation step of new standards.
        :type _sales: DataFrame
        :param step: The cadence or step of implementation and associated costs
        :type step: String
        :param _pkg_cost_veh: The direct cost of the package being applied to a unique optionID-regclassID-fueltypeID vehicle.
        :type _pkg_cost_veh: Numeric
        :param _pkg_seedvol: The seed volume factor for use in calculating learning effects following implementation for a specific optionID-regclassID-fueltypeID vehicle.
        :type _pkg_seedvol: Numeric
        :param _pkg_sales_vol_scalar: The cumulative sales volume scalar meant to learn or unlearn a cost estimate prior to implementation (not common).
        :type _pkg_sales_vol_scalar: Numeric
        :param _learning_rate: The learning rate entered in the BCA inputs sheet.
        :type _learning_rate: Numeric
        :return: A DataFrame of package costs per vehicle with learning applied and total costs with the column index:
                ['optionID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID, 'ageID', 'alt_rc_ft',
                'VPOP', 'VPOP_Complying_Cumulative','SeedVolume', 'SalesVolumeScalar',
                'DirectCost_AvgPerVeh', 'DirectCost_TotalCost']
        """
        df = pd.DataFrame(_sales.loc[_sales['alt_rc_ft'] == self._veh, :])
        df.reset_index(drop=True, inplace=True)
        # get VPOP at age0 for use in learning calc later
        vpop_age0 = pd.Series(df['VPOP'])[0]
        # insert some new columns, set to zero or empty string, then calc desired results
        new_metric_numeric = ['VPOP_Complying_Cumulative_' + step, 'SeedVolumeFactor', 'CumulativeSalesScalar',
                              'DirectCost_AvgPerVeh_' + step, 'DirectCost_TotalCost_' + step]
        for metric in new_metric_numeric:
            df.insert(len(df.columns), metric, 0)
        # now calculate results for these new metrics
        df['VPOP_Complying_Cumulative_' + step] = df['VPOP'].cumsum()
        df['SeedVolumeFactor'] = _pkg_seedvol
        df['SalesVolumeScalar'] = _pkg_sales_vol_scalar
        df['DirectCost_AvgPerVeh_' + step] = _pkg_cost_veh * (((df['VPOP_Complying_Cumulative_' + step] * _pkg_sales_vol_scalar + (vpop_age0 * _pkg_seedvol))
                                                             / (vpop_age0 + (vpop_age0 * _pkg_seedvol)))
                                                            ** _learning_rate)
        df['DirectCost_TotalCost_' + step] = df['DirectCost_AvgPerVeh_' + step] * df['VPOP']
        df = df[['optionID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID', 'ageID',
                 'alt_rc_ft', 'VPOP', 'VPOP_Complying_Cumulative_' + step,
                 'SeedVolumeFactor', 'SalesVolumeScalar',
                 'DirectCost_AvgPerVeh_' + step, 'DirectCost_TotalCost_' + step]]
        return df

    def pkg_cost_zgtech_withlearning(self, _sales, _pkg_cost_veh, _techpen, _pkg_seedvol, _learning_rate):
        """
        :param _sales: The sales by year for the fleet being considered.
        :type _sales: DataFrame
        :param _pkg_cost_veh: The direct cost of the package being applied to a unique optionID-sourcetypeID-regclassID-fueltypeID-zgtechID vehicle.
        :type _pkg_cost_veh: Number
        :param _techpen: The tech pen for a unique optionID-sourcetypeID-regclassID-fueltypeID-zgtechID vehicle; this is hardcoded as 0 where zgtechID=0 and 1 where zgtechID>0.
        :type _techpen: Number
        :param _pkg_seedvol: The seed volume factor for use in calculating learning effects for a unique optionID-sourcetypeID-regclassID-fueltypeID-zgtechID.
        :type _pkg_seedvol: Number
        :param _learning_rate: The learning rate entered in the BCA inputs sheet.
        :type _learning_rate: Number
        :return: A DataFrame of package costs per vehicle with learning applied and total costs with the column index:
                ['optionID', 'yearID', 'modelYearID', 'ageID','sourcetypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID', 
                'alt_rc_ft', 'alt_st_rc_ft', 'alt_st_rc_ft_zg',
                'VPOP', 'VPOP_Complying_ZG', 'VPOP_Complying_Cumulative_ZG',
                'DirectCost_WithLearning_ZG', 'DirectCost_AvgPerVeh_ZG', 'DirectCost_TotalCost_ZG']
        """
        df = _sales.copy()
        df.reset_index(drop=True, inplace=True)
        # get VPOP at age0 for use in learning calc later
        vpop_age0 = pd.Series(df['VPOP'])[0]
        new_metric_numeric = ['VPOP_Complying_ZG', 'VPOP_Complying_Cumulative_ZG', 'DirectCost_WithLearning_ZG', 'DirectCost_TotalCost_ZG', 'DirectCost_AvgPerVeh_ZG']
        for metric in new_metric_numeric:
            df.insert(len(df.columns), metric, 0)
        # now calculate results for these new metrics
        df['VPOP_Complying_ZG'] = df['VPOP'] * _techpen
        df['VPOP_Complying_Cumulative_ZG'] = df['VPOP_Complying_ZG'].cumsum()
        df['DirectCost_WithLearning_ZG'] = _pkg_cost_veh * (((df['VPOP_Complying_Cumulative_ZG'] + (vpop_age0 * _pkg_seedvol))
                                                             / (vpop_age0 + (vpop_age0 * _pkg_seedvol)))
                                                            ** _learning_rate)
        df['DirectCost_TotalCost_ZG'] = df['DirectCost_WithLearning_ZG'] * df['VPOP_Complying_ZG']
        df['DirectCost_AvgPerVeh_ZG'] = df['DirectCost_TotalCost_ZG'] / df['VPOP']
        df = df[['optionID', 'yearID', 'modelYearID', 'ageID', 'sourcetypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID',
                 'alt_rc_ft', 'alt_st_rc_ft', 'alt_st_rc_ft_zg',
                 'VPOP', 'VPOP_Complying_ZG', 'VPOP_Complying_Cumulative_ZG',
                 'DirectCost_WithLearning_ZG', 'DirectCost_AvgPerVeh_ZG', 'DirectCost_TotalCost_ZG']]
        return df