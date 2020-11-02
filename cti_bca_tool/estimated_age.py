"""
estimated_age.py

Contains the EstimatedAge class.

"""
import pandas as pd
from itertools import product


class EstimatedAge:
    def __init__(self, inventory_df, vmt_thru_ageID, miles_df, age_df):
        """
        The EstimatedAge class calculates the age at which warranty and useful life are reached given the alt_st_rc_ft vehicle.

        :param inventory_df: A DataFrame that provides the necessary physical parameters: a vehicle tuple; cumulative VMT/veh/year
        :param vmt_thru_ageID: A single entry in the BCA_Inputs file contained in the inputs folder.
        :param miles_df: Warranty or Useful life miles; a DataFrame generated in code from files in the inputs folder.
        :param age_df: Warranty or Useful life ages; a DataFrame generated in code from files in the inputs folder.
        """

        self.inventory_df = inventory_df
        self.vmt_thru_ageID = vmt_thru_ageID
        self.miles_df = miles_df
        self.age_df = age_df

    def ages_by_identifier(self, identifier):
        """

        :param identifier: A string: "Warranty" or "UsefulLife" expected.
        :return: A DataFrame of required, calculated (required miles divided by miles/year) and estimated ages at which warranty or useful life are expected to be reached.
        """
        print(f'\nCalculating "Estimated Ages" when {identifier} will be reached.\n')
        vmt_thru_age_df = pd.DataFrame(self.inventory_df.loc[self.inventory_df['ageID'] == self.vmt_thru_ageID],
                                       columns=['static_id', 'modelYearID', 'alt_st_rc_ft', 'alt_rc_ft', 'VMT_AvgPerVeh_CumSum'])
        vmt_thru_age_df.insert(len(vmt_thru_age_df.columns), 'TypicalVMTperYear', vmt_thru_age_df['VMT_AvgPerVeh_CumSum'] / (self.vmt_thru_ageID + 1))
        vmt_thru_age_df = vmt_thru_age_df.merge(self.miles_df[['alt_rc_ft', 'modelYearID', f'{identifier}_Miles']], on=['alt_rc_ft', 'modelYearID'], how='left')
        vmt_thru_age_df = vmt_thru_age_df.merge(self.age_df[['alt_rc_ft', 'modelYearID', f'{identifier}_Age']], on=['alt_rc_ft', 'modelYearID'], how='left')
        cols = [col for col in vmt_thru_age_df.columns if identifier in col]

        # since the merge is only for select MYs and alt_rc_ft vehicles, filling in for other ages/years has to be done via the following loop
        vehs = pd.Series(vmt_thru_age_df['alt_rc_ft'].unique())
        for veh in vehs:
            vmt_thru_age_df.loc[vmt_thru_age_df['alt_rc_ft'] == veh, cols] = vmt_thru_age_df.loc[vmt_thru_age_df['alt_rc_ft'] == veh, cols].ffill(axis=0)
        vmt_thru_age_df.insert(len(vmt_thru_age_df.columns),
                               f'CalculatedAgeWhen{identifier}Reached',
                               round(vmt_thru_age_df[f'{identifier}_Miles'] / vmt_thru_age_df['TypicalVMTperYear']))

        estimated_age = list()
        for index, row in vmt_thru_age_df.iterrows():
            required_age = row[f'{identifier}_Age']
            calculated_age = row[f'CalculatedAgeWhen{identifier}Reached']
            min_age = min(required_age, calculated_age)
            estimated_age.append(min_age)
        vmt_thru_age_df.insert(len(vmt_thru_age_df.columns), f'EstimatedAge_{identifier}', estimated_age)

        cols = [col for col in vmt_thru_age_df.columns if identifier in col]
        return_df = pd.DataFrame(self.inventory_df[['static_id', 'modelYearID', 'alt_st_rc_ft']]
                                 .merge(vmt_thru_age_df[['modelYearID', 'alt_st_rc_ft', 'TypicalVMTperYear'] + cols],
                                        on=['modelYearID', 'alt_st_rc_ft'], how='left')).reset_index(drop=True)

        # for those MYs without ageID data within the range specified in BCA_Inputs (i.e., no ageID data >= vmt_thru_ageID),
        # a forward fill will fill their data with the last MY having ageID data within the range
        vehs = pd.Series(return_df['alt_st_rc_ft'].unique())
        for veh in vehs:
            return_df.loc[(return_df['alt_st_rc_ft'] == veh) & (return_df['modelYearID'] >= return_df['modelYearID'].max() - self.vmt_thru_ageID)] \
                = return_df.loc[(return_df['alt_st_rc_ft'] == veh) & (return_df['modelYearID'] >= return_df['modelYearID'].max() - self.vmt_thru_ageID)].ffill(axis=0)
        return_df = return_df[['static_id', 'TypicalVMTperYear'] + [col for col in return_df.columns if f'{identifier}' in col]]
        return return_df


