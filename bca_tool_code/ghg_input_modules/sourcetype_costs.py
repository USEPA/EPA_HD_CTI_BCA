import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles
from bca_tool_code.general_input_modules.deflators import Deflators


class SourceTypeCosts:
    """

    The SourceTypeCosts class reads the sourcetype_costs input file and converts all dollar values to dollar_basis_analysis
    dollars.

    """

    _dict = dict()
    cost_steps = list()
    sourcetype_costs_in_analysis_dollars = pd.DataFrame()

    @staticmethod
    def init_from_file(filepath, general_inputs):

        SourceTypeCosts._dict.clear()
        SourceTypeCosts.cost_steps.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        SourceTypeCosts.cost_steps = [col for col in df.columns if '20' in col]

        df = Deflators.convert_dollars_to_analysis_basis(general_inputs, df, *SourceTypeCosts.cost_steps)

        SourceTypeCosts.sourcetype_costs_in_analysis_dollars = df.copy()

        df = df.groupby(by=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'DollarBasis'], axis=0,
                        as_index=False).sum()

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        SourceTypeCosts._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.input_files_pathlist.append(filepath)

    @staticmethod
    def get_cost(key, cost_step):
        step = cost_step
        if type(step) is not str:
            step = f'{step}'
        return SourceTypeCosts._dict[key][step]
