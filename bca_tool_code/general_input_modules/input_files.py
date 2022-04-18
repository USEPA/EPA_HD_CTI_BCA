import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file


class InputFiles:

    input_files_df = pd.DataFrame()
    input_files_pathlist = list()

    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath):

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        self.input_files_df = df.copy()

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        self.input_files_pathlist.append(filepath)

    def get_filename(self, file_id):

        return self._dict[file_id]['UserEntry.csv']

    @staticmethod
    def update_pathlist(filepath):
        InputFiles.input_files_pathlist.append(filepath)
