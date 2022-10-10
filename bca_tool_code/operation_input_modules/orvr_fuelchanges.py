"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the milliliters of gasoline available to burn for work for every gram of hydrocarbon captured.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        optionID,regClassID,fuelTypeID,ml/g
        0,41,1,0
        0,42,1,0
        0,46,1,0
        0,47,1,0
        0,48,1,0
        1,41,1,0
        1,42,1,1.48
        1,46,1,1.48
        1,47,1,1.48
        1,48,1,1.48

Data Column Name and Description
    :optionID:
        The option or alternative number.

    :regClassID:
        The MOVES regClass ID, an integer.

    :fuelTypeID:
        The MOVES fuel type ID, an integer, where 1=Gasoline, 2=Diesel, etc.

    :ml/g:
        The milliliters of gasoline per gram of hydrocarbon.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class OrvrFuelChanges:
    """

    The OrvrFuelChanges class reads the orvr_fuelchanges_cap file and provides methods to query its contents.

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

        key = pd.Series(zip(
            zip(
                df['regClassID'],
                df['fuelTypeID']),
            df['optionID']
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_ml_per_gram(self, engine, alt):
        """

        Parameters:
            engine: tuple; (regclass_id, fueltype_id). \n
            alt: int; the option_id.

        Returns:
            The milliliters of gasoline per gram of hydrocarbon captured that is available to be burned in the engine.

        """
        return self._dict[engine, alt]['ml/g']
