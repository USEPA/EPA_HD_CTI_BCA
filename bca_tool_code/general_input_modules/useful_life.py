import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class UsefulLife:
    """

    The UsefulLife class reads the useful life input file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        value_name = 'period_value'

        df = pd.melt(df,
                     id_vars=['optionID', 'regClassName', 'regClassID', 'fuelTypeID', 'period_id'],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='start_year',
                     value_name=value_name
                     )
        df['start_year'] = pd.to_numeric(df['start_year'])

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['start_year'], df['period_id']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: tuple; ((regclass_id, fueltype_id), option_id, period), where period is 'Miles' or 'Age'.\n
            year_id: str; the year for which a value is sought.

        Returns:
            A single value associated with the year_id for the given key.

        """
        return self._dict[key][attribute_name]
