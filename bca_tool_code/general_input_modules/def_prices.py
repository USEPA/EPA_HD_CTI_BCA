"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the retail price of diesel exhaust fluid (DEF).

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        yearID,DEF_USDperGal,DollarBasis
        2012,2.6,2011
        2013,2.55,2011
        2014,2.5,2011

Data Column Name and Description
    :yearID:
        The calendar year, an integer.

    :DEF_USDperGal:
        The DEF retail price per gallon.

    :DollarBasis:
        The dollar value of the associated price; prices are converted to analysis dollars in code.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class DefPrices:
    """

    The DefPrices class reads the DEF prices file and provides methods to query contents.

    """
    def __init__(self):
        self._dict = dict()
        self.def_prices_in_analysis_dollars = pd.DataFrame()

    def init_from_file(self, filepath, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.
            general_inputs: object; the GeneralInputs class object.
            deflators: object; the Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'DEF_USDperGal')

        self.def_prices_in_analysis_dollars = df.copy()

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_price(self, year_id):
        """

        Parameters:
            year_id: int; the calendar year for which the price is sought.

        Returns:
            The DEF price per gallon for the passed year_id.

        """
        return self._dict[year_id]['DEF_USDperGal']
