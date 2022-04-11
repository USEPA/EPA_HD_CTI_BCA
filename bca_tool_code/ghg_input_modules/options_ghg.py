from bca_tool_code.general_input_modules.general_functions import read_input_file


class OptionsGHG:

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        OptionsGHG._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        OptionsGHG._dict = df.to_dict('index')

    @staticmethod
    def get_option_name(alt):

        return OptionsGHG._dict[alt]['OptionName']
