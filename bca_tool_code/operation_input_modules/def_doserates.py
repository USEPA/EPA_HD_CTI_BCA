"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the linear relationship used to estimate DEF dose rates using the equation
doserate = ((nox_std - nox_engine_out) - intercept) / slope

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        regClassID,fuelTypeID,engineout_NOx,standard_NOx,slope_DEFdoserate,intercept_DEFdoserate
        41,2,4,0.2,-73.679,0.0149
        42,2,4,0.2,-73.679,0.0149
        46,2,4,0.2,-73.679,0.0149
        47,2,4,0.2,-73.679,0.0149
        48,2,4,0.2,-73.679,0.0149

Data Column Name and Description
    :regClassID:
            The MOVES regClass ID, an integer.

    :fuelTypeID:
        The MOVES fuel type ID, an integer, where 1=Gasoline, 2=Diesel, etc.

    :engineout_NOx:
        The estimated engine-out NOx emissions in grams per brake horsepower hour.

    :standard_NOx:
        The tailpipe standard NOx emissions in grams per brake horsepower hour.

    :slope_DEFdoserate:
        The slope of the DEF doserate linear relationship.

    :intercept_DEFdoserate:
        The intercept of the DEF doserate linear relationship.

----

**CODE**

"""
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

        key = pd.Series(
            zip(
                df['regClassID'],
                df['fuelTypeID']
            ))
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
            The slope or intercept curve coefficient for calculating DEF doserate.

        """
        return self._dict[engine][attribute_name]
