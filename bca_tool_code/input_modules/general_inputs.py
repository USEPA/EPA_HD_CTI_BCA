from bca_tool_code.input_modules.general_functions import read_input_file


class GeneralInputs:
    """

    The GeneralInputs class reads the BCA_General_Inputs file and provides methods to query its contents.

    """

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        GeneralInputs._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        GeneralInputs._data = df.to_dict('index')

    @staticmethod
    def get_attribute_value(attribute_name):

        return GeneralInputs._data[attribute_name]['UserEntry']
