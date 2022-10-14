"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the repair and maintenance cost attribute (i.e., cost per mile/hour) to use in estimating
emission-related repair costs.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        sourceTypeID,attribute
        31,dollars_per_mile
        32,dollars_per_mile
        41,dollars_per_hour
        42,dollars_per_hour
        43,dollars_per_hour
        51,dollars_per_hour
        52,dollars_per_hour
        53,dollars_per_mile
        54,dollars_per_mile
        61,dollars_per_mile
        62,dollars_per_mile

Data Column Name and Description
    :sourceTypeID:
        The MOVES sourcetype ID, an integer.

    :attribute:
        The attribute to use for the given sourcetype ID.

----

**CODE**

"""
from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class RepairCalcAttribute:
    """

    The RepairCalcAttribute class reads the repair calculation attribute input file, and provides methods to query its
    contents.

    """
    def __init__(self):
        self._dict = dict()
        self.attribute_name = 'attribute'

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x, index_col=0)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, sourcetype_id):
        """

        Parameters:
            sourcetype_id: int; the vehicle sourcetype_id.

        Returns:
            The repair calculation attribute (dollars_per_mile or dollars_per_hour) to use when calculating emission-related repair costs.

        """
        return self._dict[sourcetype_id][self.attribute_name]
