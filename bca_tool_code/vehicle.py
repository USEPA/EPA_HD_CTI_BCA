import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Vehicle:
    """

    Define vehicle attribute names for sourceTypeID, regClassID, fuelTypeID.

    Parameters::
        id: The associated ID from the MOVES input file.

    Returns:
        Source type name, Regclass name, Fuel type name.

    """
    vehicle_df = pd.DataFrame()
    attributes_to_adjust = list()  # these are MOVES attributes that need adjustment
    year_id_min = 0
    year_id_max = 0
    year_ids = 0

    def __init__(self):
        self.year_id = 0
        self.sourcetype_id = 0
        self.sourcetype_name = None
        self.regclass_id = 0
        self.regclass_name = None
        self.fueltype_id = 0
        self.fueltype_name = None
        self.modelyear_id = 0
        self.age_id = None
        self.option_id = None
        self.vehicle_id = None
        self.engine_id = None
        self.option_name = None
        self.thc_ustons = 0
        self.co_ustons = 0
        self.nox_ustons = 0
        self.pm25_exhaust_ustons = 0
        self.pm25_brakewear_ustons = 0
        self.pm25_tirewear_ustons = 0
        self.pm25_ustons = 0
        self.so2_ustons = 0
        self.voc_ustons = 0
        self.co2_ustons = 0
        self.ch4_ustons = 0
        self.n2o_ustons = 0
        self.energy_kj = 0
        self.vmt = 0
        self.cumulative_vmt = 0
        self.vpop = 0
        self.vpop_with_tech = 0
        self.gallons = 0

    def set_vehicle_id(self):
        return (self.sourcetype_id, self.regclass_id, self.fueltype_id)

    def set_engine_id(self):
        return (self.regclass_id, self.fueltype_id)

    def set_age_id(self):
        return self.year_id - self.modelyear_id

    def get_fueltype_name(self):
        """

        Returns:
            The fuel type name for the passed ID.

        """
        fueltype_dict = {1: 'Gasoline',
                         2: 'Diesel',
                         3: 'CNG',
                         5: 'E85-Capable',
                         9: 'Electric',
                         }
        return fueltype_dict[self.fueltype_id]

    def get_regclass_name(self):
        """

        Returns:
            The regclass name for the passed ID.

        """
        regclass_dict = {10: 'MC',
                         20: 'LDV',
                         30: 'LDT',
                         41: 'LHD',
                         42: 'LHD45',
                         46: 'MHD67',
                         47: 'HHD8',
                         48: 'Urban Bus',
                         49: 'Gliders',
                         }
        return regclass_dict[self.regclass_id]

    def get_sourcetype_name(self):
        """

        Returns:
            The source type name for the passed ID.

        """
        sourcetype_dict = {0: 'NotApplicable',
                           11: 'Motorcycles',
                           21: 'Passenger Cars',
                           31: 'Passenger Trucks',
                           32: 'Light Commercial Trucks',
                           41: 'Other Buses',
                           42: 'Transit Buses',
                           43: 'School Buses',
                           51: 'Refuse Trucks',
                           52: 'Short-Haul Single Unit Trucks',
                           53: 'Long-Haul Single Unit Trucks',
                           54: 'Motor Homes',
                           61: 'Short-Haul Combination Trucks',
                           62: 'Long-Haul Combination Trucks',
                           }
        return sourcetype_dict[self.sourcetype_id]

    def init_from_file(self, filepath, options, adjustments=None):
        """

        Parameters:
            filepath: Path to the specified file.\n
            general_inputs: object; the GeneralInputs class object.\n
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n
            adjustments: object; the MovesAdjustments class object.

        Returns:
            Reads file at filepath; creates a dictionary and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath)

        # df.insert(0, 'discount_rate', 0)
        df.insert(df.columns.get_loc('modelyear_id') + 1, 'age_id', df['year_id'] - df['modelyear_id'])

        year_min = self.get_age0_min_year(df, 'year_id')
        Vehicle.year_id_min = year_min

        year_max = df['year_id'].max()
        Vehicle.year_id_max = year_max

        years = range(year_min, year_max + 1)
        Vehicle.year_ids = years

        if adjustments:
            self.define_attributes_to_adjust()

        self.create_vehicle_df(df, year_min, options, adjustments)

        InputFiles().input_files_pathlist.append(filepath)

    def get_age0_min_year(self, df, attribute):
        """

        Parameters:
            df: DataFrame; the input data (i.e., the MOVES data).\n
            attribute: str; the attribute for which the age=0 minimum is sought (e.g., calendar year).

        Returns:
            A single value representing the minimum value of attribute for which age=0.

        """
        return df.loc[df['age_id'] == 0, attribute].min()

    def define_attributes_to_adjust(self):
        """

        Parameters:
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n

        Returns:
            Updates the attributes_with_tech object dictionary.

        """
        self.attributes_to_adjust = ['vpop', 'vmt', 'gallons']

    def create_vehicle_df(self, df, year_min, options, adjustments=None):
        """

        Parameters:
            df: DataFrame; the raw fleet input data (e.g., from MOVES). \n
            year_min: int; the first model year to include in the returned DataFrame.\n
            # program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n
            options: object; the options class object.\n
            adjustments: object; the MovesAdjustments class object.

        Returns:
            A DataFrame of the MOVES inputs with necessary MOVES adjustments made according to the MOVES adjustments
            input file.

        """
        _df = df.copy()
        if 'Alternative' in _df.columns.tolist():
            _df.rename(columns={'Alternative': 'option_id'}, inplace=True)

        # remove data we don't need for the project
        _df = _df.loc[(_df['regclass_id'] != 41) | (_df['fueltype_id'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
        _df = _df.loc[_df['regclass_id'] != 49, :]  # eliminate Gliders
        _df = _df.loc[_df['fueltype_id'] != 5, :]  # eliminate E85
        _df = _df.loc[_df['regclass_id'] >= 41, :]  # eliminate non-project regclasses

        _df = pd.DataFrame(_df.loc[_df['modelyear_id'] >= year_min, :]).reset_index(drop=True)

        # select only the options included in the options.csv input file
        option_id_list = [key for key in options._dict.keys()]
        df_alts = dict()
        df_return = pd.DataFrame()
        for alt in option_id_list:
            df_alts[alt] = _df.loc[_df['option_id'] == alt, :]
            df_return = pd.concat([df_return, df_alts[alt]], axis=0, ignore_index=True)

        df_return.reset_index(drop=True, inplace=True)

        # sum the PM constituents into a single constituent
        cols = [col for col in df_return.columns if 'pm25' in col]
        df_return.insert(len(df_return.columns), 'pm25_ustons', df_return[cols].sum(axis=1))  # sum PM25 metrics

        # make adjustments to MOVES values as needed for analysis
        if adjustments:
            vehicles = pd.Series(
                zip(
                    zip(df_return['sourcetype_id'], df_return['regclass_id'], df_return['fueltype_id']),
                    df_return['option_id'])
            ).unique()

            for (vehicle, alt) in vehicles:
                st, rc, ft = vehicle
                adjustment = adjustments.get_attribute_value(vehicle, alt, 'percent')
                growth = adjustments.get_attribute_value(vehicle, alt, 'growth') # remove this from here and input file?

                for arg in self.attributes_to_adjust:
                    arg_with_tech = df_return.loc[(df_return['option_id'] == alt)
                                                  & (df_return['sourcetype_id'] == st)
                                                  & (df_return['regclass_id'] == rc)
                                                  & (df_return['fueltype_id'] == ft), arg] * adjustment * (1 + growth)
                    df_return.loc[(df_return['option_id'] == alt)
                                  & (df_return['sourcetype_id'] == st)
                                  & (df_return['regclass_id'] == rc)
                                  & (df_return['fueltype_id'] == ft), f'{arg}'] = arg_with_tech

        # if techpens:
        #     vehicles = pd.Series(
        #         zip(
        #             zip(df_return['sourcetype_id'], df_return['regclass_id'], df_return['fueltype_id']),
        #             df_return['option_id'])
        #     ).unique()
        #
        #     # df_return_years = df_return['modelyear_id'].unique()
        #     # start_years = techpens.get_techpen_years
        #     for (vehicle, alt) in vehicles:
        #         for modelyear_id in Vehicle.year_ids:
        #             st, rc, ft = vehicle
        #             techpen = techpens.get_attribute_value(vehicle, alt, modelyear_id)
        #
        #             for arg in self.attributes_for_techpens:
        #                 arg_with_tech = df_return.loc[(df_return['option_id'] == alt)
        #                                               & (df_return['sourcetype_id'] == st)
        #                                               & (df_return['regclass_id'] == rc)
        #                                               & (df_return['fueltype_id'] == ft)
        #                                               & (df_return['modelyear_id'] == modelyear_id), arg] * techpen
        #                 df_return.loc[(df_return['option_id'] == alt)
        #                                & (df_return['sourcetype_id'] == st)
        #                                & (df_return['regclass_id'] == rc)
        #                                & (df_return['fueltype_id'] == ft)
        #                                & (df_return['modelyear_id'] == modelyear_id), f'{arg}_with_tech'] = arg_with_tech

                # if program == 'CAP':
                #     df_return.loc[(df_return['option_id'] == alt)
                #                   & (df_return['sourcetype_id'] == st)
                #                   & (df_return['regclass_id'] == rc)
                #                   & (df_return['fueltype_id'] == ft), f'{arg}'] = arg_with_tech
                # else:
                #     df_return.loc[(df_return['option_id'] == alt)
                #                   & (df_return['sourcetype_id'] == st)
                #                   & (df_return['regclass_id'] == rc)
                #                   & (df_return['fueltype_id'] == ft), f'{arg}_withTech'] = arg_with_tech

        Vehicle.vehicle_df = df_return.copy()

    
# class Vehicles(Vehicle):
#
#
#     def __init__(self):
#         super().__init__()
#
#     @staticmethod
#     def create_cap_vehicles():
#         vehicles = list()
#         for index, row in Vehicle._vehicle_df.iterrows():
#             vehicle = Vehicle()
#             vehicle.year_id = int(row['year_id'])
#             vehicle.sourcetype_id = int(row['sourcetype_id'])
#             vehicle.sourcetype_name = vehicle.get_sourcetype_name()
#             vehicle.regclass_id = int(row['regclass_id'])
#             vehicle.regclass_name = vehicle.get_regclass_name()
#             vehicle.fueltype_id = int(row['fueltype_id'])
#             vehicle.fueltype_name = vehicle.get_fueltype_name()
#             vehicle.modelyear_id = int(row['modelyear_id'])
#             vehicle.age_id = int(row['age_id'])
#             vehicle.option_id = int(row['option_id'])
#             vehicle.engine_id = vehicle.set_engine_id()
#             vehicle.vehicle_id = vehicle.set_vehicle_id()
#             vehicle.thc_ustons = row['thc_ustons']
#             vehicle.nox_ustons = row['nox_ustons']
#             vehicle.pm25_exhaust_ustons = row['pm25_exhaust_ustons']
#             vehicle.pm25_brakewear_ustons = row['pm25_brakewear_ustons']
#             vehicle.pm25_tirewear_ustons = row['pm25_tirewear_ustons']
#             vehicle.pm25_ustons = row['pm25_ustons']
#             vehicle.voc_ustons = row['voc_ustons']
#             vehicle.vmt = row['vmt']
#             vehicle.vpop = row['vpop']
#             vehicle.gallons = row['gallons']
#             try:
#                 vehicle.vmt_with_tech = row['vmt_with_tech']
#             except NotImplemented:
#                 pass
#             try:
#                 vehicle.vpop_with_tech = row['vpop_with_tech']
#             except NotImplemented:
#                 pass
#             try:
#                 vehicle.gallons_with_tech = row['gallons_with_tech']
#             except NotImplemented:
#                 pass
#             vehicles.append(vehicle)
#         return vehicles
#
#     @staticmethod
#     def create_ghg_vehicles():
#         vehicles = list()
#         for index, row in Vehicle._vehicle_df.iterrows():
#             vehicle = Vehicle()
#             vehicle.year_id = int(row['year_id'])
#             vehicle.sourcetype_id = int(row['sourcetype_id'])
#             vehicle.sourcetype_name = vehicle.get_sourcetype_name()
#             vehicle.regclass_id = int(row['regclass_id'])
#             vehicle.regclass_name = vehicle.get_regclass_name()
#             vehicle.fueltype_id = int(row['fueltype_id'])
#             vehicle.fueltype_name = vehicle.get_fueltype_name()
#             vehicle.modelyear_id = int(row['modelyear_id'])
#             vehicle.age_id = int(row['age_id'])
#             vehicle.option_id = int(row['option_id'])
#             vehicle.engine_id = vehicle.set_engine_id()
#             vehicle.vehicle_id = vehicle.set_vehicle_id()
#             vehicle.thc_ustons = row['thc_ustons']
#             vehicle_co2_ustons = row['co2_ustons']
#             vehicle.ch4_ustons = row['ch4_ustons']
#             vehicle.n2o_ustons = row['n2o_ustons']
#             vehicle.so2_ustons = row['so2_ustons']
#             vehicle_energy_kj = row['energy_kj']
#             vehicle.vmt = row['vmt']
#             vehicle.vpop = row['vpop']
#             vehicle.gallons = row['gallons']
#             try:
#                 vehicle.vmt_with_tech = row['vmt_with_tech']
#             except NotImplemented:
#                 pass
#             try:
#                 vehicle.vpop_with_tech = row['vpop_with_tech']
#             except NotImplemented:
#                 pass
#             try:
#                 vehicle.gallons_with_tech = row['gallons_with_tech']
#             except NotImplemented:
#                 pass
#             vehicles.append(vehicle)
#         return vehicles
#
#     # @staticmethod
#     def engine_sales(self, regclass_id, fueltype_id, option_id, *modelyear_ids):
#         _dict = dict()
#         for modelyear_id in modelyear_ids:
#             _dict[modelyear_id] = sum([vehicle.vpop for vehicle in self.vehicles
#                                        if vehicle.regclass_id == regclass_id
#                                        and vehicle.fueltype_id == fueltype_id
#                                        and vehicle.option_id == option_id
#                                        and vehicle.age_id == 0
#                                        and vehicle.modelyear_id == modelyear_id])
#         return _dict
