import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class SourceTypeCosts:
    """

    The SourceTypeCosts class reads the sourcetype_costs input file and converts all dollar values to dollar_basis_analysis
    dollars.

    """
    def __init__(self):
        self._dict = dict()
        self.cost_steps = list()
        self.sourcetype_costs_in_analysis_dollars = pd.DataFrame()

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
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        self.cost_steps = [col for col in df.columns if '20' in col]

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, *self.cost_steps)

        self.sourcetype_costs_in_analysis_dollars = df.copy()

        df = df.groupby(by=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'DollarBasis'], axis=0,
                        as_index=False).sum()

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_cost(self, key, cost_step):
        step = cost_step
        if type(step) is not str:
            step = f'{step}'
        return self._dict[key][step]
