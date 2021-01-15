import pandas as pd

# create a dictionary to store moves adjustments
adj_dict = dict()


def adjust_moves(vehicle, settings):
    """

    :param moves_adjustments_df: A DataFrame of adjustments to be made to MOVES values
    :return: The adjustment value to be applied.
    """
    alt, rc, ft = vehicle
    adj_dict_id = vehicle
    if adj_dict_id in adj_dict:
        adjustment = adj_dict[adj_dict_id]
    else:
        if settings.moves_adjustments is not None: # this is just to be sure that the moves adjustments file is used, otherwise the try might skip if the file isn't in settings.
            try:
                adj_df = pd.DataFrame(settings.moves_adjustments.loc[(settings.moves_adjustments['optionID'] == alt)
                                                                     & (settings.moves_adjustments['regClassID'] == rc)
                                                                     & (settings.moves_adjustments['fuelTypeID'] == ft), 'percent']).reset_index(drop=True)
                adjustment = adj_df['percent'][0]
            except:
                adjustment = 1
    adj_dict[adj_dict_id] = adjustment
    return adjustment


def create_fleet_df(settings):
    project_fleet = settings.moves.copy()
    if 'Alternative' in project_fleet.columns.tolist():
        project_fleet.rename(columns={'Alternative': 'optionID'}, inplace=True)

    # remove data we don't need to carry for the project
    project_fleet = project_fleet.loc[(project_fleet['regClassID'] != 41) | (project_fleet['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
    project_fleet = project_fleet.loc[project_fleet['regClassID'] != 49, :]  # eliminate Gliders
    project_fleet = project_fleet.loc[project_fleet['fuelTypeID'] != 5, :]  # eliminate E85
    project_fleet = project_fleet.loc[project_fleet['regClassID'] >= 41, :]  # eliminate non-project regclasses

    project_fleet = pd.DataFrame(project_fleet.loc[project_fleet['modelYearID'] >= settings.year_min, :]).reset_index(drop=True)

    # sum the PM constituents into a single constituent
    cols = [col for col in project_fleet.columns if 'PM25' in col]
    project_fleet.insert(len(project_fleet.columns), 'PM25_UStons', project_fleet[cols].sum(axis=1))  # sum PM25 metrics

    rc_vehicles = regclass_vehicles(project_fleet)
    for vehicle in rc_vehicles:
        alt, rc, ft = vehicle
        adjustment = adjust_moves(vehicle, settings)
        args_to_adjust = ['VPOP', 'VMT', 'Gallons']
        for arg in args_to_adjust:
            project_fleet.loc[(project_fleet['optionID'] == alt) & (project_fleet['regClassID'] == rc) & (project_fleet['fuelTypeID'] == ft), arg] \
                = project_fleet.loc[(project_fleet['optionID'] == alt) & (project_fleet['regClassID'] == rc) & (project_fleet['fuelTypeID'] == ft), arg] \
                  * adjustment
    return project_fleet


def create_fleet_dict(fleet_df):
    df = fleet_df.copy()
    df.insert(0, 'id', pd.Series(zip(zip(df['optionID'], fleet_df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'], df['ageID'])))
    # df.drop(columns=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID'], inplace=True)
    df.drop(columns=['modelYearID', 'ageID'], inplace=True)
    df.set_index('id', inplace=True)
    project_fleet_dict = df.to_dict('index')
    return project_fleet_dict


def create_regclass_sales_dict(fleet_df):
    df = fleet_df.copy()
    df = pd.DataFrame(df.loc[df['ageID'] == 0, ['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'VPOP']]).reset_index(drop=True)
    df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID'], as_index=False).sum()
    df.insert(0, 'id', pd.Series(zip(zip(df['optionID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'])))
    df.drop(columns=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID'], inplace=True)
    df.set_index('id', inplace=True)
    regclass_sales_dict = df.to_dict('index')
    return regclass_sales_dict


def regclass_vehicles(fleet_df):
    return pd.Series(zip(fleet_df['optionID'], fleet_df['regClassID'], fleet_df['fuelTypeID'])).unique()


def sourcetype_vehicles(fleet_df):
    return pd.Series(zip(fleet_df['optionID'], fleet_df['sourceTypeID'], fleet_df['regClassID'], fleet_df['fuelTypeID'])).unique()


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings

    project_fleet_df = create_fleet_df(settings.moves)
    vehicles_rc = pd.Series(project_fleet_df['alt_rc_ft'].unique())
    print(vehicles_rc)

    vehicles_st = pd.Series(project_fleet_df['alt_st_rc_ft'].unique())
    print(vehicles_st)
