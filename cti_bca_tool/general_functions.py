"""
general_functions.py

"""

import pandas as pd
from pathlib import PurePath
import os
import sys
import time
from math import log10, floor


def inputs_filenames(input_files_pathlist):
    """
    :param input_files_pathlist: A list of those input files that are specified in the Input_Files.csv file contained in the inputs folder.
    :return: A list of input file full paths - these will be copied directly to the output folder so that inputs and outputs end up bundled together in the output folder.
    """
    _filename_list = [PurePath(path).name for path in input_files_pathlist]
    return _filename_list


def reshape_df(df, value_variable_list, cols_to_melt, melted_header, new_column_name):
    """

    :param df: The DataFrame to melt.
    :param value_variable_list: Column(s) list to use as identifier variables.
    :param cols_to_melt: Column(s) list of columns to pivot (melt).
    :param melted_header: The header for the column to be populated with the cols_to_melt list.
    :param new_column_name: Name to use for the ‘Value’ column.
    :return: A new DataFrame in long and narrow shape rather than the passed short and wide shape.
    """
    df = df.melt(id_vars=value_variable_list,
                 value_vars=cols_to_melt, var_name=melted_header,
                 value_name=new_column_name)
    return df


def convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args):
    """

    This function converts dollars into a consistent dollar basis as set in the Inputs workbook.

    :param df: The passed DataFrame containing costs to convert.
    :param deflators: A dictionary of gdp price deflators and adjustments to be multiplied by costs.
    :param dollar_basis: The dollar basis of the analysis.
    :param args: Metrics to be converted to dollar_basis dollars.
    :return: The passed DataFrame with metric dollar values converted to dollar_basis dollars.
    """
    dollar_years = pd.Series(pd.DataFrame(df.loc[df['DollarBasis'] > 1])['DollarBasis'].unique())
    for year in dollar_years:
        for arg in args:
            df.loc[df['DollarBasis'] == year, arg] = df[arg] * deflators[year]['adjustment_factor']
        df.loc[df['DollarBasis'] == year, 'DollarBasis'] = dollar_basis
    return df


def round_metrics(df, metrics, round_by):
    """

    Note - this function is not being used.

    :param df: DataFrame containing data to be rounded.
    :param metrics: List of metrics within the passed DataFrame for which rounding is requested.
    :param round_by: A value entered via the BCA_Inputs sheet contained in the inputs folder that sets the level of rounding.
    :return: The passed DataFrame with 'metrics' rounded by 'round_by'
    """
    df[metrics] = df[metrics].round(round_by)
    return df


def round_sig(df, divisor=1, sig=0, *args):
    """

    :param df: The DataFrame containing data to be rounded.
    :param args: The metrics to be rounded.
    :param divisor: The divisor to use should results be desired in units other than those passed (set divisor=1 to maintain units).
    :param sig: The number of significant digits.
    :return: The passed DataFrame with args rounded to 'sig' digits and expressed in 'divisor' units.
    """
    for arg in args:
        try:
            df[arg] = df[arg].apply(lambda x: round(x/divisor, sig-int(floor(log10(abs(x/divisor))))-1))
        except:
            df[arg].replace(to_replace=0, value=1, inplace=True)
            df[arg] = df[arg].apply(lambda x: round(x / divisor, sig - int(floor(log10(abs(x / divisor)))) - 1))
    return df


def get_file_datetime(list_of_files):
    """

    :param list_of_files: List of files for which datetimes are required.
    :return: A DataFrame of input files (full path) and corresponding datetimes (date stamps) for those files.
    """
    file_datetime = pd.DataFrame()
    file_datetime.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
    file_datetime.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])
    return file_datetime


def read_input_files(path, input_file, usecols=None, index_col=None, skiprows=None, reset_index=False):
    """

    :param path: The path to the input file(s).
    :param input_file: The name of the input file.
    :param usecols: The columns to use (return).
    :param idx_col: The column to use as the row index.
    :param skiprows: The number of rows to skip.
    :return: A DataFrame of the desired data from the input file.
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

    :param df_left: The left DataFrame being merged.
    :param df_right: The right DataFrame being merged.
    :param ignore: Any columns (metrics) to ignore when finding common metrics.
    :return: A DataFrame merged on the common metrics (less any ignored metrics).
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
