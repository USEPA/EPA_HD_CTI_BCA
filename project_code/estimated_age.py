import pandas as pd


class EstimatedAge:
    def __init__(self, passed_df):
        self.passed_df = passed_df

    def ages_by_identifier(self, miles_df, age_df, vmt_thru_ageID, identifier):
        df_return = pd.DataFrame(self.passed_df.loc[self.passed_df['ageID'] == vmt_thru_ageID],
                                 columns=['optionID', 'modelYearID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'alt_rc_ft', 'VMT_AvgPerVeh_CumSum'])
        df_return.insert(len(df_return.columns), 'TypicalVMTperYear', df_return['VMT_AvgPerVeh_CumSum'] / (vmt_thru_ageID + 1))
        df_return = df_return.merge(miles_df, on=['optionID', 'modelYearID', 'regClassID', 'fuelTypeID'], how='left')
        df_return = df_return.merge(age_df, on=['optionID', 'modelYearID', 'regClassID', 'fuelTypeID'], how='left')
        cols = [col for col in df_return.columns if identifier in col]
        vehs = set(df_return['alt_rc_ft'])
        # since the merge is only for select MYs and alt_rc_ft vehicles, filling in for other ages/years has to be done via the following loop
        for veh in vehs:
            df_return.loc[(df_return['alt_rc_ft'] == veh), cols] = df_return.loc[(df_return['alt_rc_ft'] == veh), cols].ffill(axis=0)
        df_return.insert(len(df_return.columns), 'CalculatedAgeWhen' + identifier + 'Reached', round(df_return[identifier + '_Miles'] / df_return['TypicalVMTperYear']))

        estimated_age = list()
        for index, row in df_return.iterrows():
            actual_age = row[identifier + '_Age']
            calculated_age = row['CalculatedAgeWhen' + identifier + 'Reached']
            min_age = min(actual_age, calculated_age)
            estimated_age.append(min_age)
        df_return.insert(len(df_return.columns), 'EstimatedAge_' + identifier, estimated_age)
        df_return.drop(columns=['alt_rc_ft', 'VMT_AvgPerVeh_CumSum'], inplace=True) # drop for easier merge
        return df_return