# class EstimatedAge2: # this is a decent concept but doesn't work yet and is very slow; plus, the above works
#     def __init__(self, veh, per_veh_df, vmt_thru_age_id):
#         self.veh = veh
#         self.per_veh_df = per_veh_df
#         self.vmt_thru_age_id = vmt_thru_age_id
#
#     def __repr__(self):
#         return f'Calculating "Estimated Ages" when Warranty & Useful Life are reached: Vehicle {self.veh}'
#
#     def calc_typical_vmt_per_year(self):
#         vmt = pd.DataFrame(self.per_veh_df.loc[self.per_veh_df['ageID'] == self.vmt_thru_age_id, 'VMT_AvgPerVeh_CumSum']).reset_index(drop=True)
#         vmt = vmt.at[0, 'VMT_AvgPerVeh_CumSum'] / self.vmt_thru_age_id + 1
#         return vmt
#
#     def get_required_miles(self, miles_df, identifier, year):
#         """
#
#         :param identifier:
#         :param year:
#         :return:
#         """
#         miles_df_year = pd.DataFrame(miles_df.loc[miles_df['modelYearID'] <= year, :])
#         miles_df_year = pd.DataFrame(miles_df_year.loc[(miles_df_year['optionID'] == self.veh[0]) &
#                                                        (miles_df_year['regClassID'] == self.veh[2]) &
#                                                        (miles_df_year['fuelTypeID'] == self.veh[3]) &
#                                                        (miles_df_year['modelYearID'] == miles_df_year['modelYearID'].max())]).reset_index(drop=True)
#         miles = miles_df_year.at[0, f'{identifier}_Miles']
#         return miles
#
#     def get_required_age(self, age_df, identifier, year):
#         age_df_year = pd.DataFrame(age_df.loc[age_df['modelYearID'] <= year, :])
#         age_df_year = pd.DataFrame(age_df_year.loc[(age_df_year['optionID'] == self.veh[0]) &
#                                                    (age_df_year['regClassID'] == self.veh[2]) &
#                                                    (age_df_year['fuelTypeID'] == self.veh[3]) &
#                                                    (age_df_year['modelYearID'] == age_df_year['modelYearID'].max())]).reset_index(drop=True)
#         age = age_df_year.at[0, f'{identifier}_Age']
#         return age
#
#     def calculated_age_when_identifier_reached(self, miles_df, identifier, year):
#         age = round(self.get_required_miles(miles_df, identifier, year) / self.calc_typical_vmt_per_year())
#         return age
#
#     def calc_estimated_age(self, miles_df, age_df, identifier, year):
#         age = min(self.get_required_age(age_df, identifier, year), self.calculated_age_when_identifier_reached(miles_df, identifier, year))
#         return age
#
#     def return_df(self, miles_df, age_df, identifier, year):
#         print(f'{identifier} Estimated Age for model year {year}')
#         return_df = pd.DataFrame(self.per_veh_df[['static_id']])
#         return_df.insert(len(return_df.columns), 'TypicalVMTperYear', self.calc_typical_vmt_per_year())
#         return_df.insert(len(return_df.columns), f'{identifier}_Miles', self.get_required_miles(miles_df, identifier, year))
#         return_df.insert(len(return_df.columns), f'{identifier}_Age', self.get_required_age(age_df, identifier, year))
#         return_df.insert(len(return_df.columns), f'CalculatedAgeWhen{identifier}Reached', self.calculated_age_when_identifier_reached(miles_df, identifier, year))
#         return_df.insert(len(return_df.columns), f'EstimatedAge_{identifier}', self.calc_estimated_age(miles_df, age_df, identifier, year))
#         return return_df


