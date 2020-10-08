"""
operating_cost.py

Contains the DEFCost, ORVRadjust, FuelCost and RepairAndMaintenanceCost classes.

"""

import pandas as pd
from itertools import product
from project_code.vehicle import fuelTypeID
import project_code.general_functions as gen_fxns

grams_per_short_ton = 907185
gallons_per_ml = 0.000264172


def get_reductions(inventory_df, *args):
    """

    :param inventory_df:
    :param args:
    :return: The passed DataFrame with metrics in list_for_deltas showing as reductions from baseline rather than the values contained in the passed DataFrame
    """
    alts = pd.Series(inventory_df['optionID'].unique())
    for arg in args:
        alternative = dict()
        alternative[0] = pd.DataFrame(inventory_df.loc[inventory_df['optionID'] == 0, arg])
        alternative[0].reset_index(drop=True, inplace=True)
        alternative['all'] = alternative[0].copy()
        for alt in range(1, len(alts)):
            alternative[alt] = pd.DataFrame(inventory_df.loc[inventory_df['optionID'] == alt, arg])
            alternative[alt].reset_index(drop=True, inplace=True)
            alternative[alt][arg] = alternative[0][arg] - alternative[alt][arg]
            alternative['all'] = alternative['all'].append(alternative[alt], ignore_index=True, sort=False)
        inventory_df.insert(inventory_df.columns.get_loc(f'{arg}') + 1, f'{arg}_Reductions', alternative['all'][arg])
        inventory_df.loc[inventory_df['optionID'] == 0, f'{arg}_Reductions'] = 0
    return inventory_df


class DEFCost:
    """

    The DEFCost class calculates the DEF (urea) costs.
    """
    def __init__(self, _veh, cost_steps, inventory_df, def_doserate_inputs, def_gallons_per_ton_nox_reduction, def_prices):
        """

        :param _veh: A sourcetype_regclass_fueltype (st_rc_ft) vehicle.
        :param cost_steps:
        :param inventory_df:
        :param def_doserate_inputs:
        :param def_gallons_per_ton_nox_reduction
        :param def_prices
        """
        self._veh = _veh
        self.cost_steps = cost_steps
        self.inventory_df = inventory_df
        self.def_doserate_inputs = def_doserate_inputs
        self.def_gallons_per_ton_nox_reduction = def_gallons_per_ton_nox_reduction
        self.def_prices = def_prices

    def __repr__(self):
        return f'DEFCost: Vehicle {self._veh}'

    def def_doserate_scaling_factor(self, step):
        """

        :param step:
        :return: The DEF dose rate scaling factor to apply to fuel consumption in calculating urea operating costs for the given vehicle in the given step.
        """
        def_doserates = pd.DataFrame(self.def_doserate_inputs.loc[(self.def_doserate_inputs['regClassID'] == self._veh[2]) &
                                                                  (self.def_doserate_inputs['modelYearID'] == step), :])
        def_doserates.reset_index(drop=True, inplace=True)
        def_doserate = ((def_doserates['standard_NOx'] - def_doserates['engineout_NOx']) -
                        def_doserates['intercept_DEFdoserate']) / def_doserates['slope_DEFdoserate']
        def_doserate = def_doserate.at[0]
        return def_doserate

    def insert_def_doserate(self):
        """

        :return:
        """
        self.inventory_df.insert(len(self.inventory_df.columns), 'DEF_PercentOfFuel_Baseline', 0)
        for step_number in range(len(self.cost_steps)):
            step = int(self.cost_steps[step_number])
            self.inventory_df.loc[self.inventory_df['modelYearID'] >= step, 'DEF_PercentOfFuel_Baseline'] \
                = self.def_doserate_scaling_factor(step)
        return self.inventory_df

    def calc_gallons_def(self, gallons_df):
        """

        :return:
        """
        self.inventory_df = self.insert_def_doserate()
        # self.inventory_df = get_reductions(self.inventory_df, 'NOx_onroad')
        # self.inventory_df = self.get_reductions('NOx_onroad')
        self.inventory_df.insert(len(self.inventory_df.columns), 'Gallons_DEF', 0)
        self.inventory_df['Gallons_DEF'] = gallons_df['Gallons'] * self.inventory_df['DEF_PercentOfFuel_Baseline'] \
                                           + self.inventory_df['NOx_onroad_Reductions'] * self.def_gallons_per_ton_nox_reduction
        return self.inventory_df

    def calc_def_costs(self, gallons_df, vmt_df, per_veh_df):
        """

        :return:
        """
        self.inventory_df = self.inventory_df.merge(self.def_prices, on='yearID', how='left')
        self.inventory_df.drop(columns='DollarBasis', inplace=True)
        self.inventory_df = self.calc_gallons_def(gallons_df)
        self.inventory_df.insert(len(self.inventory_df.columns),
                                 'DEFCost_TotalCost',
                                 self.inventory_df[['Gallons_DEF', 'DEF_USDperGal']].product(axis=1))
        self.inventory_df.insert(len(self.inventory_df.columns),
                                 'DEFCost_AvgPerMile',
                                 self.inventory_df['DEFCost_TotalCost'] / vmt_df['VMT'])
        self.inventory_df.insert(len(self.inventory_df.columns),
                                 'DEFCost_AvgPerVeh',
                                 self.inventory_df['DEFCost_AvgPerMile'] * per_veh_df['VMT_AvgPerVeh'])
        return self.inventory_df


