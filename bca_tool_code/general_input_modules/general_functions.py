import pandas as pd
from pathlib import PurePath
import os
import sys
import time


def inputs_filenames(input_files_pathlist):
    """

    Parameters:
        input_files_pathlist: List; those input files that are specified in the Input_Files.csv file contained in the inputs folder.

    Returns:
        A list of input file full paths - these will be copied directly to the output folder so that inputs and outputs
        end up bundled together in the output folder associated with the given run.

    """
    _filename_list = [PurePath(path).name for path in input_files_pathlist]

    return _filename_list


def get_file_datetime(list_of_files):
    """

    Parameters:
        list_of_files: List; the files for which datetimes are required.

    Returns:
        A DataFrame of input files (full path) and corresponding datetimes (date stamps) for those files.

    """
    file_datetime = pd.DataFrame()
    file_datetime.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
    file_datetime.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])

    return file_datetime


def read_input_file(path, usecols=None, index_col=None, skiprows=None, reset_index=False):
    """

    Parameters:
        path: Path to the specified file.\n
        usecols: List; the columns to use in the returned DataFrame.\n
        index_col: int; the column to use as the index column of the returned DataFrame.\n
        skiprows: int; the number of rows to skip when reading the file.\n
        reset_index: Boolean; True resets index, False does not.

    Returns:
        A DataFrame of the desired data from the passed input file.

    Note:
        If a file is not found, the code issues an exit command and stops.

    """
    try:
        pd.read_csv(path, usecols=usecols, index_col=index_col, skiprows=skiprows, on_bad_lines='skip')
        print(f'File {path}.......FOUND.')
        if reset_index:
            return pd.read_csv(path, usecols=usecols, index_col=index_col, skiprows=skiprows, on_bad_lines='skip').dropna().reset_index(drop=True)
        else:
            return pd.read_csv(path, usecols=usecols, index_col=index_col, skiprows=skiprows, on_bad_lines='skip')
    except FileNotFoundError:
        print(f'File {path}......NOT FOUND.')
        sys.exit()


def save_dict(dict_to_save, save_path, row_header=None, stamp=None, index=False):
    """

    Parameters:
        dict_to_save: Dictionary; the dictionary to be saved to CSV.\n
        save_path: Path object; the path for saving the passed dict_to_save.\n
        row_header: List; the column names to use as the row header for the preferred structure of the output file.\n
        stamp: str; an identifier for inclusion in the filename, e.g., datetime stamp.\n
        index: Boolean; True includes the index; False excludes the index.

    Returns:
        Saves the passed dictionary to a CSV file.

    """
    print('Saving dictionary to CSV.')
    df = pd.DataFrame(dict_to_save).transpose()
    if row_header:
        cols = [col for col in df.columns if col not in row_header]
        df = pd.DataFrame(df, columns=row_header + cols)

    df.to_csv(f'{save_path}_{stamp}.csv', index=index)

    return


def save_dict_return_df(dict_to_save, save_path, row_header=None, stamp=None, index=False):
    """

    Parameters:
        dict_to_save: Dictionary; the dictionary to be saved to CSV.\n
        save_path: Path object; the path for saving the passed dict_to_save.\n
        row_header: List; the column names to use as the row header for the preferred structure of the output file.\n
        stamp: str; an identifier for inclusion in the filename, e.g., datetime stamp.\n
        index: Boolean; True includes the index; False excludes the index.

    Returns:
        Saves the passed dictionary to a CSV file and returns a DataFrame based on the passed dictionary.

    """
    print('Saving dictionary to CSV.')
    df = pd.DataFrame(dict_to_save).transpose()
    if row_header:
        cols = [col for col in df.columns if col not in row_header]
        df = pd.DataFrame(df, columns=row_header + cols)

    df.to_csv(f'{save_path}_{stamp}.csv', index=index)

    return df
