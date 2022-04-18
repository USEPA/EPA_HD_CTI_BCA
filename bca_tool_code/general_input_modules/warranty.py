import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Warranty:
    """

    The Warranty class reads the warranty input file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath):

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['period']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key, year_id):

        return self._dict[key][year_id]
