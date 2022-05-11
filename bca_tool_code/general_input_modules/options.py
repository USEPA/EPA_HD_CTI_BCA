from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Options:
    """

    The Options class reads the options file and provides methods to query contents.

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

    def get_option_name(self, alt):
        """

        Parameters:
            alt: int; the option_id for which the option_name is sought.

        Returns:
            A string associated with the given alt (i.e., option_id).

        """
        return self._dict[alt]['optionName']

    @staticmethod
    def create_option_id(action_id, no_action_id):
        """
        Create a new option_id.

        Parameters:
            action_id: int; the action scenario option_id.
            no_action_id: int; the no_action scenario option_id.

        Returns:
            An option_id number in the order of args.

        """
        return int(f'{action_id}{no_action_id}')

    def create_option_name(self, action_id, no_action_id):
        """
        Create a new option name.

        Parameters:
            action_id: int; the action scenario option_id.
            no_action_id: int; the no_action scenario option_id.

        Returns:
            An option_name based on the passed ids.

        """
        action_name = self.get_option_name(action_id)
        no_action_name = self.get_option_name(no_action_id)

        return f'{action_name}_minus_{no_action_name}'
