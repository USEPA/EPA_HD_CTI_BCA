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
