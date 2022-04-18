import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class DefPrices:
    """

    The DefPrices class reads the DEF prices file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.def_prices_in_analysis_dollars = pd.DataFrame()

    def init_from_file(self, filepath, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.
            general_inputs: The GeneralInputs class object.
            deflators: The Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'DEF_USDperGal')

        self.def_prices_in_analysis_dollars = df.copy()

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_price(self, year_id):

        return self._dict[year_id]['DEF_USDperGal']
