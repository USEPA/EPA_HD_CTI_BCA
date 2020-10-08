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
        age_df = pd.DataFrame(self.inventory_df.loc[self.inventory_df['ageID'] == self.vmt_thru_ageID],
                              columns=['static_id', 'modelYearID', 'alt_st_rc_ft', 'alt_rc_ft', 'VMT_AvgPerVeh_CumSum'])
        age_df.insert(len(age_df.columns), 'TypicalVMTperYear', age_df['VMT_AvgPerVeh_CumSum'] / (self.vmt_thru_ageID + 1))
        age_df = age_df.merge(self.miles_df[['alt_rc_ft', 'modelYearID', f'{identifier}_Miles']], on=['alt_rc_ft', 'modelYearID'], how='left')
        age_df = age_df.merge(self.age_df[['alt_rc_ft', 'modelYearID', f'{identifier}_Age']], on=['alt_rc_ft', 'modelYearID'], how='left')
        cols = [col for col in age_df.columns if identifier in col]

        # since the merge is only for select MYs and alt_rc_ft vehicles, filling in for other ages/years has to be done via the following loop
        vehs = pd.Series(age_df['alt_rc_ft'].unique())
        for veh in vehs:
            age_df.loc[age_df['alt_rc_ft'] == veh, cols] = age_df.loc[age_df['alt_rc_ft'] == veh, cols].ffill(axis=0)
        age_df.insert(len(age_df.columns),
                      f'CalculatedAgeWhen{identifier}Reached',
                      round(age_df[f'{identifier}_Miles'] / age_df['TypicalVMTperYear']))

        estimated_age = list()
        for index, row in age_df.iterrows():
            required_age = row[f'{identifier}_Age']
            calculated_age = row[f'CalculatedAgeWhen{identifier}Reached']
            min_age = min(required_age, calculated_age)
            estimated_age.append(min_age)
        age_df.insert(len(age_df.columns), f'EstimatedAge_{identifier}', estimated_age)

        cols = [col for col in age_df.columns if identifier in col]
        return_df = pd.DataFrame(self.inventory_df[['static_id', 'modelYearID', 'alt_st_rc_ft']]
                                 .merge(age_df[['modelYearID', 'alt_st_rc_ft', 'TypicalVMTperYear'] + cols],
                                        on=['modelYearID', 'alt_st_rc_ft'], how='left')).reset_index(drop=True)

        # for those MYs without ageID data within the range specified in BCA_Inputs (i.e., no ageID data >= vmt_thru_ageID),
        # a forward fill will fill their data with the last MY having ageID data within the range
        vehs = pd.Series(return_df['alt_st_rc_ft'].unique())
        for veh in vehs:
            return_df.loc[(return_df['alt_st_rc_ft'] == veh) & (return_df['modelYearID'] >= return_df['modelYearID'].max() - self.vmt_thru_ageID)] \
                = return_df.loc[(return_df['alt_st_rc_ft'] == veh) & (return_df['modelYearID'] >= return_df['modelYearID'].max() - self.vmt_thru_ageID)].ffill(axis=0)
        return_df = return_df[['static_id', 'TypicalVMTperYear'] + [col for col in return_df.columns if f'{identifier}' in col]]
        return return_df


