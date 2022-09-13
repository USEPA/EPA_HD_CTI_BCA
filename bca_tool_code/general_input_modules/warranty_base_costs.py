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
            key: tuple; (engine_id).

        Returns:
            The warranty cost for the passed engine_id under option_id.

        """
        return self._dict[key][self.value_name]
