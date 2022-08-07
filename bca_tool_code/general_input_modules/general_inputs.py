"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the general input settings for the given run.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        Metric,UserEntry,Notes
        dollar_basis_analysis,2017,enter the dollar basis for the analysis (all monetized inputs will be converted to this basis provided the deflators input file contains necessary years)
        no_action_alt,0,The optionID of the 'no action' option
        aeo_fuel_price_case,Reference case,"enter one of: ""Reference case""; ""High oil price""; ""Low oil price"" (exactly as shown)"
        social_discount_rate_1,0.03,
        social_discount_rate_2,0.07,

Data Column Name and Description
    :Metric:
        The input setting name.

    :UserEntry:
        The user provided value for the associated Metric.

    :Notes:
        Optional notes provided by the user; notes are ignored in-code.

----

**CODE**

"""
from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class GeneralInputs:
    """

    The GeneralInputs class reads the BCA_General_Inputs file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, attribute_name):
        """

        Parameters:
            attribute_name: str; the attribute for which the value is sought.

        Returns:
            The UserEntry value for the given attribute_name.

        """
        return self._dict[attribute_name]['UserEntry']
