import pandas as pd
from project_code.vehicle import fuelTypeID

GRAMSperSHORTTON = 907185
GALLONSperML = 0.000264172

class DEFandFuelCost:
    """
    The OperatingCost class calculates the operating costs (DEF (urea), fuel, etc.).

    :param input_df: A DataFrame that provides the necessary physical parameters.
    """

    def __init__(self, input_df):
        self.input_df = input_df

    def def_doserate_scaling_factor(self):
        """

        :return: A DataFrame of dose rate scaling factors to apply to fuel consumption in calculating urea operating costs.
        """
        def_doserates = self.input_df.copy()
        def_doserates.insert(len(def_doserates.columns), 'DEFDoseRate_PercentOfFuel', 0)
        def_doserates['DEFDoseRate_PercentOfFuel'] = ((def_doserates['standard_NOx'] - def_doserates['engineout_NOx'])
                                                      - def_doserates['intercept_DEFdoserate']) \
                                                     / def_doserates['slope_DEFdoserate']
        def_doserates.drop(columns=['engineout_NOx', 'standard_NOx', 'intercept_DEFdoserate', 'slope_DEFdoserate'], inplace=True)
        return def_doserates

    def def_cost_df(self, def_doserates, prices):
        """

        :param def_doserates: A DataFrame of DEF scaling factors (dose rate inputs).
        :param prices: A DataFrame of DEF prices.
        :return: The passed DataFrame after adding the DEF operating cost metrics:
                ['DoseRate_PercentOfFuel', 'DEF_USDperGal', 'OperatingCost_Urea_TotalCost']
        """
        df = self.input_df.copy()
        df = df.merge(def_doserates, on=['optionID', 'modelYearID', 'regClassID', 'fuelTypeID'], how='left')
        df['DEFDoseRate_PercentOfFuel'].fillna(method='ffill', inplace=True)
        df.loc[df['fuelTypeID'] != 2, 'DEFDoseRate_PercentOfFuel'] = 0
        df['DEFDoseRate_PercentOfFuel'].fillna(0, inplace=True)
        df = df.merge(prices, on='yearID', how='left')
        df.insert(len(df.columns), 'UreaCost_TotalCost', df[['Gallons', 'DEFDoseRate_PercentOfFuel', 'DEF_USDperGal']].product(axis=1))
        df.insert(len(df.columns), 'UreaCost_AvgPerMile', df['UreaCost_TotalCost'] / df['VMT'])
        return df

    def orvr_fuel_impacts_pct(self, _fuelchanges):
        """

        :param _fuelchanges: A DataFrame of the adjustments to the MOVES run values to account for fuel impacts not captured in MOVES.
        :return: The passed DataFrame after adding the fuel consumption metrics:
                ['Change_PercentOfFuel', 'Gallons' (adjusted)]
        """
        _fuelchanges.drop(columns='ml/g', inplace=True)
        df = self.input_df.copy()
        df = df.merge(_fuelchanges, on=['optionID', 'fuelTypeID'], how='left')
        df['Change_PercentOfFuel'].fillna(0, inplace=True)
        df['Gallons'] = df['Gallons'] * (1 + df['Change_PercentOfFuel'])
        return df

    def orvr_fuel_impacts_mlpergram(self, orvr_fuelchanges):
        """

        :param orvr_fuelchanges: A DataFrame of the adjustments to the MOVES run values to account for fuel impacts not captured in MOVES.
        :return: The passed DataFrame after adding the fuel consumption metrics:
                ['Change_PercentOfFuel', 'Gallons' (adjusted)]
        """
        fuelchanges = orvr_fuelchanges.copy()
        fuelchanges.drop(columns='Change_PercentOfFuel', inplace=True)
        df = self.input_df.copy()
        df2 = pd.DataFrame(df.loc[df['optionID'] == 0, ['yearID', 'modelYearID', 'ageID', 'sourcetypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID', 'THC (US tons)']])
        df2.rename(columns={'THC (US tons)': 'THC_Option0'}, inplace=True)
        df = df.merge(df2, on=['yearID', 'modelYearID', 'ageID', 'sourcetypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID'], how='left')
        df.insert(len(df.columns), 'THC_delta', df['THC (US tons)'] - df['THC_Option0'])
        df = df.merge(fuelchanges, on=['optionID', 'regClassID', 'fuelTypeID'], how='left')
        df['ml/g'].fillna(0, inplace=True)
        df['Gallons'] = df['Gallons'] + df['THC_delta'] * df['ml/g'] * GRAMSperSHORTTON * GALLONSperML
        df.drop(columns=['THC_Option0'], inplace=True)
        return df

    def fuel_costs(self, _prices):
        """

        :param _prices:  A DataFrame of the fuel prices being used for the given run.
        :return: The passed DataFrame after adding the fuel cost metrics:
                 ['pretax_fuelprice', 'retail_fuelprice', 'OperatingCost_Fuel_Pretax_TotalCost', 'OperatingCost_Fuel_Retail_TotalCost']
        """
        df = self.input_df.copy()
        prices_gasoline = pd.DataFrame(_prices, columns=['yearID', 'gasoline_retail', 'gasoline_pretax'])
        prices_diesel = pd.DataFrame(_prices, columns=['yearID', 'diesel_retail', 'diesel_pretax'])
        prices_gasoline.rename(columns={'gasoline_retail': 'retail_fuelprice', 'gasoline_pretax': 'pretax_fuelprice'}, inplace=True)
        prices_diesel.rename(columns={'diesel_retail': 'retail_fuelprice', 'diesel_pretax': 'pretax_fuelprice'}, inplace=True)
        id_gasoline = [k for k, v in fuelTypeID.items() if v == 'Gasoline'][0] # this determines the fuelTypeID of Gasoline
        id_diesel = [k for k, v in fuelTypeID.items() if v == 'Diesel'][0] # this determines the fuelTypeID of Diesel
        prices_gasoline.insert(0, 'fuelTypeID', id_gasoline)
        prices_diesel.insert(0, 'fuelTypeID', id_diesel)
        prices = pd.concat([prices_gasoline, prices_diesel], ignore_index=True)
        df = df.merge(prices, on=['yearID', 'fuelTypeID'], how='left')
        df['pretax_fuelprice'].fillna(method='ffill', inplace=True)
        df['retail_fuelprice'].fillna(method='ffill', inplace=True)
        df.insert(len(df.columns), 'FuelCost_Pretax_TotalCost', df[['Gallons', 'pretax_fuelprice']].product(axis=1))
        df.insert(len(df.columns), 'FuelCost_Retail_TotalCost', df[['Gallons', 'retail_fuelprice']].product(axis=1))
        df.insert(len(df.columns), 'FuelCost_Retail_AvgPerMile', df['FuelCost_Retail_TotalCost'] / df['VMT'])
        return df


