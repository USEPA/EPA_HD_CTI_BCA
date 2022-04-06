from bca_tool_code.general_functions import read_input_file


class InputData:

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        InputData._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        InputData._data = df.to_dict('index')

    @staticmethod
    def get_filename(file_id):

        return InputData._data[file_id]['UserEntry.csv']
