import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class SourceTypeLearningScalers:
    """

    The SourceTypeLearningScalers class reads the sourcetype_learning_scalers input file and provides methods to query its
    contents.

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
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))

        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_seedvolume_factor(self, vehicle, alt):
        """

        Parameters:
            vehicle: tuple; (sourcetype_id, regclass_id, fueltype_id). \n
            alt: int; the option_id.

        Returns:
            The seed volume factor for the given vehicle and option_id.

        """
        return self._dict[vehicle, alt]['SeedVolumeFactor']
