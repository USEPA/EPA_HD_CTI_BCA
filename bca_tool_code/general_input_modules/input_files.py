"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the input file names to use for the given run.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        DoNotChange,UserEntry.csv,Notes
        bca_inputs,BCA_General_Inputs.csv,
        options_cap,Options_CAP_os0622.csv,
        fuel_prices,Components_of_Selected_Petroleum_Product_Prices.csv,
        deflators,Table_1.1.9_ImplicitPriceDeflators.csv,

Data Column Name and Description
    :DoNotChange:
        The file type associated, in-code, with the UserEntry.csv file name; these entries should not be changed.

    :UserEntry.csv:
        The user provided file name to use, including the '.csv' extension. Files must be CSV format.

    :Notes:
        Optional notes provided by the user; notes are ignored in-code.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file


class InputFiles:
    """

    The InputFiles class reads the InputFiles.csv file and provides methods to query its contents.

    """
    input_files_df = pd.DataFrame()
    input_files_pathlist = list() # this list is updated when class objects are instantiated.

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
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        self.input_files_df = df.copy()

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        self.input_files_pathlist.append(filepath)

    def get_filename(self, file_id):
        """

        Parameters:
            file_id: str; the file_id stipulated in the InputFiles.csv file (e.g., bca_inputs).

        Returns:
            The name of the CSV file (e.g., BCA_General_Inputs.csv) associated with the given file_id
            (e.g., bca_inputs).

        """

        return self._dict[file_id]['UserEntry.csv']

    @staticmethod
    def update_pathlist(filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Updates input_files_pathlist with the passed path.

        """
        InputFiles.input_files_pathlist.append(filepath)
