import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class OrvrFuelChangesCAP:
    """

    The OrvrFuelChangesCAP class reads the DEF dose rates file and provides methods to query its contents.

    """

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        OrvrFuelChangesCAP._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        OrvrFuelChangesCAP._dict = df.to_dict('index')

    @staticmethod
    def get_ml_per_gram(engine, alt):

        return OrvrFuelChangesCAP._dict[engine, alt]['ml/g']
