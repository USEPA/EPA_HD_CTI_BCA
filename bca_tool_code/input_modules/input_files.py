from bca_tool_code.input_modules.general_functions import read_input_file


class InputFiles:

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        InputFiles._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        InputFiles._data = df.to_dict('index')

    @staticmethod
    def get_filename(file_id):

        return InputFiles._data[file_id]['UserEntry.csv']
