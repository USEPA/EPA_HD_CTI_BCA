"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the share of engines sold with an extended warranty along with the length of that extended warranty.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        regClassName,regClassID,FuelName,fuelTypeID,period_id,Share,Base,Extended
        HHD8,47,Diesel,2,Miles,1,100000,250000
        HHD8,47,CNG,3,Miles,1,100000,250000
        MHD67,46,Diesel,2,Miles,0.5,100000,150000
        MHD67,46,CNG,3,Miles,0.5,100000,150000

Data Column Name and Description
    :regClassName:
        The MOVES regulatory class name corresponding to the regClassID.

    :regClassID:
            The MOVES regClass ID, an integer.

    :FuelName:
        The MOVES fuel type name corresponding to the fuelTypeID.

    :fuelTypeID:
        The MOVES fuel type ID, an integer, where 1=Gasoline, 2=Diesel, etc.

    :Cost:
        The cost per year of warranty coverage.

    :DollarBasis:
        The dollar basis (dollars valued in what year) for the corresponding cost; costs are converted to analysis
        dollars in-code.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class WarrantyExtended:
    """

    The WarrantyExtended class reads the appropriate extended_warranty_share input file  and provides methods to
    query the data.

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
            )
        )
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_scaler(self, vehicle):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.

        Returns:
            The share with extended warranty for the passed engine_id under the option_id option and the scaler to apply
            to the base warranty cost.

        """
        engine_id = vehicle.engine_id
        key = engine_id
        base_miles = self._dict[key]['Base']
        extended_miles = self._dict[key]['Extended'] - base_miles
        share = self._dict[key]['Share']

        scaler = share * extended_miles / base_miles

        return scaler

    def get_required_miles_with_share(self, engine_id):
        """

        Parameters:
            engine_id: tuple; the engine_id (regclass_id, fueltype_id).

        Returns:
            The extended warranty miles and the share with extended warranty.

        """
        # engine_id, option_id = vehicle.engine_id, vehicle.option_id
        key = engine_id
        extended_miles = self._dict[key]['Extended']
        share = self._dict[key]['Share']

        return extended_miles, share

    def get_share(self, engine_id):
        """

        Parameters:
            engine_id: tuple; the engine_id (regclass_id, fueltype_id).

        Returns:
            The share with extended warranty.

        """
        key = engine_id
        share = self._dict[key]['Share']

        return share
