import pandas as pd


class SourcetypeSales:
    def __init__(self, fleet_dict):
        self.fleet_dict = fleet_dict

    def create_sourcetype_sales_dict(self, fleet_df):
        """

        Parameters:
            fleet_df: A DataFrame of the project fleet.

        Returns:
            A dictionary of the fleet having keys equal to ((unit), alt, modelYearID) where unit is a tuple representing
            a sourcetype_regclass_fueltype, and values representing sales (sales=VPOP at ageID=0) for each key by model year.

        """
        df = fleet_df.copy()
        df = pd.DataFrame(df.loc[df['ageID'] == 0, ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID', 'VPOP', 'VPOP_AddingTech']]).reset_index(drop=True)
        df = df.groupby(by=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'], as_index=False).sum()
        df.insert(0, 'id', pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID'], df['modelYearID'])))
        df.drop(columns=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID'], inplace=True)
        df.set_index('id', inplace=True)
        return df.to_dict('index')
