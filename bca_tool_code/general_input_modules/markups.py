import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Markups:
    """

    The Markups class reads the Markups input file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.contribution_factors = dict()
        self.markup_factor_names = list()

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['fuelTypeID'], df['optionID'], df['Markup_Factor']))
        df.set_index(key, inplace=True)

        self.markup_factor_names = [arg for arg in df['Markup_Factor'].unique()]

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: tuple; (fueltype_id, option_id, markup_factor), where markup_factor is, e.g., 'Warranty', RnD'.\n
            attribute_name: str; the attribute name for which a value is sought.

        Returns:
            A single value associated with the attribute name for the given key.

        """
        return self._dict[key][attribute_name]

    def get_attribute_values(self, key):
        """

        Parameters:
            key: tuple; (fueltype_id, option_id, markup_factor), where markup_factor is, e.g., 'Warranty', 'RnD'.

        Returns:
            A list of values for the given key.

        """
        values_list = list()
        for attribute_name in ['Value', 'Scaler', 'Scaled_by', 'NumberOfYears']:
            values_list.append(self.get_attribute_value(key, attribute_name))

        return values_list

    def update_contribution_factors(self, vehicle, update_dict):
        """

        Parameters:
            vehicle: object; a vehicle object of the Vehicles class.\n
            update_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        """
        key = vehicle.vehicle_id, vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
        if key in self.contribution_factors:
            for attribute_name, attribute_value in update_dict.items():
                self.contribution_factors[key][attribute_name] = attribute_value

        else:
            self.contribution_factors.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self.contribution_factors[key].update({attribute_name: attribute_value})

    def revise_warranty_contribution(self, settings, vehicle):
        """

        This method revises warranty costs where insufficient years of data exist to get a full accounting (i.e., if
        estimated warranty age is 5 years, then a 2045 vehicle has insufficient data to fully account for warranty costs
        since warranty costs are calculated on cost/year basis. This method is used only when warrnaty cost method is
        set to cost_per_year.

        Parameters:
            vehicle: object; a vehicle object of the Vehicles class.\n

        Returns:
            Revised warranty contributions based on prior model year values.

        """
        identifier = 'Warranty'
        estimated_ages_dict_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, identifier

        estimated_age = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        if vehicle.modelyear_id + estimated_age > settings.cap_vehicle.year_id_max:
            modelyear_id = settings.cap_vehicle.year_id_max - estimated_age
            key = vehicle.vehicle_id, vehicle.engine_id, vehicle.option_id, modelyear_id
            warranty_cost = self.contribution_factors[key]['WarrantyCost_PerVeh']
            update_dict = {'WarrantyCost_PerVeh': warranty_cost}
            self.update_contribution_factors(vehicle, update_dict)
