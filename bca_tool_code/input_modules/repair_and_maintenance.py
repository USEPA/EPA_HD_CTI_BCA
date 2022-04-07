from bca_tool_code.input_modules.general_functions import read_input_file
from bca_tool_code.input_modules.deflators import Deflators


class RepairAndMaintenance:
    """

    The RepairAndMaintenance class reads the repair and maintenance input file and provides methods to query its contents.

    """

    _data = dict()

    @staticmethod
    def init_from_file(filepath, settings):

        RepairAndMaintenance._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = Deflators.convert_dollars_to_analysis_basis(settings, df, 'Value')

        RepairAndMaintenance._data = df.to_dict('index')

    @staticmethod
    def get_attribute_value(attribute_name):

        return RepairAndMaintenance._data[attribute_name]
