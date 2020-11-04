"""
direct_cost.py

Contains the DirectCost class.

"""

import pandas as pd

# list of metrics to which to applying learning; note that keys in the learning dict represent fuelTypeID
# tech_apply_learning_common = ['EngineHardware', 'CDA']
# tech_apply_learning_dict = {1: tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
#                             2: tech_apply_learning_common + ['CDPF', 'DOC', 'SCR', 'HCdosing', 'Canning', 'ClosedCrankcase'],
#                             3: tech_apply_learning_common + ['Aftertreatment'],
#                             5: tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
#                             9: '',
#                             }


class DirectCost:
    """

    The DirectCost class brings together the various elements: package costs; seed volumes; and, vehicle populations (specifically vehicle sales_df).

    :param _veh: A tuple representing the given vehicle.
    :param step: The given implementation step (e.g., the CTI proposal called for new standards in 2027 and then a second set of new standards in 2030; these would be two separate implementation steps.
    :param costs_df: A DataFrame containing the individual tech costs for all vehicles and for each implementation step.
    :param seedvol_df: A DataFrame containing the learning-related seed volumes for all vehicles.
    :param sales_df: A DataFrame containing the sales for all vehicles.
    :param tech_apply_learning_dict: A dictionary of individual technologies by fuelTypeID that make up the package of technologies on vehicles of that fuelTypeID.
    """
    def __init__(self, _veh, step, costs_df, seedvol_df, sales_df):
        self._veh = _veh
        self.step = step
        self.costs_df = costs_df
        self.seedvol_df = seedvol_df
        self.sales_df = sales_df
        self.tech_apply_learning_common = ['EngineHardware', 'CDA']
        self.tech_apply_learning_dict = {1: self.tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
                                         2: self.tech_apply_learning_common + ['CDPF', 'DOC', 'SCR', 'HCdosing', 'Canning', 'ClosedCrankcase'],
                                         3: self.tech_apply_learning_common + ['Aftertreatment'],
                                         5: self.tech_apply_learning_common + ['Aftertreatment', 'ORVR'],
                                         9: '',
                                         }

    def __repr__(self):
        return f'DirectCost: Vehicle {self._veh}, Step {self.step}'

    def package_of_techs_on_vehicle(self):
        """

        :return: A DataFrame of the techs on the given vehicle in the given implementation step.
        """
        techs_on_veh = self.costs_df.loc[self.costs_df['alt_rc_ft'] == self._veh, ['TechPackageDescription', self.step]]
        techs_on_veh = techs_on_veh.set_index('TechPackageDescription')
        return techs_on_veh

    def cost_of_package_on_vehicle(self):
        """

        :return: A float of the summation of tech costs into a package cost for the given vehicle in the given implementation step.
        """
        pkg_cost_on_veh = 0
        tech_apply_learning = self.tech_apply_learning_dict[self._veh[2]]
        for tech in tech_apply_learning:
            pkg_cost_on_veh += self.package_of_techs_on_vehicle().at[tech, self.step]
        return pkg_cost_on_veh

    def seedvol_factor_regclass(self):
        """

        :return:  A single seed volume factor for use in calculating learning effects for the given vehicle in the given implementation step.
        """
        _pkg_seedvol_df = pd.DataFrame(self.seedvol_df.loc[self.seedvol_df['alt_rc_ft'] == self._veh, 'SeedVolumeFactor'])
        _pkg_seedvol_df.reset_index(drop=True, inplace=True)
        _pkg_seedvol = _pkg_seedvol_df['SeedVolumeFactor'][0]
        return _pkg_seedvol

    def vehicle_sales_for_step(self):
        """

        :return: A DataFrame that provides the sales_df for the given vehicle in the years following the given implementation step.
        """
        veh_sales_for_step = pd.DataFrame(self.sales_df.loc[(self.sales_df['alt_rc_ft'] == self._veh) &
                                                            (self.sales_df['modelYearID'] >= pd.to_numeric(self.step)) &
                                                            (self.sales_df['ageID'] == 0), :])
        return veh_sales_for_step

    def pkg_cost_regclass_withlearning(self, _learning_rate):
        """

        :param _learning_rate: The learning rate entered in the BCA inputs sheet.
        :return: A DataFrame of learned, year-over-year direct manufacturer package costs for the given vehicle in the given implementation step.
        """
        df = self.vehicle_sales_for_step().copy()
        df.reset_index(drop=True, inplace=True)
        # get VPOP at age0 for use in learning calc later
        vpop_age0 = pd.Series(df['VPOP'])[0]
        # insert some new columns, set to zero or empty string, then calc desired results
        new_metric_numeric = [f'Sales_RegClass-FuelType_Cumulative_{self.step}', 'SeedVolumeFactor',
                              f'DirectCost_AvgPerVeh_{self.step}']
        for metric in new_metric_numeric:
            df.insert(len(df.columns), metric, 0)
        # now calculate results for these new metrics
        df[f'Sales_RegClass-FuelType_Cumulative_{self.step}'] = df['VPOP'].cumsum()
        df['SeedVolumeFactor'] = self.seedvol_factor_regclass()
        df[f'DirectCost_AvgPerVeh_{self.step}'] = self.cost_of_package_on_vehicle() \
                                                  * (((df[f'Sales_RegClass-FuelType_Cumulative_{self.step}']
                                                       + (vpop_age0 * self.seedvol_factor_regclass()))
                                                      / (vpop_age0 + (vpop_age0 * self.seedvol_factor_regclass()))) ** _learning_rate)
        return df
