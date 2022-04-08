import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class Warranty:
    """

    The Warranty class reads the warranty input file and provides methods to query its contents.

    """

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        Warranty._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['period']))
        df.set_index(key, inplace=True)

        Warranty._data = df.to_dict('index')

    @staticmethod
    def get_attribute_value(key, year_id):

        return Warranty._data[key][year_id]
