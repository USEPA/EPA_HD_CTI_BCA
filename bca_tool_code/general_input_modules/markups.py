import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Markups:
    """

    The Markups class reads the Markups input file and provides methods to query its contents.

    """

    _dict = dict()
    markup_factor_names = list()

    @staticmethod
    def init_from_file(filepath):

        Markups._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['fuelTypeID'], df['optionID'], df['Markup_Factor']))
        df.set_index(key, inplace=True)

        Markups.markup_factor_names = [arg for arg in df['Markup_Factor'].unique()]

        Markups._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.input_files_pathlist.append(filepath)

    @staticmethod
    def get_attribute_value(key, attribute_name):

        return Markups._dict[key][attribute_name]
