import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class UsefulLife:
    """

    The UsefulLife class reads the useful life input file and provides methods to query its contents.

    """

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):
        UsefulLife._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['period']))
        df.set_index(key, inplace=True)

        UsefulLife._dict = df.to_dict('index')

    @staticmethod
    def get_attribute_value(key, attribute_name):

        return UsefulLife._dict[key][attribute_name]
