import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file
from bca_tool_code.input_modules.deflators import Deflators


class RegclassCosts:
    """

    The RegclassCosts class reads the regclass_costs input file and converts all dollar values to dollar_basis_analysis
    dollars.

    """

    _dict = dict()
    cost_steps = list()
    regclass_costs_in_analysis_dollars = pd.DataFrame()

    @staticmethod
    def init_from_file(filepath, general_inputs):

        RegclassCosts._dict.clear()
        RegclassCosts.cost_steps.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        RegclassCosts.cost_steps = [col for col in df.columns if '20' in col]

        df = Deflators.convert_dollars_to_analysis_basis(general_inputs, df, *RegclassCosts.cost_steps)

        RegclassCosts.regclass_costs_in_analysis_dollars = df.copy()

        df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'DollarBasis'], axis=0, as_index=False).sum()

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        RegclassCosts._dict = df.to_dict('index')

    @staticmethod
    def get_cost(key, cost_step):
        step = cost_step
        if type(step) is not str:
            step = f'{step}'
        return RegclassCosts._dict[key][step]