class ORVRadjust:
    """

    The ORVRadjust class adjusts the MOVES THC inventories and then gallons based on the ORVR impacts on THC emissions.
    """

    def __init__(self, _vehs, orvr_fuelchanges, gallons_df, inventory_df, vmt_df):
        """

        :param _vehs:
        :param orvr_fuelchanges:
        :param gallons_df:
        :param inventory_df:
        :param vmt_df:
        """
        self._vehs = _vehs
        self.orvr_fuelchanges = orvr_fuelchanges
        self.gallons_df = gallons_df
        self.inventory_df = inventory_df
        self.vmt_df = vmt_df

    def __repr__(self):
        return 'ORVR adjustments being made.'

    def get_orvr_impact(self, veh, alt):
        """

        :param veh:
        :param alt:
        :return:
        """
        impact = pd.DataFrame(self.orvr_fuelchanges.loc[(self.orvr_fuelchanges['optionID'] == alt) &
                                                        (self.orvr_fuelchanges['regClassID'] == veh[2]), 'ml/g'])
        impact.reset_index(drop=True, inplace=True)
        impact = impact.at[0, 'ml/g']
        return impact

    def adjust_gallons(self):
        """

        :return:
        """
        alts = pd.Series(self.gallons_df['optionID'].unique())
        self.gallons_df.insert(len(self.gallons_df.columns), 'ml/g', 0)
        for veh in self._vehs:
            if veh[3] == 1:
                print(f'Adjusting gallons associated with ORVR: Vehicle {veh}')
                for alt in alts:
                    self.gallons_df.loc[self.gallons_df['alt_st_rc_ft'] == veh, 'ml/g'] = self.get_orvr_impact(veh, alt)
            else:
                self.gallons_df.loc[self.gallons_df['alt_st_rc_ft'] == veh, 'ml/g'] = 0
        self.gallons_df['Gallons'] \
            = self.gallons_df['Gallons'] \
              - self.inventory_df['THC_UStons_Reductions'] * self.gallons_df['ml/g'] * grams_per_short_ton * gallons_per_ml
        return self.gallons_df

    def adjust_mpg(self, per_veh_df):
        """

        :param per_veh_df:
        :return:
        """
        per_veh_df['MPG_AvgPerVeh'] = self.vmt_df['VMT'] / self.gallons_df['Gallons']
        return per_veh_df


