from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles

# TODO make all classes like this to make things more pythonic
# class OptionsCAP:
#
#     def __init__(self):
#         self._dict = dict()
#
#     def init_from_file(self, filepath):
#
#         self._dict.clear()
#
#         df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)
#
#         self._dict = df.to_dict('index')
#
#         # update input_files_pathlist if this class is used
#         InputFiles.input_files_pathlist.append(filepath)
#
#     def get_option_name(self, alt):
#
#         return self._dict[alt]['OptionName']

class OptionsCAP:

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        OptionsCAP._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        OptionsCAP._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.input_files_pathlist.append(filepath)

    @staticmethod
    def get_option_name(alt):

        return OptionsCAP._dict[alt]['OptionName']
