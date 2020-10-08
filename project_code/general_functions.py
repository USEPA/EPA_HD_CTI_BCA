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
    :param input_files_pathlist: A list of those input files that are not modified in code.
    :type input_files_pathlist: List - currently hardcoded.
    :return: A list of input file paths - these will be copied directly to the output folder so that inputs and outputs end up bundled together in the output folder.
    """
    _filename_list = [PurePath(path).name for path in input_files_pathlist]
    return _filename_list


def reshape_df(df, value_variable_list, cols_to_melt, melted_header, new_column_name):
    """

    :param df: Data to melt.
    :type df: DataFrame
    :param value_variable_list: Column(s) to use as identifier variables.
    :type value_variable_list: List
    :param cols_to_melt: Column(s) to unpivot (melt).
    :type cols_to_melt: List - this is a list of columns determined in code that are to be melted.
    :param melted_header: The header for the column to be populated with the cols_to_melt list.
    :type melted_header: String
    :param new_column_name: Name to use for the ‘Value’ column.
    :type new_column_name: String
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
            df.loc[df['DollarBasis'] == year, arg] = df[arg] * deflators[year]['adjustment']
        df.loc[df['DollarBasis'] == year, 'DollarBasis'] = dollar_basis
    return df


def round_metrics(df, metrics, round_by):
    """

    :param df: DataFrame containing data to be rounded.
    :param metrics: List of metrics within the passed DataFrame for which rounding is requested.
    :param round_by: A value entered via the BCA_Inputs sheet contained in the inputs folder that sets the level of rounding.
    :return: The passed DataFrame with 'metrics' rounded by 'round_by'
    """
    df[metrics] = df[metrics].round(round_by)
    return df


def round_sig(df, metrics, divisor, sig=0):
    for metric in metrics:
        try:
            df[metric] = df[metric].apply(lambda x: round(x/divisor, sig-int(floor(log10(abs(x/divisor))))-1))
        except:
            df[metric].replace(to_replace=0, value=1, inplace=True)
            df[metric] = df[metric].apply(lambda x: round(x / divisor, sig - int(floor(log10(abs(x / divisor)))) - 1))
    return df


def get_file_datetime(list_of_files):
    file_datetime = pd.DataFrame()
    file_datetime.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
    file_datetime.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])
    return file_datetime


def cols_for_df(source_df, metrics):
    return_df = pd.DataFrame(source_df, columns=metrics)
    return return_df


def read_input_files(path_inputs, input_file, col_list, idx_col=None):
    try:
        pd.read_csv(path_inputs / f'{input_file}', usecols=col_list, index_col=idx_col)
        print(f'File {input_file}.......FOUND.')
        df_return = pd.read_csv(path_inputs / f'{input_file}', usecols=col_list, index_col=idx_col)
    except FileNotFoundError:
        print(f'File {input_file}......NOT FOUND in {path_inputs} folder.')
        sys.exit()
    return df_return


def get_common_metrics(df_left, df_right, ignore=None):
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
        print(f'No common columns found in {df_left} with {df_right} merge.')
        return


def pivot_table_of_results(df_source, index_list, function=None, *value_args):
    value_list = []
    for value_arg in value_args:
        value_list.append(value_arg)
    table = pd.pivot_table(df_source, aggfunc=function, values=value_list, index=index_list)
    return table
