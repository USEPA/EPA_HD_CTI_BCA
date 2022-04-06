import pandas as pd

from bca_tool_code.deflators import Deflators


class RegclassCosts:
    """

    The RegclassCosts class reads the regclass_costs input file and converts all dollar values to dollar_basis_analysis
    dollars.

    """

    _data = dict()
    cost_steps = list()

    @staticmethod
    def init_from_file(filepath, settings):

        RegclassCosts._data.clear()
        RegclassCosts.cost_steps.clear()

        df = pd.read_csv(filepath, usecols=lambda x: 'Notes' not in x)

        RegclassCosts.cost_steps = [col for col in df.columns if '20' in col]

        df = Deflators.convert_dollars_to_analysis_basis(settings, df, *RegclassCosts.cost_steps)

        df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'DollarBasis'], axis=0, as_index=False).sum()

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        RegclassCosts._data = df.to_dict('index')

    @staticmethod
    def get_cost(engine, alt, cost_step):

        return RegclassCosts._data[engine, alt][cost_step]
