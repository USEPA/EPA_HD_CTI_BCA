"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent a "seed volume factor" that serves to slow learning effects; the higher the seed volume factor the
slower the learning while a lower number results in more rapid learning.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        optionID,sourceTypeName,sourceTypeID,regClassName,regClassID,FuelName,fuelTypeID,SeedVolumeFactor,Notes
        0,Passenger Trucks,31,LHD,41,Gasoline,1,1,1 implies no learning to date but learning going forward
        0,Passenger Trucks,31,LHD45,42,Gasoline,1,1,SeedVolumeFactor set to 3 to imply 3 years of learning prior to first use thereby slowing learning beyond first use
        0,Passenger Trucks,31,MHD67,46,Gasoline,1,1,SeedVolumeFactor: 10 to slow learning beyond first use

Data Column Name and Description
    :optionID:
        The option or alternative number.

    :sourceTypeName:
        The MOVES source type name, a string.

    :sourceTypeID:
        The MOVES source type ID, an integer.

    :regClassName:
        The MOVES reg class name, a string.

    :regClassID:
        The MOVES regClassID, an integer.

    :FuelName:
        The MOVES fuel name, e.g., 'Gasoline', 'Diesel'.

    :fuelTypeID:
        The MOVES fuelTypeID, an integer.

    :SeedVolumeFactor:
        The value of the seed volume factor, an integer.

    :Notes:
        A string of notes pertinent to the data; Notes are ignored in code.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class VehicleLearningScalers:
    """

    The VehicleLearningScalers class reads the sourcetype_learning_scalers input file and provides methods to query its
    contents.

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

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))

        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_seedvolume_factor(self, vehicle_id, option_id):
        """

        Parameters:
            vehicle_id: tuple; (sourcetype_id, regclass_id, fueltype_id). \n
            option_id: int; the option_id.

        Returns:
            The seed volume factor for the given vehicle and option_id.

        """
        return self._dict[vehicle_id, option_id]['SeedVolumeFactor']

    def calc_learning_effect(self, vehicle, sales_year1, cumulative_sales, learning_rate):
        """

        Args:
            vehicle: object; an object of the Vehicle class.
            sales_year1: numeric; the sales in the first year of implementation of a new standard.
            cumulative_sales: numeric; the cumulative sales since and including the first year of implementation of a
            new standard.
            learning_rate: numeric; the learning rate set via the General Inputs file.

        Returns:
            The learning effect or factor to be applied to first year costs to reflect the learned cost after sales
            have totaled cumulative_sales.

        """
        seedvolume_factor = self.get_seedvolume_factor(vehicle.vehicle_id, vehicle.option_id)

        learning_effect = ((cumulative_sales + (sales_year1 * seedvolume_factor))
                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate

        return learning_effect
