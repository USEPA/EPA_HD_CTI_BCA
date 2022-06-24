import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class WarrantyExtended:
    """

    The WarrantyExtendedShares class reads the appropriate extended_warranty_share input file  and provides methods to
    query the data.

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

        key = pd.Series(
            zip(
                df['regClassID'],
                df['fuelTypeID']
            )
        )
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_scaler(self, vehicle):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.

        Returns:
            The share with extended warranty for the passed engine_id under the option_id option and the scaler to apply
            to the base warranty cost.

        """
        engine_id = vehicle.engine_id
        key = engine_id
        base_miles = self._dict[key]['Base']
        extended_miles = self._dict[key]['Extended'] - base_miles
        share = self._dict[key]['Share']

        scaler = share * extended_miles / base_miles

        return scaler

    def get_required_miles_with_share(self, engine_id):
        """

        Parameters:
            engine_id: tuple; the engine_id (regclass_id, fueltype_id).

        Returns:
            The extended warranty miles multiplied by the share with extended warranty.

        """
        # engine_id, option_id = vehicle.engine_id, vehicle.option_id
        key = engine_id
        extended_miles = self._dict[key]['Extended']
        share = self._dict[key]['Share']

        return extended_miles, share


    def get_share(self, engine_id):
        """

        Parameters:
            engine_id: tuple; the engine_id (regclass_id, fueltype_id).

        Returns:
            The extended warranty miles multiplied by the share with extended warranty.

        """
        # engine_id, option_id = vehicle.engine_id, vehicle.option_id
        key = engine_id
        share = self._dict[key]['Share']

        return share
