import pandas as pd


def create_fleet_totals_dict(fleet_df):
    df = fleet_df.copy()
    id = pd.Series(zip(zip(df['optionID'], fleet_df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'], df['ageID']))
    df.insert(0, 'id', id)
    df.drop(columns=['modelYearID', 'ageID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_fleet_averages_dict(fleet_df):
    df = pd.DataFrame(fleet_df[['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'yearID', 'modelYearID', 'ageID']]).reset_index(drop=True)
    id = pd.Series(zip(zip(df['optionID'], fleet_df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'], df['ageID']))
    df.insert(0, 'id', id)
    df.drop(columns=['modelYearID', 'ageID'], inplace=True)
    df.insert(len(df.columns), 'VMT_AvgPerVeh', fleet_df['VMT'] / fleet_df['VPOP'])
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_regclass_sales_dict(fleet_df):
    df = fleet_df.copy()
    df = pd.DataFrame(df.loc[df['ageID'] == 0, ['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'VPOP']]).reset_index(drop=True)
    df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID'], as_index=False).sum()
    df.insert(0, 'id', pd.Series(zip(zip(df['optionID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'])))
    df.drop(columns=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_moves_adjustments_dict(input_df, *args):
    df = input_df.copy()
    cols = [arg for arg in args]
    id = pd.Series(zip(df[cols[0]], df[cols[1]], df[cols[2]]))
    df.insert(0, 'id', id)
    df.drop(columns=cols, inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_seedvol_factor_dict(input_df):
    df = input_df.copy()
    id = pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID']))
    df.insert(0, 'id', id)
    df.drop(columns=['optionID', 'regClassID', 'fuelTypeID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_markup_inputs_dict(input_df):
    """

    :param df: A DataFrame of the indirect cost markup factors and values by option and fueltype.
    :return: A dictionary with 'fueltype, markup factor' keys and 'markup value' values.
    """
    df = input_df.copy()
    # insert a unique id to use as a dictionary key
    df.insert(0, 'id', pd.Series(zip(df['fuelTypeID'], df['Markup_Factor'])))
    df.set_index('id', inplace=True)
    df.drop(columns=['fuelTypeID', 'Markup_Factor'], inplace=True)
    return df.to_dict('index')


def create_def_doserate_inputs_dict(input_df):
    df = input_df.copy()
    id = pd.Series(zip(df['regClassID'], df['fuelTypeID']))
    df.insert(0, 'id', id)
    df.drop(columns=['regClassID', 'fuelTypeID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_def_prices_dict(input_df):
    df = input_df.copy()
    df.set_index('yearID', inplace=True)
    return df.to_dict('index')


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles

    project_fleet_df = create_fleet_df(settings)
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_dict = create_fleet_totals_dict(project_fleet_df)

    moves_adjustments_dict = create_moves_adjustments_dict(settings.moves_adjustments, 'optionID', 'regClassID', 'fuelTypeID')
    seedvol_factor_dict = create_seedvol_factor_dict(settings.regclass_learningscalers)
    markup_inputs_dict = create_markup_inputs_dict(settings.markups)
    print('')