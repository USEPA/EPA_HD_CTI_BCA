import pandas as pd
import numpy as np
from pathlib import PurePath
import os
import sys
import time
from math import log10, floor


def inputs_filenames(input_files_pathlist):
    """

    Args:
        input_files_pathlist: A list of those input files that are specified in the Input_Files.csv file contained in the inputs folder.

    Returns: A list of input file full paths - these will be copied directly to the output folder so that inputs and outputs end up bundled together
        in the output folder associated with the given run.

    """
    _filename_list = [PurePath(path).name for path in input_files_pathlist]
    return _filename_list


def reshape_df(df, value_variable_list, cols_to_melt, melted_header, new_column_name):
    """

    Args:
        df: The DataFrame to melt.
        value_variable_list: Column(s) list to use as identifier variables.
        cols_to_melt: Column(s) list of columns to pivot (melt).
        melted_header: The header for the column to be populated with the cols_to_melt list.
        new_column_name: Name to use for the ‘Value’ column.

    Returns: A new DataFrame in long and narrow shape rather than the passed short and wide shape.

    """
    df = df.melt(id_vars=value_variable_list,
                 value_vars=cols_to_melt, var_name=melted_header,
                 value_name=new_column_name)
    return df


def convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args):
    """This function converts dollars into a consistent dollar basis as set via the get_context_data module.

    Args:
        df: A DataFrame containing monetized values and their associated cost basis.
        deflators: A dictionary of GDP deflators for use in adjusting monetized values throughout the tool into a consistent dollar basis.
        dollar_basis: The dollar basis to be used throughout the analysis. This is determined by the get_context_data module.
        *args: Arguments within the passed df to be adjusted into 'dollar_basis' dollars.

    Returns: The passed DataFrame will all args adjusted into dollar_basis dollars.

    """
    dollar_years = pd.Series(pd.DataFrame(df.loc[df['DollarBasis'] > 1])['DollarBasis'].unique())
    for year in dollar_years:
        for arg in args:
            df.loc[df['DollarBasis'] == year, arg] = df[arg] * deflators[year]['adjustment_factor']
        df.loc[df['DollarBasis'] == year, 'DollarBasis'] = dollar_basis
    return df


def round_metrics(df, metrics, round_by):
    """Note - this function is not being used.

    Args:
        df: DataFrame containing data to be rounded.
        metrics: List of metrics within the passed DataFrame for which rounding is requested.
        round_by: A value that sets the level of rounding.

    Returns: The passed DataFrame with 'metrics' rounded by 'round_by'.

    """
    df[metrics] = df[metrics].round(round_by)
    return df


def round_sig(df, divisor=1, sig=0, *args):
    """

    Args:
        df: The DataFrame containing data to be expressed in 'sig' significant digits.
        divisor: The divisor to use in calculating results.
        sig: The number of significant digits to use for results.
        *args: The arguments to be expressed in 'sig' significant digits and in 'divisor' units.

    Returns: The passed DataFrame with args expressed in 'sig' significant digits and in 'divisor' units.

    """
    for arg in args:
        df.loc[(df[arg] != np.nan) & (df[arg] != 0), arg] \
            = df.loc[(df[arg] != np.nan) & (df[arg] != 0), arg].apply(lambda x: round(x / divisor, sig-int(floor(log10(abs(x / divisor))))-1))
    return df


def get_file_datetime(list_of_files):
    """

    Args:
        list_of_files: List of files for which datetimes are required.

    Returns: A DataFrame of input files (full path) and corresponding datetimes (date stamps) for those files.

    """
    file_datetime = pd.DataFrame()
    file_datetime.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
    file_datetime.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])
    return file_datetime


def read_input_files(path, input_file, usecols=None, index_col=None, skiprows=None, reset_index=False):
    """

    Args:
        path: The path to input files.
        input_file: The file (filename) to read.
        usecols: The columns to used in the returned DataFrame.
        index_col: The column to use as the index column of the returned DataFrame.
        skiprows: The number of rows to skip when reading the file.
        reset_index: True resets index, False does not.

    Returns: A DataFrame of the desired data from the passed input file.

    """
    try:
        pd.read_csv(path / f'{input_file}', usecols=usecols, index_col=index_col, skiprows=skiprows, error_bad_lines=False)
        print(f'File {input_file}.......FOUND.')
        if reset_index:
            return pd.read_csv(path / f'{input_file}', usecols=usecols, index_col=index_col, skiprows=skiprows, error_bad_lines=False).dropna().reset_index(drop=True)
        else:
            return pd.read_csv(path / f'{input_file}', usecols=usecols, index_col=index_col, skiprows=skiprows, error_bad_lines=False)
    except FileNotFoundError:
        print(f'File {input_file}......NOT FOUND in {path} folder.')
        sys.exit()


def get_common_metrics(df_left, df_right, ignore=None):
    """

    This function simply finds common metrics between 2 DataFrames being merged to ensure a safe merge.
    Args:
        df_left: The left DataFrame being merged.
        df_right: The right DataFrame being merged.
        ignore: Any columns (arguments) to ignore when finding common metrics.

    Returns: A DataFrame merged on the common arguments (less any ignored arguments).

    """
    if ignore:
        cols_left = df_left.columns.tolist()
        cols_right = df_right.columns.tolist()
        for item in ignore:
            if item in cols_left:
                cols_left.remove(item)
            if item in cols_right:
                cols_right.remove(item)
        cols = [col for col in df_left[cols_left] if col in df_right[cols_right]]
    else:
        cols = [col for col in df_left.columns if col in df_right.columns]
    if cols != []:
        return cols
    else:
        return


def save_dict_to_csv(dict_to_save, save_path, *args):
    """

    Args:
        dict_to_save: A dictionary having a tuple of args as keys.
        save_path: The path for saving the passed CSV.
        *args: The arguments contained in the tuple key - these will be pulled out and named according to the passed arguments.

    Returns: A CSV file with individual key elements split out into columns with args as names.

    """
    print('Saving dictionary to CSV.')
    df = pd.DataFrame(dict_to_save).transpose()
    df.reset_index(inplace=True)
    for idx, arg in enumerate(args):
        df.rename(columns={f'level_{idx}': arg}, inplace=True)
    df.to_csv(f'{save_path}.csv', index=False)
    return


def convert_dict_to_df(dict_to_convert, *args):
    """

    Args:
        dict_to_convert: A dictionary meant for conversion to a DataFrame.
        *args: The arguments to use as column names for the separated keys.

    Returns: A DataFrame containing the passed dictionary of data.

    """
    print('Converting dictionary to DataFrame.')
    df = pd.DataFrame(dict_to_convert).transpose()
    df.reset_index(inplace=True)
    for idx, arg in enumerate(args):
        df.rename(columns={f'level_{idx}': arg}, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
