"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the repair and maintenance cost per mile/hour values, their dollar basis and other metrics used to
estimate emission-related repair costs.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        Metric,Units,Value,DollarBasis,Notes
        repair_and_maintenance,dollars_per_mile,0.158,2017,
        repair_and_maintenance,dollars_per_hour,6.31,2017,
        typical_vmt_thru,age_id,6,,ageID=6 would include 7 years
        emission_repair_share,share_of_total_repair_and_maintenance,0.108,,

Data Column Name and Description
    :Metric:
        The name of the given attribute.

    :Units:
        The units of the given attribute value.

    :Value:
        The value of the given metric.

    :DollarBasis:
        The dollar basis (dollars valued in what year) for the corresponding cost; costs are converted to analysis
        dollars in-code.

----

**CODE**

"""
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class RepairAndMaintenance:
    """

    The RepairAndMaintenance class reads the repair and maintenance input file, converts monetized values to analysis dollars, and provides methods to query its contents.

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
            key: tuple of strings; e.g., ('repair_and_maintenance', 'dollars_per_mile').

        Returns:
            The value of the passed attribute.

        """
        return self._dict[key]['Value']
