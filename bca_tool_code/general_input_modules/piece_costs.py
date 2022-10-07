"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the cost of the applicable piece of technology, indicated by the TechDescription, and the dollar
basis for the cost.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        optionID,regClassName,regClassID,FuelName,fuelTypeID,TechDescription,2027,2031,DollarBasis,Notes
        0,LHD,41,Diesel,2,CDA,0,0,,
        0,LHD,41,Diesel,2,ClosedCrankcase,0,0,,
        0,LHD,41,Diesel,2,EngineHardware,1065.75,0,2015,
        0,LHD,41,Diesel,2,EGR_CoolerBypass,0,0,,

Data Column Name and Description
    :optionID:
        The option or alternative number.

    :regClassName:
        The MOVES regulatory class name corresponding to the regClassID.

    :regClassID:
            The MOVES regClass ID, an integer.

    :FuelName:
        The MOVES fuel type name corresponding to the fuelTypeID.

    :fuelTypeID:
        The MOVES fuel type ID, an integer, where 1=Gasoline, 2=Diesel, etc.

    :TechDescription:
        A description or name of the technology.

    :2027:
        The cost associated with a new standard that begins in the indicated year (i.e., 2027, if applicable).

    :2031:
        The cost associated with a new standard that begins in the indicated year (i.e., 2031, if applicable).

    :DollarBasis:
        The dollar basis (dollars valued in what year) for the corresponding cost; costs are converted to analysis
        dollars in-code.

    :Notes:
        User input area, if desired; ignored in-code.

----

**CODE**

"""
import sys
import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class PieceCosts:
    """

    The PieceCosts class reads the appropriate piece cost input file and converts all dollar values to
    dollar_basis_analysis dollars and provides methods to query the data.

    """
    def __init__(self):
        self._dict = dict()
        self.standardyear_ids = list()
        self.piece_costs_in_analysis_dollars = pd.DataFrame()
        self.package_cost_by_step = dict()
        self.value_name = 'piece_cost'
        self.unit_id = None

    def init_from_file(self, filepath, unit_id, general_inputs, deflators):
        """

        Parameters:
            filepath: Path to the specified file.\n
            unit_id: str; 'engine_id' or 'vehicle_id'.\n
            general_inputs: object; the GeneralInputs class object.\n
            deflators: object; the Deflators class object.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, skiprows=1, usecols=lambda x: 'Notes' not in x)

        self.unit_id = unit_id
        if unit_id == 'engine_id':
            df.insert(0,
                      unit_id,
                      pd.Series(
                          zip(
                              df['regClassID'],
                              df['fuelTypeID']
                          )))
            id_vars = ['optionID', unit_id, 'regClassID', 'fuelTypeID', 'TechDescription', 'DollarBasis']
        elif unit_id == 'vehicle_id':
            df.insert(0,
                      unit_id,
                      pd.Series(
                          zip(
                              df['sourceTypeID'],
                              df['regClassID'],
                              df['fuelTypeID']
                          )))
            id_vars = ['optionID', unit_id, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'TechDescription', 'DollarBasis']
        else:
            print(f'\nImproper unit_id passed to {self}')
            sys.exit()

        df = pd.melt(df,
                     id_vars=id_vars,
                     value_vars=[col for col in df.columns if '20' in col],
                     var_name='standardyear_id',
                     value_name=self.value_name)

        df['standardyear_id'] = pd.to_numeric(df['standardyear_id'])
        self.standardyear_ids = df['standardyear_id'].unique()

        df = deflators.convert_dollars_to_analysis_basis(general_inputs, df, self.value_name)

        self.piece_costs_in_analysis_dollars = df.copy()

        df.drop(columns='DollarBasis', inplace=True)

        groupby_cols = id_vars[:-2]
        groupby_cols.append('standardyear_id')
        df = df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

        df.rename(columns={'piece_cost': 'pkg_cost'}, inplace=True)

        key = pd.Series(
            zip(
                df[unit_id],
                df['optionID'],
                df['standardyear_id']
            ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_start_year_cost(self, key, attribute_name):
        """

        Parameters:
            key: tuple; (unit_id, option_id, start_year) where unit_id is 'engine_id' or 'vehicle_id'.\n
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

        """
        key = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
        if self.unit_id == 'vehicle_id':
            key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
        if key in self.package_cost_by_step:
            for attribute_name, attribute_value in update_dict.items():
                self.package_cost_by_step[key][attribute_name] = attribute_value

        else:
            self.package_cost_by_step.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self.package_cost_by_step[key].update({attribute_name: attribute_value})

    def get_package_cost_by_standardyear_id(self, key, *attribute_names):
        """

        Parameters:
            key: tuple; (unit_id, option_id, year).\n
            attribute_names: list; the list of attribute names for which values are sought.

        Returns:
            A list of attribute values associated with attribute_names for the given key.

        """
        attribute_values = list()
        for attribute_name in attribute_names:
            attribute_values.append(self.package_cost_by_step[key][attribute_name])

        return attribute_values
