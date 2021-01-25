import pandas as pd


from vehicle import Vehicle


def create_fleet_df(settings):
    df = settings.moves.copy()
    if 'Alternative' in df.columns.tolist():
        df.rename(columns={'Alternative': 'optionID'}, inplace=True)

    # remove data we don't need to carry for the project
    df = df.loc[(df['regClassID'] != 41) | (df['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
    df = df.loc[df['regClassID'] != 49, :]  # eliminate Gliders
    df = df.loc[df['fuelTypeID'] != 5, :]  # eliminate E85
    df = df.loc[df['regClassID'] >= 41, :]  # eliminate non-project regclasses

    df = pd.DataFrame(df.loc[df['modelYearID'] >= settings.year_min, :]).reset_index(drop=True)

    # add some vehicle identifiers
    df.insert(0, 'OptionName', '')
    for alt in settings.options_dict.keys():
        df.loc[df['optionID'] == alt, 'OptionName'] = settings.options_dict[alt]['OptionName']

    df.insert(0, 'sourceTypeName', '')
    for st in Vehicle.sourcetype_dict.keys():
        df.loc[df['sourceTypeID'] == st, 'sourceTypeName'] = Vehicle(st).sourcetype_name()
        # df.loc[df['sourceTypeID'] == st, 'sourceTypeName'] = sourcetype_dict[st]

    df.insert(0, 'regClassName', '')
    for rc in Vehicle.regclass_dict.keys():
        df.loc[df['regClassID'] == rc, 'regClassName'] = Vehicle(rc).regclass_name()
        # df.loc[df['regClassID'] == rc, 'regClassName'] = regclass_dict[rc]

    df.insert(0, 'fuelTypeName', '')
    for ft in Vehicle.fueltype_dict.keys():
        df.loc[df['fuelTypeID'] == ft, 'fuelTypeName'] = Vehicle(ft).fueltype_name()
        # df.loc[df['fuelTypeID'] == ft, 'fuelTypeName'] = fueltype_dict[ft]

    # sum the PM constituents into a single constituent
    cols = [col for col in df.columns if 'PM25' in col]
    df.insert(len(df.columns), 'PM25_UStons', df[cols].sum(axis=1))  # sum PM25 metrics

    rc_vehicles = regclass_vehicles(df)
    # make adjustments to MOVES values as needed for cost analysis
    for vehicle in rc_vehicles:
        alt, rc, ft = vehicle
        if vehicle in settings.moves_adjustments_dict.keys():
            adjustment = settings.moves_adjustments_dict[(vehicle)]['percent']
            growth = settings.moves_adjustments_dict[(vehicle)]['growth']
        else:
            adjustment, growth = 1, 0
        args_to_adjust = ['VPOP', 'VMT', 'Gallons']
        for arg in args_to_adjust:
            df.loc[(df['optionID'] == alt) & (df['regClassID'] == rc) & (df['fuelTypeID'] == ft), arg] \
                = df.loc[(df['optionID'] == alt) & (df['regClassID'] == rc) & (df['fuelTypeID'] == ft), arg] \
                  * adjustment * (1 + growth)
    return df


def regclass_vehicles(fleet_df):
    return pd.Series(zip(fleet_df['optionID'], fleet_df['regClassID'], fleet_df['fuelTypeID'])).unique()


def sourcetype_vehicles(fleet_df):
    return pd.Series(zip(fleet_df['optionID'], fleet_df['sourceTypeID'], fleet_df['regClassID'], fleet_df['fuelTypeID'])).unique()


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)
    print(f'\n{vehicles_rc}\n')

    vehicles_st = sourcetype_vehicles(project_fleet_df)
    print(f'\n{vehicles_st}\n')
