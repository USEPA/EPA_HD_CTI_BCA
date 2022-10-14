"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the warranty provisions for the associated optionID.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        optionID,regClassName,regClassID,fuelTypeID,period_id,2024,2027,2031
        0,HHD8,47,1,Miles,50000,50000,50000,
        0,HHD8,47,1,Age,5,5,5,
        0,HHD8,47,3,Hours,,,,
        1,HHD8,47,3,Miles,100000,450000,450000,
        1,HHD8,47,3,Age,5,7,7,
        1,HHD8,47,1,Hours,,8000,8000,

Data Column Name and Description
    :optionID:
        The option or alternative number.

    :regClassName:
        The MOVES regulatory class name corresponding to the regClassID.

    :regClassID:
            The MOVES regClass ID, an integer.

    :fuelTypeID:
        The MOVES fuel type ID, an integer, where 1=Gasoline, 2=Diesel, etc.

    :period_id:
        The identifier, i.e., 'Miles', 'Age' or 'Hours'

    :2024:
        The miles/age/hours provision for MY2024 and later.

    :2027:
        The miles/age/hours provision for MY2027 and later.

    :2031:
        The miles/age/hours provision for MY2031 and later.

----

**CODE**

"""
import pandas as pd
import numpy as np

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Warranty:
    """

    The Warranty class reads the warranty input file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.start_years = list()
        self.value_name = 'period_value'

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x)

        df = df.replace(np.nan, None)

        # value_name = 'period_value'

        df = pd.melt(df,
                     id_vars=['optionID', 'regClassName', 'regClassID', 'fuelTypeID', 'period_id'],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='start_year',
                     value_name=self.value_name
                     )
        df['start_year'] = pd.to_numeric(df['start_year'])
        self.start_years = df['start_year'].unique()

        key = pd.Series(
            zip(
                zip(
                    df['regClassID'],
                    df['fuelTypeID']),
                df['optionID'],
                df['start_year'],
                df['period_id']
            )
        )
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: tuple; ((regclass_id, fueltype_id), option_id, modelyear_id, period_id), where period_id is 'Miles' or 'Age' or 'Hours'.\n
            attribute_name: str; the attribute name for which a value is sought (e.g., period_value).

        Returns:
            A single value associated with the period_id for the given key.

        """
        engine_id, option_id, my_id, period_id = key
        if my_id == min(self.start_years):
            year = my_id
        else:
            year = max([int(year) for year in self.start_years if int(year) <= my_id])
        new_key = (engine_id, option_id, year, period_id)

        return self._dict[new_key][attribute_name]
