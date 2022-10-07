"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent adjustments (multipliers) to be applied to certain MOVES data attributes (e.g., 'VPOP', 'VMT') to
account for vehicles covered or not covered in the analysis.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        optionID,sourceTypeName,sourceTypeID,regClassName,regClassID,FuelName,fuelTypeID,percent,growth
        0,Long-Haul Combination Trucks,62,Urban Bus,48,Gasoline,1,1,0
        0,Passenger Trucks,31,LHD,41,Diesel,2,0.051,0
        0,Passenger Trucks,31,LHD45,42,Diesel,2,1,0

Data Column Name and Description
    :optionID:
        The option or alternative number.

    :sourceTypeName:
        The MOVES source type name corresponding to the sourceTypeID.

    :sourceTypeID:
            The MOVES source type ID, an integer.

    :regClassName:
        The MOVES regulatory class name corresponding to the regClassID.

    :regClassID:
            The MOVES regClass ID, an integer.

    :FuelName:
        The MOVES fuel type name corresponding to the fuelTypeID.

    :fuelTypeID:
        The MOVES fuel type ID, an integer, where 1=Gasoline, 2=Diesel, etc.

    :percent:
        The multiplicative factor to be applied where appropriate.

    :growth:
        Not used.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class MovesAdjustments:
    """

    The MovesAdjustments class reads the MOVES adjustments file and provides methods to query its contents.

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

        key = pd.Series(zip
                        (zip(df['sourceTypeID'],
                             df['regClassID'],
                             df['fuelTypeID']),
                         df['optionID']
                         ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, vehicle, alt, attribute_name):
        """

        Parameters:
            vehicle: tuple; (sourcetype_id, regclass_id, fueltype_id), option_id.\n
            alt: int; the option_id.\n
            attribute_name: str; the attribute name for which a value is sought.

        Returns:
            A single value associated with the attribute name for the given key.

        """
        return self._dict[vehicle, alt][attribute_name]
