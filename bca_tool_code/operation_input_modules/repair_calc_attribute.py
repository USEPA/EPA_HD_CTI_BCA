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
            The repair calculation attribute (dollars_per_mile or dollars_per_hour).

        """
        return self._dict[sourcetype_id][self.attribute_name]
