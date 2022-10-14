"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the warranty cost per year of warranty coverage.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        regClassName,regClassID,FuelName,fuelTypeID,Cost,DollarBasis,
        LHD,41,Gasoline,1,0,,
        LHD45,42,Gasoline,1,1000,2018,EMA public comments at page 151
        MHD67,46,Gasoline,1,1000,2018,ibid
        HHD8,47,Gasoline,1,1000,2018,ibid
        UrbanBus,48,Gasoline,1,0,,
        LHD,41,Diesel,2,1000,2018,ibid
        LHD45,42,Diesel,2,1000,2018,ibid
        MHD67,46,Diesel,2,1000,2018,ibid
        HHD8,47,Diesel,2,1000,2018,ibid
        UrbanBus,48,Diesel,2,1000,2018,ibid
        LHD,41,CNG,3,0,,
        LHD45,42,CNG,3,0,,
        MHD67,46,CNG,3,0,,
        HHD8,47,CNG,3,1000,2018,ibid
        UrbanBus,48,CNG,3,1000,2018,ibid

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


class BaseWarrantyCosts:
    """

    The BaseWarrantyCosts class reads the appropriate warranty costs input file and converts all dollar values to
    dollar_basis_analysis dollars and provides methods to query the data.

    """
    def __init__(self):
        self._dict = dict()
        self.piece_costs_in_analysis_dollars = pd.DataFrame()
        self.value_name = 'Cost'

    def init_from_file(self, filepath, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.\n
            general_inputs: object; the GeneralInputs class object.\n
            deflators: object; the Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x)

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, self.value_name)

        self.piece_costs_in_analysis_dollars = df.copy()

        df.drop(columns='DollarBasis', inplace=True)

        key = pd.Series(zip(
            df['regClassID'],
            df['fuelTypeID'],
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_warranty_cost(self, key):
        """

        Parameters:
            key: tuple; the engine_id.

        Returns:
            The warranty cost for the passed engine_id under option_id.

        """
        return self._dict[key][self.value_name]
