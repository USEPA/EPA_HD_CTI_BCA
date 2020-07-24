import pandas as pd

# list of metrics to which to applying learning; note that keys in the learning dict represent fuelTypeID
tech_apply_learning_common = ['EngineHardware', 'CDA']
tech_apply_learning_dict = {1: tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
                            2: tech_apply_learning_common + ['CDPF', 'DOC', 'SCR', 'HCdosing', 'Canning', 'ClosedCrankcase'],
                            3: tech_apply_learning_common + ['Aftertreatment'],
                            5: tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
                            9: '',
                            }


class DirectCost:
    """The DirectCost class brings together the various elements: package costs; techpens; seed volumes; and, vehicle populations (specifically vehicle sales).
    A single vehicle is the object of the class and the class methods bring in the appropriate costing elements.

    :param _veh: A unique vehicle object.
    :typle _veh: tuple of 3 to 5 integers, where the first entry is always the optionID.
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

    # def cumulative_sales_scalar_regclass(self, _seed_vols):
    #     """
    #     :param _seed_vols: The seed volume factors input file by reg class.
    #     :type _seed_vols: DataFrame
    #     :return:  A single cumulative sales volume scalar for use in calculating learning effects for a specific optionID-regclassID-fueltypeID vehicle.
    #     """
    #     _pkg_seedvol_df = _seed_vols.loc[_seed_vols['alt_rc_ft'] == self._veh, :]
    #     _pkg_seedvol_df.reset_index(drop=True, inplace=True)
    #     _pkg_sales_vol_scalar = _pkg_seedvol_df['CumulativeSalesScalar'][0]
    #     return _pkg_sales_vol_scalar

    def pkg_cost_regclass_withlearning(self, _sales, step, _pkg_cost_veh, _pkg_seedvol, _learning_rate):
        """
        :param _sales: The sales by year for the fleet being considered; the first year of sales must correspond to the implementation step of new standards.
        :type _sales: DataFrame
        :param step: The cadence or step of implementation and associated costs
        :type step: String
        :param _pkg_cost_veh: The direct cost of the package being applied to a unique optionID-regclassID-fueltypeID vehicle.
        :type _pkg_cost_veh: Numeric
        :param _pkg_seedvol: The seed volume factor for use in calculating learning effects following implementation for a specific optionID-regclassID-fueltypeID vehicle.
        :type _pkg_seedvol: Numeric
        :param _learning_rate: The learning rate entered in the BCA inputs sheet.
        :type _learning_rate: Numeric
        :return: A DataFrame of package costs per vehicle with learning applied and then total costs.
        """
        df = pd.DataFrame(_sales.loc[_sales['alt_rc_ft'] == self._veh, :])
        df.reset_index(drop=True, inplace=True)
        # get VPOP at age0 for use in learning calc later
        vpop_age0 = pd.Series(df['VPOP'])[0]
        # insert some new columns, set to zero or empty string, then calc desired results
        new_metric_numeric = [f'Sales_RegClass-FuelType_Cumulative_{step}', 'SeedVolumeFactor', # 'CumulativeSalesScalar',
                              f'DirectCost_AvgPerVeh_{step}', f'DirectCost_TotalCost_{step}']
        for metric in new_metric_numeric:
            df.insert(len(df.columns), metric, 0)
        # now calculate results for these new metrics
        df[f'Sales_RegClass-FuelType_Cumulative_{step}'] = df['VPOP'].cumsum()
        df['SeedVolumeFactor'] = _pkg_seedvol
        df[f'DirectCost_AvgPerVeh_{step}'] = _pkg_cost_veh * (((df[f'Sales_RegClass-FuelType_Cumulative_{step}'] + (vpop_age0 * _pkg_seedvol))
                                                             / (vpop_age0 + (vpop_age0 * _pkg_seedvol)))
                                                            ** _learning_rate)
        df[f'DirectCost_TotalCost_{step}'] = df[f'DirectCost_AvgPerVeh_{step}'] * df['VPOP']
        return df

    def pkg_cost_regclass_withlearning2(self, df_source, step, pkg_cost_veh, pkg_seedvol, pkg_sales_vol_scalar, learning_rate):
        """
        :param sales: The sales by year for the fleet being considered; the first year of sales must correspond to the implementation step of new standards.
        :type sales: DataFrame
        :param step: The cadence or step of implementation and associated costs
        :type step: String
        :param pkg_cost_veh: The direct cost of the package being applied to a unique optionID-regclassID-fueltypeID vehicle.
        :type pkg_cost_veh: Numeric
        :param pkg_seedvol: The seed volume factor for use in calculating learning effects following implementation for a specific optionID-regclassID-fueltypeID vehicle.
        :type pkg_seedvol: Numeric
        :param pkg_sales_vol_scalar: The cumulative sales volume scalar meant to learn or unlearn a cost estimate prior to implementation (not common).
        :type pkg_sales_vol_scalar: Numeric
        :param learning_rate: The learning rate entered in the BCA inputs sheet.
        :type learning_rate: Numeric
        :return:
        """
        df_return = pd.DataFrame(df_source.loc[(df_source['alt_rc_ft'] == self._veh) & (df_source['ageID'] == 0), :])
        df_return.reset_index(drop=True, inplace=True)
        #
        groupby_metrics = ['optionID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID', 'ageID', 'alt_rc_ft']
        sales_rcid_ftid = _sales[groupby_metrics + ['VPOP']].groupby(by=groupby_metrics, as_index=False).sum()
        # get VPOP at age0 for use in learning calc later
        vpop_age0 = pd.Series(df_return['VPOP'])[0]
        # insert some new columns, set to zero or empty string, then calc desired results
        new_metric_numeric = [f'VPOP_Complying_Cumulative_{step}', 'SeedVolumeFactor', 'CumulativeSalesScalar',
                              f'DirectCost_AvgPerVeh_{step}', f'DirectCost_TotalCost_{step}']
        for metric in new_metric_numeric:
            df_return.insert(len(df_return.columns), metric, 0)
        # now calculate results for these new metrics
        df_return[f'VPOP_Complying_Cumulative_{step}'] = df_return['VPOP'].cumsum()
        df_return['SeedVolumeFactor'] = pkg_seedvol
        df_return['SalesVolumeScalar'] = pkg_sales_vol_scalar
        df_return[f'DirectCost_AvgPerVeh_{step}'] = pkg_cost_veh * \
                                                    (((df_return[f'VPOP_Complying_Cumulative_{step}'] * pkg_sales_vol_scalar + (vpop_age0 * pkg_seedvol))
                                                      / (vpop_age0 + (vpop_age0 * pkg_seedvol))) ** learning_rate)
        df_return[f'DirectCost_TotalCost_{step}'] = df_return[f'DirectCost_AvgPerVeh_{step}'] * df_return['VPOP']
        # df_return = df_return[['optionID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID', 'ageID',
        #          'alt_rc_ft', 'VPOP', f'VPOP_Complying_Cumulative_{step}',
        #          'SeedVolumeFactor', 'SalesVolumeScalar',
        #          f'DirectCost_AvgPerVeh_{step}', f'DirectCost_TotalCost_{step}']]
        return df_return
