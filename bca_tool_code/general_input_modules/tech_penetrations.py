import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class TechPenetrations:
    """

    The TechPenetrations class reads the tech penetrations file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.techpen_years = list()

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID']))
        df.set_index(key, inplace=True)

        self.techpen_years = [col for col in df.columns if '20' in col]

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, vehicle, option_id, modelyear_id):
        """

        Parameters:
            vehicle: tuple; (sourcetype_id, regclass_id, fueltype_id).\n
            option_id: int; the option_id.\n
            modelyear_id: int; the model year of vehicle.

        Returns:
            A single tech penetration value for the given vehicle in the given model year.

        """
        year = max([int(year) for year in self.techpen_years if int(year) <= modelyear_id])
        return self._dict[vehicle, option_id][str(year)]