class RepairAndMaintenanceCost:
    """
        The RepairAndMaintenance class calculates the repair & maintenance costs.

        :param passed_object: A DataFrame that provides the necessary physical parameters; or a vehicle tuple.
        """
    def __init__(self, passed_object):
        self.passed_object = passed_object

    def repair_and_maintenance_costs_byAge(self, repair_and_maintenance_cpm):
        """

        :param repair_and_maintenance_cpm: A DataFrame of cost per mile input values by ageID.
        :return: The passed DataFrame (which must contain vehicles and vehicle ageID) with maintenance & repair costs along with emission-related maintenance & repair costs added in.
        """
        return_df = self.passed_object.copy()
        # cost_per_mile_df = pd.DataFrame(return_df, columns=['optionID', 'regClassID', 'fuelTypeID', 'ageID'])
        repair_and_maintenance_cpm.insert(0, 'emission_repair_cpm',
                                          repair_and_maintenance_cpm['emission_share']
                                          * repair_and_maintenance_cpm['repair_share']
                                          * repair_and_maintenance_cpm['maintenance_and_repair_cpm'])
        return_df = return_df.merge(repair_and_maintenance_cpm[['ageID', 'maintenance_and_repair_cpm', 'emission_repair_cpm']], on=['ageID'])
        return_df.insert(len(return_df.columns), 'MaintenanceAndRepairCost_TotalCost', return_df['VMT'] * return_df['maintenance_and_repair_cpm'])
        return_df.insert(len(return_df.columns), 'EmissionRepairCost_TotalCost', return_df['VMT'] * return_df['emission_repair_cpm'])
        return_df.insert(len(return_df.columns), 'MaintenanceAndRepairCost_AvgPerVeh', return_df['VMT_AvgPerVeh'] * return_df['maintenance_and_repair_cpm'])
        return_df.insert(len(return_df.columns), 'EmissionRepairCost_AvgPerVeh', return_df['VMT_AvgPerVeh'] * return_df['emission_repair_cpm'])
        return return_df

    def repair_and_maintenance_costs_curve(self, metrics_repair_and_maint_dict):
        df_return = self.passed_object.copy()
        emission_repair_share = metrics_repair_and_maint_dict['repair_and_maintenance_emission_share'] \
                                * metrics_repair_and_maint_dict['repair_and_maintenance_repair_share']
        vehicles = set(df_return['alt_rc_ft'])
        df_return.insert(len(df_return.columns), 'EmissionRepairCost_AvgPerMile', 0)
        for veh in vehicles:
            if veh[2] == 1:
                scalar = metrics_repair_and_maint_dict['scalar_gasoline']
            else:
                scalar = 1
            df_return.loc[(df_return['alt_rc_ft'] == veh)
                          & (df_return['VMT_AvgPerVeh_CumSum'] <= df_return['Warranty_Miles']),
                          'EmissionRepairCost_AvgPerMile'] \
                = metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_cpm'] \
                  * scalar \
                  * emission_repair_share
            df_return.loc[(df_return['alt_rc_ft'] == veh)
                          & (df_return['VMT_AvgPerVeh_CumSum'] > df_return['Warranty_Miles'])
                          & (df_return['VMT_AvgPerVeh_CumSum'] <= df_return['UsefulLife_Miles']),
                          'EmissionRepairCost_AvgPerMile'] \
                = ((df_return['VMT_AvgPerVeh_CumSum'] - df_return['Warranty_Miles'])
                    * metrics_repair_and_maint_dict['slope_repair_and_maintenance_cpm']
                    + metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_cpm']) \
                  * scalar \
                  * emission_repair_share
            df_return.loc[(df_return['alt_rc_ft'] == veh)
                          & (df_return['VMT_AvgPerVeh_CumSum'] > df_return['UsefulLife_Miles']),
                          'EmissionRepairCost_AvgPerMile'] \
                = ((df_return['UsefulLife_Miles'] - df_return['Warranty_Miles'])
                    * metrics_repair_and_maint_dict['slope_repair_and_maintenance_cpm']
                    + metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_cpm']) \
                  * scalar \
                  * emission_repair_share \
                  * (1 + metrics_repair_and_maint_dict['repair_and_maintenance_increase_beyond_usefullife'])
        df_return.insert(len(df_return.columns), 'EmissionRepairCost_AvgPerVeh', df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_AvgPerMile'])
        df_return.insert(len(df_return.columns), 'EmissionRepairCost_TotalCost', df_return['VMT'] * df_return['EmissionRepairCost_AvgPerMile'])
        return df_return

    def repair_and_maintenance_costs_curve2(self, metrics_repair_and_maint_dict):
        df_return = self.passed_object.copy()
        emission_repair_share = metrics_repair_and_maint_dict['repair_and_maintenance_emission_share'] \
                                * metrics_repair_and_maint_dict['repair_and_maintenance_repair_share']
        vehicles = set(df_return['alt_rc_ft'])
        # df_return.insert(len(df_return.columns), 'EmissionRepairCost_AvgPerMile', 0)
        df_return.insert(len(df_return.columns), 'EmissionRepairCost_OwnerOperator_AvgPerMile', 0)
        df_return.insert(len(df_return.columns), 'EmissionRepairCost_OEM_AvgPerMile', 0)
        # determine emission repair cost per mile
        # df_return['EmissionRepairCost_AvgPerMile'] =
        for veh in vehicles:
            if veh[2] == 1:
                scalar = metrics_repair_and_maint_dict['scalar_gasoline']
            else:
                scalar = 1
            for model_year in range(df_return['modelYearID'].min(), df_return['modelYearID'].max() + 1):
                warranty_miles = df_return.loc[(df_return['alt_rc_ft'] == veh) & (df_return['modelYearID'] == model_year), 'Warranty_Miles'].mean()
                usefullife_miles = df_return.loc[(df_return['alt_rc_ft'] == veh) & (df_return['modelYearID'] == model_year), 'UsefulLife_Miles'].mean()
                slope = ((metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_ownop_cpm'] - metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_ownop_cpm'])
                         / (usefullife_miles - warranty_miles)) \
                         * scalar
                # determine in-warranty cost per mile for OEM
                df_return.loc[(df_return['alt_rc_ft'] == veh) & (df_return['modelYearID'] == model_year)
                              & (df_return['VMT_AvgPerVeh_CumSum'] <= df_return['Warranty_Miles'])
                              & (df_return['ageID'] + 1 <= df_return['UsefulLife_Age']), # ageID <= useful life here due to low VMT vehicles
                              'EmissionRepairCost_OEM_AvgPerMile'] \
                    = metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_oem_cpm'] \
                      * scalar * emission_repair_share
                # determine "in-warranty" cost per mile for owner/operator
                df_return.loc[(df_return['alt_rc_ft'] == veh) & (df_return['modelYearID'] == model_year)
                              & (df_return['VMT_AvgPerVeh_CumSum'] <= df_return['Warranty_Miles']),
                              'EmissionRepairCost_OwnerOperator_AvgPerMile'] \
                    = 0
                # determine out-of-warranty but within-usefule-life cost per mile for owner/operator (this case is 0 for OEM)
                df_return.loc[(df_return['alt_rc_ft'] == veh) & (df_return['modelYearID'] == model_year)
                              & (df_return['VMT_AvgPerVeh_CumSum'] > df_return['Warranty_Miles'])
                              & (df_return['VMT_AvgPerVeh_CumSum'] <= df_return['UsefulLife_Miles']),
                              'EmissionRepairCost_OwnerOperator_AvgPerMile'] \
                    = ((df_return['VMT_AvgPerVeh_CumSum'] - df_return['Warranty_Miles'])
                        * slope
                        + metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_ownop_cpm']) \
                      * scalar \
                      * emission_repair_share
                # determine beyond-useful-life cost per mile for owner/operator (this case is 0 for OEM)
                df_return.loc[(df_return['alt_rc_ft'] == veh) & (df_return['modelYearID'] == model_year)
                              & ((df_return['VMT_AvgPerVeh_CumSum'] > df_return['UsefulLife_Miles'])
                                 | (df_return['ageID'] + 1 > df_return['UsefulLife_Age'])),
                              'EmissionRepairCost_OwnerOperator_AvgPerMile'] \
                    = metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_ownop_cpm'] \
                      * scalar \
                      * emission_repair_share \
                      * (1 + metrics_repair_and_maint_dict['repair_and_maintenance_increase_beyond_usefullife'])
                # set beyond-warranty cost per mile for OEM to 0
                df_return['EmissionRepairCost_OEM_AvgPerMile'].fillna(0, inplace=True)
        # set baseline max CPM as the max CPM for each alternative
        for veh in vehicles:
            baseline_veh = (0, veh[1], veh[2])
            max_cpm_baseline = df_return.loc[df_return['alt_rc_ft'] == baseline_veh, 'EmissionRepairCost_OwnerOperator_AvgPerMile'].max()
            df_return.loc[(df_return['alt_rc_ft'] == veh)
                          & (df_return['EmissionRepairCost_OwnerOperator_AvgPerMile'] > max_cpm_baseline),
                          'EmissionRepairCost_OwnerOperator_AvgPerMile'] \
                = max_cpm_baseline
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_OwnerOperator_AvgPerVeh',
                         df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_OwnerOperator_AvgPerMile'])
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_OEM_AvgPerVeh',
                         df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_OEM_AvgPerMile'])
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_OwnerOperator_TotalCost',
                         df_return['VMT'] * df_return['EmissionRepairCost_OwnerOperator_AvgPerMile'])
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_OEM_TotalCost',
                         df_return['VMT'] * df_return['EmissionRepairCost_OEM_AvgPerMile'])
        return df_return
