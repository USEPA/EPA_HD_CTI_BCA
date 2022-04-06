import pandas as pd
import sys


class RegclassLearningScalers:

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        RegclassLearningScalers._data.clear()

        try:
            pd.read_csv(filepath)
            print(f'File {filepath}.......FOUND.')
            df = pd.read_csv(filepath, usecols=lambda x: 'Notes' not in x)

            key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID']))

            df.set_index(key, inplace=True)

            RegclassLearningScalers._data = df.to_dict('index')

        except FileNotFoundError:
            print(f'File {filepath}......NOT FOUND.')
            sys.exit()

    @staticmethod
    def get_seedvolume_factor(engine, alt):

        seedvolume_factor = RegclassLearningScalers[engine, alt]['SeedVolumeFactor']

        return seedvolume_factor
