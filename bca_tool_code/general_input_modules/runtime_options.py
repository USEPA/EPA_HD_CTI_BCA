"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent options for what to include in the given run of the tool.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,user_entry,notes
        calculate_cap_costs,1,"1 for YES, 0 for NO"
        calculate_cap_pollution_effects,0,"1 for YES, 0 for NO"
        discount_values,1,"1 for YES, 0 for NO"
        calculate_deltas,1,"1 for YES, 0 for NO"

Data Column Name and Description
    :item:
        The name of the option; these should not be changed.

    :user_entry:
        A boolean indication (0 or 1) of what to include in the run.

    :Notes:
        User input area, if desired; ignored in-code.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class RuntimeOptions:
    """

    The RuntimeOptions class reads the runtime_options file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.runtime_options = list()
        self.calc_cap_costs = False
        self.calc_cap_pollution = False
        self.discount_values = False
        self.calc_deltas = False

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'notes' not in x, index_col=0)

        df = self.set_runtime_options(df)

        self._dict = df.to_dict('index')

        self.get_runtime_options()

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, attribute_name):
        """

        Parameters:
            attribute_name: str; the attribute for which the value is sought.

        Returns:
            The UserEntry value for the given attribute_name.

        """
        return self._dict[attribute_name]['user_entry']

    def set_runtime_options(self, df):

        self.runtime_options = [item for item in df.index.values]

        for setting in self.runtime_options:
            if pd.to_numeric(df.at[setting, 'user_entry']) == 1:
                df.at[setting, 'user_entry'] = True
            else:
                df.at[setting, 'user_entry'] = False

        return df

    def get_runtime_options(self):

        self.calc_cap_costs = self.get_attribute_value('calculate_cap_costs')
        self.calc_cap_pollution = self.get_attribute_value('calculate_cap_pollution_effects')
        self.discount_values = self.get_attribute_value('discount_values')
        self.calc_deltas = self.get_attribute_value('calculate_deltas')
