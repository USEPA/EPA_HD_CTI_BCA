import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file


class InputFiles:
    """

    The InputFiles class reads the InputFiles.csv file and provides methods to query its contents.

    """

    input_files_df = pd.DataFrame()
    input_files_pathlist = list() # this list is updated when class objects are initiated.

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
