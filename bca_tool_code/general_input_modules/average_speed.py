import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class AverageSpeed:
    """

    The AverageSpeed class reads the average speed input file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.attribute_name = 'AvgSpeed MPH'

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = df['sourceTypeID']

        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key):
        """

        Parameters:
            key: tuple; sourcetype_id, regclass_id

        Returns:
            A single value associated with the period_id for the given key.

        """
        return self._dict[key][self.attribute_name]
