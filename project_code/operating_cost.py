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
        def_doserates.insert(len(def_doserates.columns), 'DEF_PercentOfFuel_Baseline', 0)
        def_doserates['DEF_PercentOfFuel_Baseline'] = ((def_doserates['standard_NOx'] - def_doserates['engineout_NOx'])
                                                      - def_doserates['intercept_DEFdoserate']) \
                                                     / def_doserates['slope_DEFdoserate']
        def_doserates.drop(columns=['engineout_NOx', 'standard_NOx', 'intercept_DEFdoserate', 'slope_DEFdoserate'], inplace=True)
        return def_doserates

    def def_cost_df(self, def_doserates, prices, def_gallons_perTonNOxReduction):
        """

        :param def_doserates: A DataFrame of DEF scaling factors (dose rate inputs).
        :param prices: A DataFrame of DEF prices.
        :param def_gallons_perTonNOxReduction: The gallons of DEF consumed for each ton of NOx reduced
        :return: The passed DataFrame after adding the DEF operating cost metrics:
                ['DoseRate_PercentOfFuel', 'DEF_USDperGal', 'OperatingCost_Urea_TotalCost']
        """
        df = self.input_df.copy()
        df = df.merge(def_doserates, on=['modelYearID', 'regClassID', 'fuelTypeID'], how='left')
        # df = df.merge(def_doserates, on=['optionID', 'modelYearID', 'regClassID', 'fuelTypeID'], how='left')
        vehs = set(df['alt_rc_ft'])
        # since the merge of DEF dose rates is only for select MYs and alt_rc_ft vehicles, filling in for other ages/years has to be done via the following two loops
        for veh in vehs:
            df.loc[(df['alt_rc_ft'] == veh) & (df['ageID'] == 0), 'DEF_PercentOfFuel_Baseline'] \
                = df.loc[(df['alt_rc_ft'] == veh) & (df['ageID'] == 0), 'DEF_PercentOfFuel_Baseline'].ffill(axis=0)
        for veh in vehs:
            for year in range(df['modelYearID'].min(), df['modelYearID'].max() + 1):
                df.loc[(df['alt_rc_ft'] == veh) & (df['modelYearID'] == year), 'DEF_PercentOfFuel_Baseline'] \
                    = df.loc[(df['alt_rc_ft'] == veh) & (df['modelYearID'] == year), 'DEF_PercentOfFuel_Baseline'].ffill(axis=0)
        # set non-diesel dose rates to zero and any NaNs to zero just for certainty
        df.loc[df['fuelTypeID'] != 2, 'DEF_PercentOfFuel_Baseline'] = 0
        df['DEF_PercentOfFuel_Baseline'].fillna(0, inplace=True)
        df.insert(len(df.columns), 'Gallons_DEF', 0)
        df.loc[df['fuelTypeID'] == 2, 'Gallons_DEF'] = df['Gallons'] * df['DEF_PercentOfFuel_Baseline'] + df['NOx_onroad_Reductions'] * def_gallons_perTonNOxReduction
        df = df.merge(prices, on='yearID', how='left')
        df.insert(len(df.columns), 'UreaCost_TotalCost', df[['Gallons_DEF', 'DEF_USDperGal']].product(axis=1))
        df.insert(len(df.columns), 'UreaCost_AvgPerMile', df['UreaCost_TotalCost'] / df['VMT'])
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
        df2 = pd.DataFrame(df.loc[df['optionID'] == 0, ['yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID', 'THC_UStons']])
        df2.rename(columns={'THC_UStons': 'THC_Option0'}, inplace=True)
        df = df.merge(df2, on=['yearID', 'modelYearID', 'ageID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID'], how='left')
        df.insert(len(df.columns), 'THC_delta', df['THC_UStons'] - df['THC_Option0'])
        df = df.merge(fuelchanges, on=['optionID', 'regClassID', 'fuelTypeID'], how='left')
        df['ml/g'].fillna(0, inplace=True)
        df['Gallons'] = df['Gallons'] + df['THC_delta'] * df['ml/g'] * GRAMSperSHORTTON * GALLONSperML
        df.drop(columns=['THC_Option0'], inplace=True)
        return df

    def fuel_costs(self, prices):
        """

        :param prices:  A DataFrame of the fuel prices being used for the given run.
        :return: The passed DataFrame after adding the fuel cost metrics:
                 ['pretax_fuelprice', 'retail_fuelprice', 'OperatingCost_Fuel_Pretax_TotalCost', 'OperatingCost_Fuel_Retail_TotalCost']
        """
        df = self.input_df.copy()
        prices_gasoline = pd.DataFrame(prices, columns=['yearID', 'gasoline_retail', 'gasoline_pretax'])
        prices_diesel = pd.DataFrame(prices, columns=['yearID', 'diesel_retail', 'diesel_pretax'])
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

    :param passed_object: A DataFrame that provides the necessary physical parameters: a vehicle tuple; cumulative VMT/veh/year;
                          estimated ages when warranty & useful life is reached.
    :param metrics_repair_and_maint_dict: The repair and maintenance cost curve inputs contained in the inputs folder; the dictionary is created in code
    :param pkg_directcost_veh_regclass_dict: The dictionary of package direct costs, year-over-year, created in code
    """
    def __init__(self, passed_object, metrics_repair_and_maint_dict, pkg_directcost_veh_regclass_dict):
        self.passed_object = passed_object
        self.metrics_repair_and_maint_dict = metrics_repair_and_maint_dict
        self.pkg_directcost_veh_regclass_dict = pkg_directcost_veh_regclass_dict

    def emission_repair_costs(self):
        """

        :return: The passed DataFrame (operating_costs expected) with emission repair metrics included (cost/mile, cost/veh, total costs)
        """

        df_temp = self.passed_object.copy()
        vehicles = pd.Series(df_temp['alt_st_rc_ft']).unique()
        repair_cost_dict = dict()
        for veh in vehicles:
            print(f'Working on repair costs for {veh}')
            index_loc = 0
            for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
                repair_cost_dict[veh, model_year] = pd.DataFrame(df_temp.loc[((df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year)), :])
                # first determine the ratio of direct costs of the veh to direct costs of (0, 47, 2)
                veh_regclass = (veh[0], veh[2], veh[3])
                direct_cost_scalar = self.pkg_directcost_veh_regclass_dict[veh_regclass].loc[self.pkg_directcost_veh_regclass_dict[veh_regclass]['modelYearID'] == model_year, 'DirectCost_AvgPerVeh'][index_loc] / \
                                     self.pkg_directcost_veh_regclass_dict[0, 47, 2].loc[self.pkg_directcost_veh_regclass_dict[0, 47, 2]['modelYearID'] == model_year, 'DirectCost_AvgPerVeh'][index_loc]
                warranty_age = df_temp.loc[(df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year), 'EstimatedAge_Warranty'].mean()
                usefullife_age = df_temp.loc[(df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year), 'EstimatedAge_UsefulLife'].mean()
                if usefullife_age != warranty_age:
                    slope_within_usefullife = (self.metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_owner_cpm'] - self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm']) \
                                               * direct_cost_scalar \
                                               * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                                              / (usefullife_age - warranty_age)
                else:
                    slope_within_usefullife = (self.metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_owner_cpm'] - self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm']) \
                                               * direct_cost_scalar \
                                               * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                                              / (usefullife_age - 1)
                max_cpm = self.metrics_repair_and_maint_dict['max_repair_and_maintenance_cpm'] \
                          * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                          * direct_cost_scalar
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'direct_cost_scalar', direct_cost_scalar)
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'slope_within_usefullife', slope_within_usefullife)
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'max_cpm', max_cpm)
                # determine in-warranty cost per mile
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'EmissionRepairCost_Owner_AvgPerMile',
                                                         self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm']
                                                         * self.metrics_repair_and_maint_dict['emission_repair_share']
                                                         * direct_cost_scalar)
                # determine out-of-warranty but within-useful-life cost per mile for owner
                repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] + 1 > warranty_age), 'EmissionRepairCost_Owner_AvgPerMile'] \
                    = slope_within_usefullife * repair_cost_dict[veh, model_year]['ageID'] \
                      + self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm']\
                      * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                      * direct_cost_scalar
                # determine beyond-useful-life cost per mile for owner
                repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] + 1 > usefullife_age),
                                                      'EmissionRepairCost_Owner_AvgPerMile'] \
                    = max_cpm
                # set max_cpm as the max for any calculated using slopes that may have exceeded max
                repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['EmissionRepairCost_Owner_AvgPerMile'] > max_cpm),
                                                      'EmissionRepairCost_Owner_AvgPerMile'] \
                    = max_cpm
                index_loc += 1
        df_return = pd.DataFrame()
        for veh in vehicles:
            for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
                df_return = pd.concat([df_return, repair_cost_dict[veh, model_year]], axis=0, ignore_index=True)
        df_return.reset_index(drop=True, inplace=True)
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_Owner_AvgPerVeh',
                         df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_Owner_TotalCost',
                         df_return['VMT'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
        return df_return


    def emission_repair_costs2(self):
        """

        :return: The passed DataFrame (operating_costs expected) with emission repair metrics included (cost/mile, cost/veh, total costs)
        """

        df_temp = self.passed_object.copy()
        vehicles = pd.Series(df_temp['alt_st_rc_ft']).unique()
        repair_cost_dict = dict()
        for veh in vehicles:
            print(f'Working on repair costs for {veh}')
            index_loc = 0
            for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
                repair_cost_dict[veh, model_year] = pd.DataFrame(df_temp.loc[((df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year)), :])
                # first determine the ratio of direct costs of the veh to direct costs of (0, 47, 2)
                veh_regclass = (veh[0], veh[2], veh[3])
                direct_cost_scalar = self.pkg_directcost_veh_regclass_dict[veh_regclass].loc[
                                         self.pkg_directcost_veh_regclass_dict[veh_regclass]['modelYearID'] == model_year,
                                         'DirectCost_AvgPerVeh'][index_loc] \
                                     / self.pkg_directcost_veh_regclass_dict[0, 47, 2].loc[
                                         self.pkg_directcost_veh_regclass_dict[0, 47, 2]['modelYearID'] == model_year,
                                         'DirectCost_AvgPerVeh'][index_loc]
                warranty_age = df_temp.loc[(df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year), 'EstimatedAge_Warranty'].mean()
                usefullife_age = df_temp.loc[(df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year), 'EstimatedAge_UsefulLife'].mean()
                in_warranty_cpm = self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm'] \
                                  * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                                  * direct_cost_scalar
                at_usefullife_cpm = self.metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_owner_cpm'] \
                                    * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                                    * direct_cost_scalar
                if usefullife_age > warranty_age:
                    slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) / (usefullife_age - warranty_age)
                else:
                    slope_within_usefullife = 0
                max_cpm = self.metrics_repair_and_maint_dict['max_repair_and_maintenance_cpm'] \
                          * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                          * direct_cost_scalar
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'direct_cost_scalar', direct_cost_scalar)
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'slope_within_usefullife', slope_within_usefullife)
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'max_cpm', max_cpm)
                # determine in-warranty cost per mile
                repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'EmissionRepairCost_Owner_AvgPerMile',
                                                         in_warranty_cpm)
                # determine out-of-warranty but within-useful-life cost per mile for owner
                repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] > (warranty_age - 1)), 'EmissionRepairCost_Owner_AvgPerMile'] \
                    = slope_within_usefullife * (repair_cost_dict[veh, model_year]['ageID'] - (warranty_age - 1)) \
                      + in_warranty_cpm
                # determine at-usefullife cost per mile
                repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] >= (usefullife_age - 1)), 'EmissionRepairCost_Owner_AvgPerMile'] \
                    = at_usefullife_cpm
                # determine beyond-useful-life cost per mile for owner
                repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] > (usefullife_age - 1)),
                                                      'EmissionRepairCost_Owner_AvgPerMile'] \
                    = max_cpm
                index_loc += 1
        df_return = pd.DataFrame()
        for veh in vehicles:
            for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
                df_return = pd.concat([df_return, repair_cost_dict[veh, model_year]], axis=0, ignore_index=True)
        df_return.reset_index(drop=True, inplace=True)
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_Owner_AvgPerVeh',
                         df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_Owner_TotalCost',
                         df_return['VMT'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
        return df_return