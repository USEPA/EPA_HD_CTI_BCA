import pandas as pd


def create_project_dict(input_df, *args):
    """

    Parameters:
        input_df: A DataFrame of the MOVES adjustments input file.\n
        args: Vehicle parameters to adjust.

    Returns:
        The passed DataFrame as a dictionary.

    """
    df = input_df.copy()
    cols = [arg for arg in args]
    len_cols = len(cols)
    if len_cols == 2: id = pd.Series(zip(df[cols[0]], df[cols[1]]))
    elif len_cols == 3: id = pd.Series(zip(zip(df[cols[0]], df[cols[1]]), df[cols[2]]))
    elif len_cols == 4: id = pd.Series(zip(zip(df[cols[0]], df[cols[1]], df[cols[2]]), df[cols[3]]))
    else:
        print('Improper number of args passed to function.')
    df.insert(0, 'id', id)
    df.drop(columns=cols, inplace=True)
    df.set_index('id', inplace=True)
    return df.to_dict('index')


def create_required_miles_and_ages_dict(warranty_inputs, warranty_id, usefullife_inputs, usefullife_id):
    """

    Parameters:
        warranty_inputs: A DataFrame of the warranty inputs.\n
        warranty_id: A string "Warranty."\n
        usefullife_inputs: A DataFrame of the useful life Inputs.\n
        usefullife_id: A string "Usefullife."

    Returns:
        A single dictionary having keys equal to ((vehicle), identifier, period) where vehicle is an alt_regclass_fueltype
        vehicle, identifier is "Warranty" or "Usefullife" and period is "Age" or "Miles" and having values consistent with the passed DataFrames.

    """
    df_all = pd.DataFrame()
    df1 = warranty_inputs.copy()
    df2 = usefullife_inputs.copy()
    df1.insert(0, 'identifier', f'{warranty_id}')
    df2.insert(0, 'identifier', f'{usefullife_id}')
    for df in [df1, df2]:
        df.insert(0, 'id', pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['identifier'], df['period'])))
        df = df[['id'] + [col for col in df.columns if '20' in col]]
        df_all = pd.concat([df_all, df], axis=0, ignore_index=True)
    df_all.set_index('id', inplace=True)
    dict_return = df_all.to_dict('index')
    return dict_return


def create_def_prices_dict(input_df):
    """

    Parameters:
        input_df: A DataFrame of the DEF prices.

    Returns:
        A dictionary of the passed DEF prices.

    """
    df = input_df.copy()
    df.set_index('yearID', inplace=True)
    return df.to_dict('index')


def create_criteria_cost_factors_dict(input_df):
    """

    Parameters:
        input_df: A DataFrame of the criteria cost factor inputs.

    Returns:
        A dictionary of the passed DataFrame.

    """
    df = input_df.copy()
    df.set_index('yearID', inplace=True)
    return df.to_dict('index')


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