class EstimatedAge2: # this works, but is very slow
    def __init__(self, veh, inventory_df, vmt_thru_age_id):
        self.veh = veh
        self.inventory_df = inventory_df
        self.vmt_thru_age_id = vmt_thru_age_id

    def __repr__(self):
        return f'Calculating "Estimated Ages" when Warranty & Useful Life are reached: Vehicle {self.veh}'

    def calc_typical_vmt_per_year(self):
        vmt = pd.DataFrame(self.inventory_df.loc[self.inventory_df['ageID'] == self.vmt_thru_age_id, 'VMT_AvgPerVeh_CumSum']).reset_index(drop=True)
        vmt = vmt.at[0, 'VMT_AvgPerVeh_CumSum'] / self.vmt_thru_age_id + 1
        return vmt

    def get_identifier_miles(self, miles_df, identifier, year):
        """

        :param identifier:
        :param year:
        :return:
        """
        miles_df_year = pd.DataFrame(miles_df.loc[miles_df['modelYearID'] <= year, :])
        miles_df_year = pd.DataFrame(miles_df_year.loc[(miles_df_year['optionID'] == self.veh[0]) &
                                                       (miles_df_year['regClassID'] == self.veh[2]) &
                                                       (miles_df_year['fuelTypeID'] == self.veh[3]) &
                                                       (miles_df_year['modelYearID'] == miles_df_year['modelYearID'].max())]).reset_index(drop=True)
        miles = miles_df_year.at[0, f'{identifier}_Miles']
        return miles

    def get_identifier_age(self, age_df, identifier, year):
        age_df_year = pd.DataFrame(age_df.loc[age_df['modelYearID'] <= year, :])
        age_df_year = pd.DataFrame(age_df_year.loc[(age_df_year['optionID'] == self.veh[0]) &
                                                   (age_df_year['regClassID'] == self.veh[2]) &
                                                   (age_df_year['fuelTypeID'] == self.veh[3]) &
                                                   (age_df_year['modelYearID'] == age_df_year['modelYearID'].max())]).reset_index(drop=True)
        age = age_df_year.at[0, f'{identifier}_Age']
        return age

    def calculated_age_when_identifier_reached(self, miles_df, identifier, year):
        age = round(self.get_identifier_miles(miles_df, identifier, year) / self.calc_typical_vmt_per_year())
        return age

    def calc_estimated_age(self, miles_df, age_df, identifier, year):
        age = min(self.get_identifier_age(age_df, identifier, year), self.calculated_age_when_identifier_reached(miles_df, identifier, year))
        return age

    def return_df(self, miles_df, age_df, identifier, year):
        print(f'{identifier} Estimated Age for model year {year}')
        return_df = pd.DataFrame(self.inventory_df[['static_id']])
        return_df.insert(len(return_df.columns), 'TypicalVMTperYear', self.calc_typical_vmt_per_year())
        return_df.insert(len(return_df.columns), f'{identifier}_Miles', self.get_identifier_miles(miles_df, identifier, year))
        return_df.insert(len(return_df.columns), f'{identifier}_Age', self.get_identifier_age(age_df, identifier, year))
        return_df.insert(len(return_df.columns), f'CalculatedAgeWhen{identifier}Reached', self.calculated_age_when_identifier_reached(miles_df, identifier, year))
        return_df.insert(len(return_df.columns), f'EstimatedAge_{identifier}', self.calc_estimated_age(miles_df, age_df, identifier, year))
        return return_df


if __name__ == '__main__':
    import pandas as pd
    from pathlib import Path
    from project_code.cti_bca import reshape_df
    # from project_code.estimated_age import EstimatedAge

    typical_vmt_thru_age = 6

    path_project = Path.cwd()
    path_inputs = path_project / 'inputs'
    sourcetype_costs_file = path_project / 'dev/estimated_age_test.csv'
    sourcetype_costs = pd.read_csv(sourcetype_costs_file)

    warranty_inputs = pd.read_csv(path_inputs / 'Warranty_Inputs.csv')
    usefullife_inputs = pd.read_csv(path_inputs / 'UsefulLife_Inputs.csv')
    warranty_miles_reshaped = reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                         [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Miles')
    warranty_age_reshaped = reshape_df(warranty_inputs.loc[warranty_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                       [col for col in warranty_inputs.columns if '20' in col], 'modelYearID', 'Warranty_Age')
    usefullife_miles_reshaped = reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Miles'], ['optionID', 'regClassID', 'fuelTypeID'],
                                           [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Miles')
    usefullife_age_reshaped = reshape_df(usefullife_inputs.loc[usefullife_inputs['period'] == 'Age'], ['optionID', 'regClassID', 'fuelTypeID'],
                                         [col for col in usefullife_inputs.columns if '20' in col], 'modelYearID', 'UsefulLife_Age')

    warranty_miles_reshaped['modelYearID'] = pd.to_numeric(warranty_miles_reshaped['modelYearID'])
    warranty_age_reshaped['modelYearID'] = pd.to_numeric(warranty_age_reshaped['modelYearID'])
    usefullife_miles_reshaped['modelYearID'] = pd.to_numeric(usefullife_miles_reshaped['modelYearID'])
    usefullife_age_reshaped['modelYearID'] = pd.to_numeric(usefullife_age_reshaped['modelYearID'])

    sourcetype_costs = EstimatedAge(sourcetype_costs, typical_vmt_thru_age, warranty_miles_reshaped, warranty_age_reshaped).ages_by_identifier('Warranty')
    sourcetype_costs = EstimatedAge(sourcetype_costs, typical_vmt_thru_age, usefullife_miles_reshaped, usefullife_age_reshaped).ages_by_identifier('UsefulLife')

    sourcetype_costs.to_csv(path_project / 'dev/sourcetype_costs.csv', index=False)
