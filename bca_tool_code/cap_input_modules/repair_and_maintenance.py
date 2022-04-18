import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class RepairAndMaintenance:
    """

    The RepairAndMaintenance class reads the repair and maintenance input file and provides methods to query its contents.

    """

    _dict = dict()
    repair_and_maintenance_in_analysis_dollars = pd.DataFrame()

    @staticmethod
    def init_from_file(filepath, general_inputs, deflators):

        RepairAndMaintenance._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'Value')

        RepairAndMaintenance.repair_and_maintenance_in_analysis_dollars = df.copy()

        RepairAndMaintenance._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    @staticmethod
    def get_attribute_value(attribute_name):

        return RepairAndMaintenance._dict[attribute_name]['Value']
