import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class RepairAndMaintenance:
    """

    The RepairAndMaintenance class reads the repair and maintenance input file, converts monetized values to analysis
     dollars, and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.repair_and_maintenance_in_analysis_dollars = pd.DataFrame()

    def init_from_file(self, filepath, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.
            general_inputs: The GeneralInputs class object.
            deflators: The Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x) #, index_col=0)

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'Value')

        self.repair_and_maintenance_in_analysis_dollars = df.copy()

        key = pd.Series(zip(
            df['Metric'],
            df['Units'],
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key):
        """

        Parameters:
            key: tuple of strings; e.g., ('max', 'dollars_per_mile').

        Returns:
            The value of the passed attribute.

        """
        return self._dict[key]['Value']
