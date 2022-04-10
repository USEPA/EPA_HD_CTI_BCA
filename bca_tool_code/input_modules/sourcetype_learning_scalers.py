import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class SourceTypeLearningScalers:

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        SourceTypeLearningScalers._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))

        df.set_index(key, inplace=True)

        SourceTypeLearningScalers._dict = df.to_dict('index')

    @staticmethod
    def get_seedvolume_factor(vehicle, alt):

        return SourceTypeLearningScalers._dict[vehicle, alt]['SeedVolumeFactor']
