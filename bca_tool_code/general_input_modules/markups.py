import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Markups:
    """

    The Markups class reads the Markups input file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.markup_factor_names = list()

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['fuelTypeID'], df['optionID'], df['Markup_Factor']))
        df.set_index(key, inplace=True)

        self.markup_factor_names = [arg for arg in df['Markup_Factor'].unique()]

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: tuple; (fueltype_id, option_id, markup_factor), where markup_factor is, e.g., 'Warranty', RnD'.\n
            attribute_name: str; the attribute name for which a value is sought.

        Returns:
            A single value associated with the attribute name for the given key.

        """
        return self._dict[key][attribute_name]

    def get_attribute_values(self, key):
        """

        Parameters:
            key: tuple; (fueltype_id, option_id, markup_factor), where markup_factor is, e.g., 'Warranty', RnD'.

        Returns:
            A list of values for the given key.

        """
        values_list = list()
        for attribute_name in ['Value', 'Scaler', 'Scaled_by', 'NumberOfYears']:
            values_list.append(self.get_attribute_value(key, attribute_name))

        return values_list
