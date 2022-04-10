import pandas as pd
import sys


class OptionsGHG:

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        OptionsGHG._dict.clear()

        try:
            pd.read_csv(filepath)
            print(f'File {filepath}.......FOUND.')
            df = pd.read_csv(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

            OptionsGHG._dict = df.to_dict('index')

        except FileNotFoundError:
            print(f'File {filepath}......NOT FOUND.')
            sys.exit()

    @staticmethod
    def get_option_name(alt):

        return OptionsGHG._dict[alt]['OptionName']
