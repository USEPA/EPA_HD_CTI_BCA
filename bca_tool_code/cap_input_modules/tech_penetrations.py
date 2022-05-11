import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class CapTechPenetrations:
    """

    The GhgTechPenetrations class reads the tech penetrations file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.start_years = list()
        self.value_name = 'techpen'

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1)

        df = pd.melt(df,
                     id_vars=['optionID', 'regClassID', 'fuelTypeID'],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='start_year',
                     value_name=self.value_name)

        df['start_year'] = pd.to_numeric(df['start_year'])
        self.start_years = df['start_year'].unique()

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['start_year']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, vehicle):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.

        Returns:
            A single tech penetration value for the given vehicle.

        """
        engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
        year = min([int(year) for year in self.start_years if int(year) <= modelyear_id])

        return self._dict[engine_id, option_id, year][self.value_name]
