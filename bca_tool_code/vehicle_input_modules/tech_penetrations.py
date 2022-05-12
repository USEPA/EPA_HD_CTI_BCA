import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class GhgTechPenetrations:
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
                     id_vars=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'standardyear_id'],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='modelyear_id',
                     value_name=self.value_name)

        df['modelyear_id'] = pd.to_numeric(df['modelyear_id'])
        self.start_years = df['modelyear_id'].unique()

        key = pd.Series(zip(
            zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']),
            df['optionID'], df['modelyear_id'], df['standardyear_id']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, vehicle, standardyear_id):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.
            standardyear_id: int; the year in which a new standard starts.

        Returns:
            A single tech penetration value for the given vehicle.

        """
        vehicle_id, option_id, modelyear_id = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
        year = max([int(year) for year in self.start_years if int(year) <= modelyear_id])

        return self._dict[vehicle_id, option_id, year, standardyear_id][self.value_name]
