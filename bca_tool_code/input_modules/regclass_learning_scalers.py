import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class RegclassLearningScalers:

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        RegclassLearningScalers._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID']))

        df.set_index(key, inplace=True)

        RegclassLearningScalers._dict = df.to_dict('index')

    @staticmethod
    def get_seedvolume_factor(engine, alt):

        return RegclassLearningScalers._dict[engine, alt]['SeedVolumeFactor']
