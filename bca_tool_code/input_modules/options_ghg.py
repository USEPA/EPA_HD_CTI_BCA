import pandas as pd
import sys


class OptionsGHG:

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        OptionsGHG._data.clear()

        try:
            pd.read_csv(filepath)
            print(f'File {filepath}.......FOUND.')
            df = pd.read_csv(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

            OptionsGHG._data = df.to_dict('index')

        except FileNotFoundError:
            print(f'File {filepath}......NOT FOUND.')
            sys.exit()

    @staticmethod
    def get_option_name(alt):

        return OptionsGHG._data[alt]['OptionName']
