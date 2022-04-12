import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file


class InputFiles:

    _dict = dict()
    input_files_df = pd.DataFrame()
    input_files_pathlist = list()

    @staticmethod
    def init_from_file(filepath):

        InputFiles._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        InputFiles.input_files_df = df.copy()

        InputFiles._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.input_files_pathlist.append(filepath)

    @staticmethod
    def get_filename(file_id):

        return InputFiles._dict[file_id]['UserEntry.csv']
