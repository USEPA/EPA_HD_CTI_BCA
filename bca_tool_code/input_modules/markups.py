import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class Markups:
    """

    The Markups class reads the Markups input file and provides methods to query its contents.

    """

    _data = dict()
    markup_factor_names = list()

    @staticmethod
    def init_from_file(filepath):

        Markups._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['fuelTypeID'], df['optionID'], df['Markup_Factor']))
        df.set_index(key, inplace=True)

        Markups.markup_factor_names = [arg for arg in df['Markup_Factor'].unique()]

        Markups._data = df.to_dict('index')

    @staticmethod
    def get_attribute_value(key, attribute_name):

        return Markups._data[key][attribute_name]