if __name__ == '__main__':
    import pandas as pd
    from pathlib import Path
    import cti_bca_tool.general_functions as gen_fxns

    typical_vmt_thru_age = 6

    path_project = Path.cwd()
    path_inputs = path_project / 'inputs'
    sourcetype_per_veh_file = path_project / 'dev/sourcetype_per_veh.csv'
    sourcetype_per_veh = pd.read_csv(sourcetype_per_veh_file)
    # this reads alt_rc_ft entries as strings, not tuples, so re-do these entries as tuples
    sourcetype_per_veh = sourcetype_per_veh['alt_rc_ft'].str.split(', ', expand=True).join(sourcetype_per_veh)
    sourcetype_per_veh.drop(columns=0, inplace=True)
    sourcetype_per_veh.rename(columns={1: 'regClassID', 2: 'fuelTypeID'}, inplace=True)
    sourcetype_per_veh['fuelTypeID'] = sourcetype_per_veh['fuelTypeID'].str.rstrip(')')
    sourcetype_per_veh['regClassID'] = pd.to_numeric(sourcetype_per_veh['regClassID'])
    sourcetype_per_veh['fuelTypeID'] = pd.to_numeric(sourcetype_per_veh['fuelTypeID'])
    sourcetype_per_veh['alt_rc_ft'] = pd.Series(zip(sourcetype_per_veh['optionID'], sourcetype_per_veh['regClassID'], sourcetype_per_veh['fuelTypeID']))

    input_files_df = pd.read_csv(path_inputs / 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    input_files_dict = input_files_df.to_dict('index')
    warranty_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['warranty_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
    usefullife_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['usefullife_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
    warranty_miles_reshaped = gen_fxns.reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                  [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Miles')
    warranty_age_reshaped = gen_fxns.reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Age')
    usefullife_miles_reshaped = gen_fxns.reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                    [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Miles')
    usefullife_age_reshaped = gen_fxns.reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                                  [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Age')

    for df in [warranty_miles_reshaped, warranty_age_reshaped, usefullife_miles_reshaped, usefullife_age_reshaped]:
        df['modelYearID'] = pd.to_numeric(df['modelYearID'])
        df.insert(0, 'alt_rc_ft', pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID'])))

    estimated_warranty_age_obj = EstimatedAge(sourcetype_per_veh, typical_vmt_thru_age,
                                              warranty_miles_reshaped, warranty_age_reshaped)
    warranty_ages = estimated_warranty_age_obj.ages_by_identifier('Warranty')
    estimated_usefullife_age_obj = EstimatedAge(sourcetype_per_veh, typical_vmt_thru_age,
                                                usefullife_miles_reshaped, usefullife_age_reshaped)
    usefullife_ages = estimated_usefullife_age_obj.ages_by_identifier('UsefulLife')
    estimated_ages_df = warranty_ages.merge(usefullife_ages, on=gen_fxns.get_common_metrics(warranty_ages, usefullife_ages), how='left')

    estimated_ages_df.to_csv(path_project / 'dev/estimated_ages_test.csv', index=False)
