import pandas as pd
from cti_bca_tool.repair_costs import calc_per_veh_cumulative_vmt

def create_fleet_totals_dict(fleet_df, rate=0):
    """

    Args:
        fleet_df: A DataFrame of the project fleet.
        rate: The discount rate to associate with the passed data.

    Returns: A dictionary of the fleet having keys equal to ((vehicle), modelYearID, ageID, discount_rate) where vehicle is a tuple representing
        an alt_sourcetype_regclass_fueltype vehicle, and values representing totals for each key over time.

    """
    df = fleet_df.copy()
    df.insert(0, 'DiscountRate', rate)
    id = pd.Series(zip(zip(df['optionID'], fleet_df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'], df['ageID'], df['DiscountRate']))
    df.insert(0, 'id', id)
    df.drop(columns=['modelYearID', 'ageID', 'DiscountRate'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_fleet_averages_dict(fleet_df, rate=0):
    """

    Args:
        fleet_df: A DataFrame of the project fleet.
        rate: The discount rate to associate with the passed data.

    Returns: A dictionary of the fleet having keys equal to ((vehicle), modelYearID, ageID, discount_rate) where vehicle is a tuple representing
        an alt_sourcetype_regclass_fueltype vehicle, and values representing per vehicle or per mile averages for each key over time.

    """
    df = pd.DataFrame(fleet_df[['OptionName', 'optionID', 'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName',
                                'fuelTypeID', 'fuelTypeName', 'yearID', 'modelYearID', 'ageID']]).reset_index(drop=True)
    df.insert(0, 'DiscountRate', rate)
    id = pd.Series(zip(zip(df['optionID'], df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'], df['ageID'], df['DiscountRate']))
    df.insert(0, 'id', id)
    df.drop(columns=['modelYearID', 'ageID', 'DiscountRate'], inplace=True)
    df.insert(len(df.columns), 'VMT_AvgPerVeh', fleet_df['VMT'] / fleet_df['VPOP'])
    df.set_index('id', inplace=True)
    return_dict = df.to_dict('index')
    return_dict = calc_per_veh_cumulative_vmt(return_dict)
    return return_dict


def create_regclass_sales_dict(fleet_df):
    """

    Args:
        fleet_df: A DataFrame of the project fleet.

    Returns: A dictionary of the fleet having keys equal to ((vehicle), modelYearID) where vehicle is a tuple representing
        an alt_regclass_fueltype vehicle, and values representing sales (sales=VPOP at ageID=0) for each key by model year.

    """
    df = fleet_df.copy()
    df = pd.DataFrame(df.loc[df['ageID'] == 0, ['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'VPOP']]).reset_index(drop=True)
    df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID'], as_index=False).sum()
    df.insert(0, 'id', pd.Series(zip(zip(df['optionID'], df['regClassID'], df['fuelTypeID']), df['modelYearID'])))
    df.drop(columns=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_moves_adjustments_dict(input_df, *args):
    """

    Args:
        input_df: A DataFrame of the MOVES adjustments input file.
        *args: Vehicle parameters to adjust.

    Returns: The passed DataFrame as a dictionary.

    """
    df = input_df.copy()
    cols = [arg for arg in args]
    id = pd.Series(zip(df[cols[0]], df[cols[1]], df[cols[2]]))
    df.insert(0, 'id', id)
    df.drop(columns=cols, inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_seedvol_factor_dict(input_df):
    """

    Args:
        input_df: A DataFrame that provides seed volume factors by optionID, regClassID and fuelTypeID.

    Returns: The passed DataFrame as a dictionary.

    """
    df = input_df.copy()
    id = pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID']))
    df.insert(0, 'id', id)
    df.drop(columns=['optionID', 'regClassID', 'fuelTypeID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_markup_inputs_dict(input_df):
    """

    Args:
        input_df: A DataFrame that provides indirect cost markup factor values by fuelTypeID.

    Returns: A dictionary with 'fueltype, markup factor' keys and 'markup value' values.

    """
    df = input_df.copy()
    # insert a unique id to use as a dictionary key
    df.insert(0, 'id', pd.Series(zip(df['fuelTypeID'], df['Markup_Factor'])))
    df.set_index('id', inplace=True)
    df.drop(columns=['fuelTypeID', 'Markup_Factor'], inplace=True)
    return df.to_dict('index')


def create_required_miles_and_ages_dict(warranty_inputs, warranty_id, usefullife_inputs, usefullife_id):
    """

    Args:
        warranty_inputs: A DataFrame of the warranty inputs.
        warranty_id: A string "Warranty."
        usefullife_inputs: A DataFrame of the useful life Inputs.
        usefullife_id: A string "Usefullife."

    Returns: A single dictionary having keys equal to ((vehicle), identifier, period) where vehicle is an alt_regclass_fueltype
        vehicle, identifier is "Warranty" or "Usefullife" and period is "Age" or "Miles" and having values consistent with the passed DataFrames.

    """
    df_all = pd.DataFrame()
    df1 = warranty_inputs.copy()
    df2 = usefullife_inputs.copy()
    df1.insert(0, 'identifier', f'{warranty_id}')
    df2.insert(0, 'identifier', f'{usefullife_id}')
    for df in [df1, df2]:
        df.insert(0, 'id', pd.Series(zip(zip(df['optionID'], df['regClassID'], df['fuelTypeID']), df['identifier'], df['period'])))
        df = df[['id'] + [col for col in df.columns if '20' in col]]
        df_all = pd.concat([df_all, df], axis=0, ignore_index=True)
    df_all.set_index('id', inplace=True)
    dict_return = df_all.to_dict('index')
    return dict_return


def create_def_doserate_inputs_dict(input_df):
    """

    Args:
        input_df: A DataFrame of the DEF dose rate inputs file.

    Returns: A dictionary having keys equal to (regclassID, fuelTypeID) and values consisting of the DEF dose rate inputs for each key.

    """
    df = input_df.copy()
    id = pd.Series(zip(df['regClassID'], df['fuelTypeID']))
    df.insert(0, 'id', id)
    df.drop(columns=['regClassID', 'fuelTypeID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_def_prices_dict(input_df):
    """

    Args:
        input_df: A DataFrame of the DEF prices.

    Returns: A dictionary of the passed DEF prices.

    """
    df = input_df.copy()
    df.set_index('yearID', inplace=True)
    return df.to_dict('index')


def create_orvr_inputs_dict(input_df):
    """

    Args:
        input_df: A DataFrame of the ORVR inputs.

    Returns: A dictionary of the passed ORVR inputs.

    """
    df = input_df.copy()
    id = pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID']))
    df.insert(0, 'id', id)
    df.drop(columns=['optionID', 'regClassID', 'fuelTypeID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_fuel_prices_dict(input_df):
    """

    Args:
        input_df: A DataFrame of the fuel prices to be used in the given run.

    Returns: A dictionary of the passed fuel prices by yearID and fuelTypeID.

    """
    df = input_df.copy()
    id = pd.Series(zip(df['yearID'], df['fuelTypeID']))
    df.insert(0, 'id', id)
    df.drop(columns=['yearID', 'fuelTypeID'], inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_repair_inputs_dict(input_df):
    """

    Args:
        input_df: A DataFrame of the repair cost curve inputs.

    Returns: A dictionary of the passed DataFrame.

    """
    df = input_df.copy()
    df.set_index('Metric', inplace=True)
    return df.to_dict('index')


def create_criteria_cost_factors_dict(input_df):
    """

    Args:
        input_df: A DataFrame of the criteria cost factor inputs.

    Returns: A dictionary of the passed DataFrame.

    """
    df = input_df.copy()
    df.set_index('yearID', inplace=True)
    return df.to_dict('index')


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df

    project_fleet_df = create_fleet_df(settings)
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_dict = create_fleet_totals_dict(project_fleet_df)

    moves_adjustments_dict = create_moves_adjustments_dict(settings.moves_adjustments, 'optionID', 'regClassID', 'fuelTypeID')
    seedvol_factor_dict = create_seedvol_factor_dict(settings.regclass_learningscalers)
    markup_inputs_dict = create_markup_inputs_dict(settings.markups)
