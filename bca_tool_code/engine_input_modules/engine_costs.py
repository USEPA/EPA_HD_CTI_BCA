import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class EngineCosts:
    """

    The EngineCosts class reads the engine_costs input file and converts all dollar values to dollar_basis_analysis
    dollars and provides methods to query the data.

    """
    def __init__(self):
        self._dict = dict()
        self.start_years = list()
        self.piece_costs_in_analysis_dollars = pd.DataFrame()
        self.package_cost_by_step = dict()
        self.value_name = 'piece_cost'

    def init_from_file(self, filepath, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.\n
            general_inputs: object; the GeneralInputs class object.\n
            deflators: object; the Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        df = pd.melt(df,
                     id_vars=['optionID', 'regClassID', 'fuelTypeID', 'TechDescription', 'DollarBasis'],
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='start_year',
                     value_name=self.value_name)

        df['start_year'] = pd.to_numeric(df['start_year'])
        self.start_years = df['start_year'].unique()

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, self.value_name)

        self.piece_costs_in_analysis_dollars = df.copy()

        df.drop(columns='DollarBasis', inplace=True)
        df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'start_year'],
                        axis=0, as_index=False).sum()

        df.rename(columns={'piece_cost': 'pkg_cost'}, inplace=True)

        key = pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['start_year']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_start_year_cost(self, key, attribute_name):
        """

        Parameters:
            key: tuple; (engine_id, option_id, start_year).\n
            attribute_name: str; the attribute name associated with the needed cost (e.g., 'pkg_cost').

        Returns:
            The start_year package cost for the passed engine_id under the option_id option.

        """
        return self._dict[key][attribute_name]

    def update_package_cost_by_step(self, vehicle, update_dict):
        """

        Parameters:
            vehicle: object; a vehicle object of the Vehicles class.\n
            update_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        Note:
            The method updates an existing key having attribute_name with attribute_value.

        """
        key = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
        if key in self.package_cost_by_step:
            for attribute_name, attribute_value in update_dict.items():
                self.package_cost_by_step[key][attribute_name] = attribute_value

        else:
            self.package_cost_by_step.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self.package_cost_by_step[key].update({attribute_name: attribute_value})

    def get_package_cost_by_step(self, key, *attribute_names):
        """

        Parameters:
            key: tuple; (vehicle_id, option_id, model_year, age_id, discount_rate).\n
            attribute_names: list; the list of attribute names for which values are sought.

        Returns:
            A list of attribute values associated with attribute_names for the given key.

        """
        attribute_values = list()
        for attribute_name in attribute_names:
            attribute_values.append(self.package_cost_by_step[key][attribute_name])

        return attribute_values
