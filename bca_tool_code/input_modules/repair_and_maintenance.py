import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file
from bca_tool_code.input_modules.deflators import Deflators


class RepairAndMaintenance:
    """

    The RepairAndMaintenance class reads the repair and maintenance input file and provides methods to query its contents.

    """

    _data = dict()
    repair_and_maintenance_in_analysis_dollars = pd.DataFrame()

    @staticmethod
    def init_from_file(filepath, general_inputs):

        RepairAndMaintenance._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = Deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'Value')

        RepairAndMaintenance.repair_and_maintenance_in_analysis_dollars = df.copy()

        RepairAndMaintenance._data = df.to_dict('index')

    @staticmethod
    def get_attribute_value(attribute_name):

        return RepairAndMaintenance._data[attribute_name]['Value']
