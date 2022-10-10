import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Vehicle:
    """

    Define vehicle attribute names for sourceTypeID, regClassID, fuelTypeID.

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
        self.vmt_per_veh = 0
        self.odometer = 0
        self.vpop = 0
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
            options: object; an instance of the Options class.\n
            adjustments: object; an instance of the MovesAdjustments class (if applicable).

        Returns:
            Reads file at filepath; creates a dictionary and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath)

        df = self.rename_attributes(df)

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

        Returns:
            Updates the attributes_to_adjust object list.

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

        df_return.insert(len(df_return.columns), 'vmt_per_veh', df_return['vmt'] / df_return['vpop'])
        odometer = self.calc_odometer(df_return)

        df_return.insert(len(df_return.columns), 'odometer', odometer)

        Vehicle.vehicle_df = df_return.copy()

    @staticmethod
    def calc_odometer(df):
        """

        Parameters:
            df: DataFrame; vehicle level data containing vmt_per_veh information.

        Returns:
            A pandas Series of odometer data (cumulative vmt_per_vehicle).

        """
        temp = df.groupby(by=[
            'sourcetype_id',
            'regclass_id',
            'fueltype_id',
            'option_id',
            'modelyear_id',
        ]).cumsum(axis=0)

        odometer = temp['vmt_per_veh']

        return odometer

    @staticmethod
    def rename_attributes(df):

        rename_dict = {'sourceTypeID': 'sourcetype_id',
                       'regClassID': 'regclass_id',
                       'fuelTypeID': 'fueltype_id',
                       'yearID': 'year_id',
                       'Alternative': 'option_id',
                       'modelYearID': 'modelyear_id',
                       'VPOP': 'vpop',
                       'VMT': 'vmt',
                       'Gallons': 'gallons',
                       'Energy_KJ': 'energy_kilojoules',
                       'THC_UStons': 'thc_ustons',
                       'CO_UStons': 'co_ustons',
                       'NOx_UStons': 'nox_ustons',
                       'CO2_UStons': 'co2_ustons',
                       'CH4_UStons': 'ch4_ustons',
                       'N2O_UStons': 'n2o_ustons',
                       'SO2_UStons': 'so2_ustons',
                       'VOC_UStons': 'voc_ustons',
                       'PM25_exhaust_UStons': 'pm25_exhaust_ustons',
                       'PM25_brakewear_UStons': 'pm25_brakewear_ustons',
                       'PM25_tirewear_UStons': 'pm25_tirewear_ustons',
                       }
        for key in rename_dict:
            df.rename(columns={key: rename_dict[key]}, inplace=True)

        return df