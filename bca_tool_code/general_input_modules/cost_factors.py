"""
This module was not used to support the HD2027 FRM so there is no input file(s).

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class CostFactors:

    """

    The CostFactors class reads the cost factors input file and provides methods to query contents.

    """
    def __init__(self):
        self._dict = dict()
        self.factors = list()
        self.factors_in_analysis_dollars = pd.DataFrame()

    def init_from_file(self, filepath, general_inputs, deflators=None):
        """

        Parameters:
            filepath: Path to the specified file.
            general_inputs: object; the GeneralInputs class object.\n
            deflators: object; the appropriate deflators object (CPI or GDP-based).

        Returns:
            Reads file at filepath, creates a dictionary and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        self.factors = [col for col in df.columns if 'year_id' not in col and 'DollarBasis' not in col]

        if deflators:
            df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, *self.factors)

        self.factors_in_analysis_dollars = df.copy()

        df.drop(columns='DollarBasis', inplace=True)
        key = df['year_id']
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_factors(self, year_id):
        """

        Parameters:
            year_id: int; the calendar year for which emission cost factors are needed.

        Returns:
            A dictionary of dollar per ton cost factors for the passed year_id.

        Note:
            Note that the BCA_General_Inputs file contains a toggle to stipulate whether to estimate emission (pollution)
            costs or not. This function is called only if that toggle is set to 'Y' (yes). The default setting is
            'N' (no).

        """
        factor_dict = dict()
        for factor in self.factors:
            factor_dict.update({factor: self._dict[year_id][factor]})

        return factor_dict