class FuelCost:
    """
    The FuelCost class calculates the monetized fuel impacts.
    """
    def __init__(self, vehs, inventory_df, vmt_df, per_veh_df, fuel_prices):
        """

        :param vehs: List of vehicles.
        :param inventory_df: DataFrame with inventory (gallons) for all vehicles.
        :param vmt_df: DataFrame with VMT for all vehicles.
        :param per_veh_df: DataFrame with VMT/veh for all vehicles.
        :param fuel_prices: DataFrame of fuel prices for all fuels for all years.
        """
        self.vehs = vehs
        self.inventory_df = inventory_df
        self.fuel_prices = fuel_prices
        self.vmt_df = vmt_df
        self.per_veh_df = per_veh_df

    def veh_inventory(self, veh):
        return self.inventory_df.loc[self.inventory_df['alt_st_rc_ft'] == veh, ['static_id', 'yearID', 'Gallons']].reset_index(drop=True)

    def veh_vmt(self, veh):
        return self.vmt_df.loc[self.vmt_df['alt_st_rc_ft'] == veh, 'VMT'].reset_index(drop=True)

    def veh_vmt_per_veh(self, veh):
        return self.per_veh_df.loc[self.per_veh_df['alt_st_rc_ft'] == veh, 'VMT_AvgPerVeh'].reset_index(drop=True)

    def veh_fuel_prices(self, veh):
        cols = [col for col in self.fuel_prices.columns if 'fuel_price' in col]
        return self.fuel_prices.loc[self.fuel_prices['fuelTypeID'] == veh[3], ['yearID'] + cols]

    def calc_fuel_costs(self):
        """

        :return:
        """
        fuel_cost_dict = dict()
        fuel_cost_df = pd.DataFrame()
        for veh in self.vehs:
            print(f'Calculating fuel costs: Vehicle {veh}')
            fuel_cost_dict[veh] = self.veh_inventory(veh)\
                .merge(self.veh_fuel_prices(veh),
                       on=gen_fxns.get_common_metrics(self.veh_inventory(veh), self.veh_fuel_prices(veh)),
                       how='left')
            # self.inventory_df = self.inventory_df.merge(self.fuel_prices, on=['yearID', 'fuelTypeID'], how='left')
            fuel_cost_dict[veh].insert(len(fuel_cost_dict[veh].columns),
                                       'FuelCost_Pretax_TotalCost',
                                       fuel_cost_dict[veh][['Gallons', 'pretax_fuel_price']].product(axis=1))
            fuel_cost_dict[veh].insert(len(fuel_cost_dict[veh].columns),
                                       'FuelCost_Retail_TotalCost',
                                       fuel_cost_dict[veh][['Gallons', 'retail_fuel_price']].product(axis=1))
            # self.inventory_df.insert(len(self.inventory_df.columns),
            #                          'FuelCost_Pretax_TotalCost',
            #                          self.inventory_df[['Gallons', 'pretax_fuel_price']].product(axis=1))
            # self.inventory_df.insert(len(self.inventory_df.columns),
            #                          'FuelCost_Retail_TotalCost',
            #                          self.inventory_df[['Gallons', 'retail_fuel_price']].product(axis=1))
            fuel_cost_dict[veh].insert(len(fuel_cost_dict[veh].columns),
                                       'FuelCost_Retail_AvgPerMile',
                                       fuel_cost_dict[veh]['FuelCost_Retail_TotalCost'] / self.veh_vmt(veh))
            fuel_cost_dict[veh].insert(len(fuel_cost_dict[veh].columns),
                                       'FuelCost_Retail_AvgPerVeh',
                                       fuel_cost_dict[veh]['FuelCost_Retail_AvgPerMile'] * self.veh_vmt_per_veh(veh))
            fuel_cost_dict[veh].drop(columns='Gallons', inplace=True)
            fuel_cost_df = pd.concat([fuel_cost_df, fuel_cost_dict[veh]], ignore_index=True, axis=0)
            # self.inventory_df.insert(len(self.inventory_df.columns),
            #                          'FuelCost_Retail_AvgPerMile',
            #                          self.inventory_df['FuelCost_Retail_TotalCost'] / self.inventory_df['VMT'])
            # self.inventory_df.insert(len(self.inventory_df.columns),
            #                          'FuelCost_Retail_AvgPerVeh',
            #                          self.inventory_df[['FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh']].product(axis=1))
        return fuel_cost_df


