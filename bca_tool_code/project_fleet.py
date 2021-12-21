import pandas as pd


def create_fleet_df(settings, input_df, options_dict, adj_dict, *args_with_tech):
    """

    Parameters:
        settings: The SetInputs class.\n
        input_df: DataFrame; the raw fleet input data (e.g., from MOVES). \n
        options_dict: Dictionary; provides the option IDs and names of options being run.\n
        adj_dict: Dictionary; provides any adjustments to be made to the data contained in input_df. \n
        args_with_tech: String(s); the attributes to be adjusted.

    Returns:
        A DataFrame of the MOVES inputs with necessary MOVES adjustments made according to the MOVES adjustments input file. The DataFrame will also add
        optionID/sourceTypeID/regClassID/fuelTypeID names and will use only those options included in the options.csv input file.

    """
    df = input_df.copy()
    if 'Alternative' in df.columns.tolist():
        df.rename(columns={'Alternative': 'optionID'}, inplace=True)

    # remove data we don't need to carry for the project
    df = df.loc[(df['regClassID'] != 41) | (df['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
    df = df.loc[df['regClassID'] != 49, :]  # eliminate Gliders
    df = df.loc[df['fuelTypeID'] != 5, :]  # eliminate E85
    df = df.loc[df['regClassID'] >= 41, :]  # eliminate non-project regclasses

    df = pd.DataFrame(df.loc[df['modelYearID'] >= settings.year_min, :]).reset_index(drop=True)

    # select only the options included in the options.csv input file
    option_id_list = [key for key in options_dict.keys()]
    df_alts = dict()
    df_return = pd.DataFrame()
    for alt in option_id_list:
        df_alts[alt] = df.loc[df['optionID'] == alt, :]
        df_return = pd.concat([df_return, df_alts[alt]], axis=0, ignore_index=True)

    df_return.reset_index(drop=True, inplace=True)

    # sum the PM constituents into a single constituent
    cols = [col for col in df_return.columns if 'PM25' in col]
    df_return.insert(len(df_return.columns), 'PM25_UStons', df_return[cols].sum(axis=1))  # sum PM25 metrics

    # make adjustments to MOVES values as needed for analysis
    st_vehicles = sourcetype_vehicles(df_return)
    for arg in args_with_tech:
        df_return.insert(df_return.columns.get_loc(arg) + 1, f'{arg}_withTech', 0)
    for (vehicle, alt) in st_vehicles:
        st, rc, ft = vehicle
        adjustment = adj_dict[(vehicle, alt)]['percent']
        growth = adj_dict[(vehicle, alt)]['growth']
        for arg in args_with_tech:
            arg_with_tech = df_return.loc[(df_return['optionID'] == alt)
                                          & (df_return['sourceTypeID'] == st)
                                          & (df_return['regClassID'] == rc)
                                          & (df_return['fuelTypeID'] == ft), arg] * adjustment * (1 + growth)
            df_return.loc[(df_return['optionID'] == alt)
                          & (df_return['sourceTypeID'] == st)
                          & (df_return['regClassID'] == rc)
                          & (df_return['fuelTypeID'] == ft), f'{arg}_withTech'] = arg_with_tech

    return df_return


def regclass_vehicles(fleet_df):
    """

    Parameters:
        fleet_df: A DataFrame of the project fleet.

    Returns:
        A series of unique vehicles where a vehicle is a ((regClass, fuelType), alt) vehicle.

    """
    return pd.Series(zip(zip(fleet_df['regClassID'], fleet_df['fuelTypeID']), fleet_df['optionID'])).unique()


def sourcetype_vehicles(fleet_df):
    """

    Parameters:
        fleet_df: A DataFrame of the project fleet.

    Returns:
        A series of unique vehicles where a vehicle is a ((sourceType, regClass, fuelType), alt) vehicle.

    """
    return pd.Series(zip(zip(fleet_df['sourceTypeID'], fleet_df['regClassID'], fleet_df['fuelTypeID']), fleet_df['optionID'])).unique()


if __name__ == '__main__':
    from bca_tool_code.tool_setup import SetInputs as settings
    from bca_tool_code.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)
    print(f'\n{vehicles_rc}\n')

    vehicles_st = sourcetype_vehicles(project_fleet_df)
    print(f'\n{vehicles_st}\n')
