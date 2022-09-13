import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class DefDoseRates:
    """

    The DefDoseRates class reads the DEF dose rates file and provides methods to query its contents.

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
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['regClassID'], df['fuelTypeID']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_curve_coefficients(self, engine):
        """

        Parameters:
            engine: tuple; (regclass_id, fueltype_id).

        Returns:
            The slope and intercept curve coefficients for calculating DEF doserate.

        """
        slope, intercept = self._dict[engine]['slope_DEFdoserate'], \
                           self._dict[engine]['intercept_DEFdoserate']

        return slope, intercept

    def get_attribute_value(self, engine, attribute_name):
        """

        Parameters:
            engine: tuple; (regclass_id, fueltype_id).
            attribute_name: str; the attribute name for which a value is sought.

        Returns:
            The slope and intercept curve coefficients for calculating DEF doserate.

        """
        return self._dict[engine][attribute_name]