class RepairAndMaintenanceCost:
    """
    The RepairAndMaintenance class calculates the repair & maintenance costs.

    :param passed_df: A DataFrame that provides the necessary physical parameters: a vehicle tuple; cumulative VMT/veh/year;
    estimated ages when warranty & useful life is reached.
    :param metrics_repair_and_maint_dict: The repair and maintenance cost curve inputs contained in the inputs folder; the dictionary is created in code
    :param pkg_directcost_veh_regclass_dict: The dictionary of package direct costs, year-over-year, created in code
    """

    def __init__(self, passed_df, metrics_repair_and_maint_dict, scaling_frame_of_reference_df, estimated_ages_df, per_veh_df, vmt_df):
        self.passed_df = passed_df
        self.metrics_repair_and_maint_dict = metrics_repair_and_maint_dict
        self.scaling_frame_of_reference_df = scaling_frame_of_reference_df
        self.estimated_ages_df = estimated_ages_df
        self.per_veh_df = per_veh_df
        self.vmt_df = vmt_df

    def get_estimated_identifier_age(self, location, identifier):
        temp = pd.DataFrame(self.estimated_ages_df.loc[self.estimated_ages_df['static_id'] == location, f'EstimatedAge_{identifier}']).reset_index(drop=True)
        return temp.at[0, f'EstimatedAge_{identifier}']

    def merge_vmt_avg_per_veh(self, df_return):
        veh_vmt_per_veh_df = df_return[['static_id']].merge(self.per_veh_df[['static_id', 'VMT_AvgPerVeh']], on='static_id').reset_index(drop=True)
        return veh_vmt_per_veh_df

    def merge_vmt(self, df_return):
        veh_vmt_df = df_return[['static_id']].merge(self.vmt_df[['static_id', 'VMT']], on='static_id').reset_index(drop=True)
        return veh_vmt_df

    def emission_repair_costs(self, veh):
        """

        :return: A vehicle-specific DataFrame with emission repair metrics included (cost/mile, cost/veh, total costs)
        """
        print(f'Working on repair costs for {veh}')
        veh_df = pd.DataFrame(self.passed_df.loc[self.passed_df['alt_st_rc_ft'] == veh,
                                                 ['static_id', 'modelYearID', 'ageID', 'DirectCost_AvgPerVeh']]).reset_index(drop=True)
        repair_cost_dict = dict()
        # index_loc = 0
        for model_year in range(veh_df['modelYearID'].min(), veh_df['modelYearID'].max() + 1):
            repair_cost_dict[model_year] = pd.DataFrame(veh_df.loc[veh_df['modelYearID'] == model_year, :]).reset_index(drop=True)
            # first determine the ratio of direct costs of the veh to direct costs of passed scaling frame of reference
            # veh_regclass = (veh[0], veh[2], veh[3])
            scaling_frame_of_reference = pd.DataFrame(self.scaling_frame_of_reference_df.loc[self.scaling_frame_of_reference_df['modelYearID'] == model_year,
                                                                                             'DirectCost_AvgPerVeh']).reset_index(drop=True)
            direct_cost_scaler = repair_cost_dict[model_year]['DirectCost_AvgPerVeh'][0] \
                                 / scaling_frame_of_reference['DirectCost_AvgPerVeh'][0]
            warranty_age = self.get_estimated_identifier_age(repair_cost_dict[model_year]['static_id'][0], 'Warranty')
            usefullife_age = self.get_estimated_identifier_age(repair_cost_dict[model_year]['static_id'][0], 'UsefulLife')
            # warranty_age = df_temp.loc[df_temp['modelYearID'] == model_year, 'EstimatedAge_Warranty'].mean()
            # usefullife_age = df_temp.loc[df_temp['modelYearID'] == model_year, 'EstimatedAge_UsefulLife'].mean()
            in_warranty_cpm = self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm'] \
                              * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                              * direct_cost_scaler
            at_usefullife_cpm = self.metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_owner_cpm'] \
                                * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                                * direct_cost_scaler
            if usefullife_age > warranty_age:
                slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) / (usefullife_age - warranty_age)
            else:
                slope_within_usefullife = 0
            max_cpm = self.metrics_repair_and_maint_dict['max_repair_and_maintenance_cpm'] \
                      * self.metrics_repair_and_maint_dict['emission_repair_share'] \
                      * direct_cost_scaler
            repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
                                                'direct_cost_scaler',
                                                direct_cost_scaler)
            repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
                                                'slope_within_usefullife',
                                                slope_within_usefullife)
            repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
                                                'max_cpm',
                                                max_cpm)
            # determine in-warranty cost per mile
            repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
                                                'EmissionRepairCost_Owner_AvgPerMile',
                                                in_warranty_cpm)
            # determine out-of-warranty but within-useful-life cost per mile for owner
            repair_cost_dict[model_year].loc[(repair_cost_dict[model_year]['ageID'] > (warranty_age - 1)),
                                             'EmissionRepairCost_Owner_AvgPerMile'] \
                = slope_within_usefullife * (repair_cost_dict[model_year]['ageID'] - (warranty_age - 1)) \
                  + in_warranty_cpm
            # determine at-usefullife cost per mile
            repair_cost_dict[model_year].loc[(repair_cost_dict[model_year]['ageID'] >= (usefullife_age - 1)),
                                             'EmissionRepairCost_Owner_AvgPerMile'] \
                = at_usefullife_cpm
            # determine beyond-useful-life cost per mile for owner
            repair_cost_dict[model_year].loc[(repair_cost_dict[model_year]['ageID'] > (usefullife_age - 1)),
                                             'EmissionRepairCost_Owner_AvgPerMile'] \
                = max_cpm
            # index_loc += 1
        df_return = pd.DataFrame()
        for model_year in range(veh_df['modelYearID'].min(), veh_df['modelYearID'].max() + 1):
            df_return = pd.concat([df_return, repair_cost_dict[model_year]], axis=0, ignore_index=True)
        df_return.reset_index(drop=True, inplace=True)
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_Owner_AvgPerVeh',
                         self.merge_vmt_avg_per_veh(df_return)['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
        df_return.insert(len(df_return.columns),
                         'EmissionRepairCost_Owner_TotalCost',
                         self.merge_vmt(df_return)['VMT'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
        df_return.drop(columns=['modelYearID', 'ageID', 'DirectCost_AvgPerVeh'], inplace=True)
        return df_return

# class RepairAndMaintenanceCost:
#     """
#     The RepairAndMaintenance class calculates the repair & maintenance costs.
#
#     :param passed_df: A DataFrame that provides the necessary physical parameters: a vehicle tuple; cumulative VMT/veh/year;
#     estimated ages when warranty & useful life is reached.
#     :param metrics_repair_and_maint_dict: The repair and maintenance cost curve inputs contained in the inputs folder; the dictionary is created in code
#     :param pkg_directcost_veh_regclass_dict: The dictionary of package direct costs, year-over-year, created in code
#     """
#
#     def __init__(self, passed_df, metrics_repair_and_maint_dict, pkg_directcost_veh_regclass_dict):
#         self.passed_df = passed_df
#         self.metrics_repair_and_maint_dict = metrics_repair_and_maint_dict
#         self.pkg_directcost_veh_regclass_dict = pkg_directcost_veh_regclass_dict
#
#     def emission_repair_costs(self, veh):
#         """
#
#         :return: A vehicle-specific DataFrame with emission repair metrics included (cost/mile, cost/veh, total costs)
#         """
#         print(f'Working on repair costs for {veh}')
#         df_temp = pd.DataFrame(self.passed_df.loc[self.passed_df['alt_st_rc_ft'] == veh, :])
#         repair_cost_dict = dict()
#         index_loc = 0
#         for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
#             repair_cost_dict[model_year] = pd.DataFrame(df_temp.loc[df_temp['modelYearID'] == model_year, :])
#             # first determine the ratio of direct costs of the veh to direct costs of (0, 47, 2)
#             veh_regclass = (veh[0], veh[2], veh[3])
#             direct_cost_scalar = self.pkg_directcost_veh_regclass_dict[veh_regclass].loc[
#                                      self.pkg_directcost_veh_regclass_dict[veh_regclass]['modelYearID'] == model_year,
#                                      'DirectCost_AvgPerVeh'][index_loc] \
#                                  / self.pkg_directcost_veh_regclass_dict[0, 47, 2].loc[
#                                      self.pkg_directcost_veh_regclass_dict[0, 47, 2]['modelYearID'] == model_year,
#                                      'DirectCost_AvgPerVeh'][index_loc]
#             warranty_age = df_temp.loc[df_temp['modelYearID'] == model_year, 'EstimatedAge_Warranty'].mean()
#             usefullife_age = df_temp.loc[df_temp['modelYearID'] == model_year, 'EstimatedAge_UsefulLife'].mean()
#             in_warranty_cpm = self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm'] \
#                               * self.metrics_repair_and_maint_dict['emission_repair_share'] \
#                               * direct_cost_scalar
#             at_usefullife_cpm = self.metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_owner_cpm'] \
#                                 * self.metrics_repair_and_maint_dict['emission_repair_share'] \
#                                 * direct_cost_scalar
#             if usefullife_age > warranty_age:
#                 slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) / (usefullife_age - warranty_age)
#             else:
#                 slope_within_usefullife = 0
#             max_cpm = self.metrics_repair_and_maint_dict['max_repair_and_maintenance_cpm'] \
#                       * self.metrics_repair_and_maint_dict['emission_repair_share'] \
#                       * direct_cost_scalar
#             repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
#                                                 'direct_cost_scalar',
#                                                 direct_cost_scalar)
#             repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
#                                                 'slope_within_usefullife',
#                                                 slope_within_usefullife)
#             repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
#                                                 'max_cpm',
#                                                 max_cpm)
#             # determine in-warranty cost per mile
#             repair_cost_dict[model_year].insert(len(repair_cost_dict[model_year].columns),
#                                                 'EmissionRepairCost_Owner_AvgPerMile',
#                                                 in_warranty_cpm)
#             # determine out-of-warranty but within-useful-life cost per mile for owner
#             repair_cost_dict[model_year].loc[(repair_cost_dict[model_year]['ageID'] > (warranty_age - 1)),
#                                              'EmissionRepairCost_Owner_AvgPerMile'] \
#                 = slope_within_usefullife * (repair_cost_dict[model_year]['ageID'] - (warranty_age - 1)) \
#                   + in_warranty_cpm
#             # determine at-usefullife cost per mile
#             repair_cost_dict[model_year].loc[(repair_cost_dict[model_year]['ageID'] >= (usefullife_age - 1)),
#                                              'EmissionRepairCost_Owner_AvgPerMile'] \
#                 = at_usefullife_cpm
#             # determine beyond-useful-life cost per mile for owner
#             repair_cost_dict[model_year].loc[(repair_cost_dict[model_year]['ageID'] > (usefullife_age - 1)),
#                                              'EmissionRepairCost_Owner_AvgPerMile'] \
#                 = max_cpm
#             index_loc += 1
#         df_return = pd.DataFrame()
#         for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
#             df_return = pd.concat([df_return, repair_cost_dict[model_year]], axis=0, ignore_index=True)
#         df_return.reset_index(drop=True, inplace=True)
#         df_return.insert(len(df_return.columns),
#                          'EmissionRepairCost_Owner_AvgPerVeh',
#                          df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
#         df_return.insert(len(df_return.columns),
#                          'EmissionRepairCost_Owner_TotalCost',
#                          df_return['VMT'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
#         return df_return

    # def emission_repair_costs(self):
    #     """
    # 
    #     :return: The passed DataFrame (operating_costs expected) with emission repair metrics included (cost/mile, cost/veh, total costs)
    #     """
    # 
    #     df_temp = self.passed_object.copy()
    #     vehicles = pd.Series(df_temp['alt_st_rc_ft']).unique()
    #     repair_cost_dict = dict()
    #     for veh in vehicles:
    #         print(f'Working on repair costs for {veh}')
    #         index_loc = 0
    #         for model_year in range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1):
    #             repair_cost_dict[veh, model_year] = pd.DataFrame(df_temp.loc[((df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year)), :])
    #             # first determine the ratio of direct costs of the veh to direct costs of (0, 47, 2)
    #             veh_regclass = (veh[0], veh[2], veh[3])
    #             direct_cost_scalar = self.pkg_directcost_veh_regclass_dict[veh_regclass].loc[
    #                                      self.pkg_directcost_veh_regclass_dict[veh_regclass]['modelYearID'] == model_year,
    #                                      'DirectCost_AvgPerVeh'][index_loc] \
    #                                  / self.pkg_directcost_veh_regclass_dict[0, 47, 2].loc[
    #                                      self.pkg_directcost_veh_regclass_dict[0, 47, 2]['modelYearID'] == model_year,
    #                                      'DirectCost_AvgPerVeh'][index_loc]
    #             warranty_age = df_temp.loc[(df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year), 'EstimatedAge_Warranty'].mean()
    #             usefullife_age = df_temp.loc[(df_temp['alt_st_rc_ft'] == veh) & (df_temp['modelYearID'] == model_year), 'EstimatedAge_UsefulLife'].mean()
    #             in_warranty_cpm = self.metrics_repair_and_maint_dict['inwarranty_repair_and_maintenance_owner_cpm'] \
    #                               * self.metrics_repair_and_maint_dict['emission_repair_share'] \
    #                               * direct_cost_scalar
    #             at_usefullife_cpm = self.metrics_repair_and_maint_dict['atusefullife_repair_and_maintenance_owner_cpm'] \
    #                                 * self.metrics_repair_and_maint_dict['emission_repair_share'] \
    #                                 * direct_cost_scalar
    #             if usefullife_age > warranty_age:
    #                 slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) / (usefullife_age - warranty_age)
    #             else:
    #                 slope_within_usefullife = 0
    #             max_cpm = self.metrics_repair_and_maint_dict['max_repair_and_maintenance_cpm'] \
    #                       * self.metrics_repair_and_maint_dict['emission_repair_share'] \
    #                       * direct_cost_scalar
    #             repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'direct_cost_scalar', direct_cost_scalar)
    #             repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'slope_within_usefullife', slope_within_usefullife)
    #             repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'max_cpm', max_cpm)
    #             # determine in-warranty cost per mile
    #             repair_cost_dict[veh, model_year].insert(len(repair_cost_dict[veh, model_year].columns), 'EmissionRepairCost_Owner_AvgPerMile',
    #                                                      in_warranty_cpm)
    #             # determine out-of-warranty but within-useful-life cost per mile for owner
    #             repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] > (warranty_age - 1)), 'EmissionRepairCost_Owner_AvgPerMile'] \
    #                 = slope_within_usefullife * (repair_cost_dict[veh, model_year]['ageID'] - (warranty_age - 1)) \
    #                   + in_warranty_cpm
    #             # determine at-usefullife cost per mile
    #             repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] >= (usefullife_age - 1)), 'EmissionRepairCost_Owner_AvgPerMile'] \
    #                 = at_usefullife_cpm
    #             # determine beyond-useful-life cost per mile for owner
    #             repair_cost_dict[veh, model_year].loc[(repair_cost_dict[veh, model_year]['ageID'] > (usefullife_age - 1)),
    #                                                   'EmissionRepairCost_Owner_AvgPerMile'] \
    #                 = max_cpm
    #             index_loc += 1
    #     df_return = pd.DataFrame()
    #     for veh, model_year in product(vehicles, range(df_temp['modelYearID'].min(), df_temp['modelYearID'].max() + 1)):
    #         df_return = pd.concat([df_return, repair_cost_dict[veh, model_year]], axis=0, ignore_index=True)
    #     df_return.reset_index(drop=True, inplace=True)
    #     df_return.insert(len(df_return.columns),
    #                      'EmissionRepairCost_Owner_AvgPerVeh',
    #                      df_return['VMT_AvgPerVeh'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
    #     df_return.insert(len(df_return.columns),
    #                      'EmissionRepairCost_Owner_TotalCost',
    #                      df_return['VMT'] * df_return['EmissionRepairCost_Owner_AvgPerMile'])
    #     return df_return


if __name__ == '__main__':
    import pandas as pd
    from pathlib import Path
    from project_code.fleet import Fleet
    from project_code.cti_bca import read_input_files
    from project_code.operating_cost import ORVRadjust
    from project_code.group_metrics import GroupMetrics

    path_project = Path.cwd()
    path_inputs = path_project / 'inputs'

    # for testing the ORVRadjust class
    moves_file = path_inputs / 'CTI_NPRM_CY2027_2045_NewGRID_for_Todd_withORVRcorrection.csv'
    moves = pd.read_csv(moves_file)
    moves_adjustments = read_input_files(path_inputs, 'MOVES_Adjustments.csv', lambda x: 'Notes' not in x)
    orvr_fuelchanges = read_input_files(path_inputs, 'ORVR_FuelChangeInputs.csv', lambda x: 'Notes' not in x)
    if 'Alternative' in moves.columns.tolist():
        moves.rename(columns={'Alternative': 'optionID'}, inplace=True)
    for df in [moves, moves_adjustments]:
        df = Fleet(df).define_bca_regclass()
        df = Fleet(df).define_bca_sourcetype()
    moves_adjusted = Fleet(moves).adjust_moves(moves_adjustments)  # adjust (41, 2) to be engine cert only
    moves_adjusted = moves_adjusted.loc[(moves_adjusted['regClassID'] != 41) | (moves_adjusted['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
    moves_adjusted = moves_adjusted.loc[moves_adjusted['regClassID'] != 49, :]  # eliminate Gliders
    moves_adjusted = moves_adjusted.loc[moves_adjusted['fuelTypeID'] != 5, :]  # eliminate E85
    moves_adjusted = moves_adjusted.loc[moves_adjusted['regClassID'] >= 41, :]  # eliminate non-CTI regclasses
    cols = [col for col in moves_adjusted.columns if 'PM25' in col]
    moves_adjusted.insert(len(moves_adjusted.columns), 'PM25_onroad', moves_adjusted[cols].sum(axis=1))  # sum PM25 metrics
    moves_adjusted.insert(len(moves_adjusted.columns), 'ageID', moves_adjusted['yearID'] - moves_adjusted['modelYearID'])
    moves_adjusted.rename(columns={'NOx_UStons': 'NOx_onroad'}, inplace=True)
    cols_to_drop = [col for col in moves_adjusted.columns if 'CO_UStons' in col or 'exhaust' in col or 'brakewear' in col
                    or 'tirewear' in col or 'VOC' in col or 'CO2' in col or 'Energy' in col]
    moves_adjusted = moves_adjusted.drop(columns=cols_to_drop)
    moves_adjusted.reset_index(drop=True, inplace=True)

    # add VMT/vehicle & Gallons/mile metrics to moves dataframe
    moves_adjusted.insert(len(moves_adjusted.columns), 'VMT_AvgPerVeh', moves_adjusted['VMT'] / moves_adjusted['VPOP'])
    moves_adjusted = moves_adjusted.join(GroupMetrics(moves_adjusted,
                                                      ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'])
                                         .group_cumsum(['VMT_AvgPerVeh']))
    moves_adjusted.rename({'VPOP_CumSum': 'VPOP_CumSum_by_alt_rc_ft'}, inplace=True, axis=1)
    moves_adjusted.insert(len(moves_adjusted.columns), 'MPG_AvgPerVeh', moves_adjusted['VMT'] / moves_adjusted['Gallons'])

    st_rc_ft_vehs = pd.Series(moves_adjusted['st_rc_ft'].unique())

    moves_adjusted = ORVRadjust(st_rc_ft_vehs, orvr_fuelchanges, moves_adjusted).adjust_gallons()
    print(moves_adjusted.loc[(moves_adjusted['fuelTypeID'] == 1) & (moves_adjusted['optionID'] == 1), 'ml/g'].head())
    print(moves_adjusted.loc[(moves_adjusted['fuelTypeID'] == 1) & (moves_adjusted['optionID'] == 1), 'THC_UStons_Reductions'].head())
    print(moves_adjusted.loc[(moves_adjusted['fuelTypeID'] == 2) & (moves_adjusted['optionID'] == 1), 'ml/g'].head())
    print(moves_adjusted.loc[(moves_adjusted['fuelTypeID'] == 2) & (moves_adjusted['optionID'] == 1), 'THC_UStons_Reductions'].head())

    # for testing the get_reductions function created DataFrames should show metric_reductions values of 0 for
    # optionID 0 and 100 for optionID 1.
    df = pd.DataFrame({'optionID': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, ],
                       'OptionName': ['Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Base', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', 'Alt1', ],
                       'modelYearID': [2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028, 2027, 2027, 2027, 2027, 2028, 2028, 2028, 2028, ],
                       'regClassID': [46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, 46, 47, ],
                       'fuelTypeID': [1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2, ],
                       'metric': [200, 200, 200, 200, 300, 300, 300, 300, 100, 100, 100, 100, 200, 200, 200, 200, ]})
    number_alts = int(df['optionID'].max()) + 1
    df = get_reductions(df, 'metric')
    print(df)
