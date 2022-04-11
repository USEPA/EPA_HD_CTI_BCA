import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file


class MovesAdjCAP:
    """

    The MovesAdjCAP class reads the MOVES adjustments file and provides methods to query its contents.

    """

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        MovesAdjCAP._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        MovesAdjCAP._dict = df.to_dict('index')

    @staticmethod
    def get_attribute_value(vehicle, alt, attribute_name):

        return MovesAdjCAP._dict[vehicle, alt][attribute_name]
