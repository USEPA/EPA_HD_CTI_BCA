import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class WarrantyNewTechAdj:
    """

    The WarrantyNewTechAdj class reads the warranty_new_tech_adj_factor input file and provides methods to query its
    contents.

    """
    def __init__(self):
        self._dict = dict()
        self.start_years = list()
        self.value_name = 'factor'

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x)
        df.fillna(0, inplace=True)

        df = pd.melt(df,
                     id_vars=['optionID', 'regClassName', 'regClassID', 'fuelTypeID'],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='start_year',
                     value_name=self.value_name
                     )
        df['start_year'] = pd.to_numeric(df['start_year'])
        self.start_years = df['start_year'].unique()

        key = pd.Series(
            zip(
                zip(
                    df['regClassID'],
                    df['fuelTypeID']
                ),
                df['optionID'],
                df['start_year'],
            ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, vehicle):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.

        Returns:
            The adjustment factor to be applied to warranty costs when warranty provisions change.

        """
        engine_id, option_id, my_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
        if my_id == min(self.start_years):
            year = my_id
        else:
            year = max([int(year) for year in self.start_years if int(year) <= my_id])
        new_key = (engine_id, option_id, year)

        return self._dict[new_key][self.value_name]
