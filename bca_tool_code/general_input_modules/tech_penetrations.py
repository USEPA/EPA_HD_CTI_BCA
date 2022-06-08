import sys
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class TechPenetrations:
    """

    The GhgTechPenetrations class reads the tech penetrations file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.start_years = list()
        self.value_name = 'techpen'
        self.unit_id = None

    def init_from_file(self, filepath, unit_id):
        """

        Parameters:
            filepath: Path to the specified file.\n
            unit_id: str; 'engine_id' or 'vehicle_id'.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1)

        self.unit_id = unit_id
        if unit_id == 'engine_id':
            df.insert(0,
                      unit_id,
                      pd.Series(zip(df['regClassID'], df['fuelTypeID'])))
            id_vars = ['optionID', unit_id, 'regClassID', 'fuelTypeID', 'standardyear_id']
        elif unit_id == 'vehicle_id':
            df.insert(0,
                      unit_id,
                      pd.Series(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID'])))
            id_vars = ['optionID', unit_id, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'standardyear_id']
        else:
            print(f'\nImproper unit_id passed to {self}')
            sys.exit()

        df = pd.melt(df,
                     id_vars=id_vars,
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='modelyear_id',
                     value_name=self.value_name)

        df['modelyear_id'] = pd.to_numeric(df['modelyear_id'])
        self.start_years = df['modelyear_id'].unique()

        key = pd.Series(zip(
            df[unit_id],
            df['optionID'],
            df['modelyear_id'],
            df['standardyear_id'],
        ))
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
        unit_id = vehicle.engine_id
        if self.unit_id == 'vehicle_id':
            unit_id = vehicle.vehicle_id
        option_id, modelyear_id = vehicle.option_id, vehicle.modelyear_id
        year = max([int(year) for year in self.start_years if int(year) <= modelyear_id])

        return self._dict[unit_id, option_id, year, standardyear_id][self.value_name]
