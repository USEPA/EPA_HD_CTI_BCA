import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class Fleet:
    """

    The Fleet class reads the MOVES input data file, adjusts data as specified in moves_adjustments file and provides
    methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.attributes_with_tech = None  # these are MOVES attributes that need adjustment
        self.year_min = 0
        self.year_max = 0
        self.years = 0
        self.fleet_df = pd.DataFrame()  # used in RegClassSales or SourceTypeSales
        self.keys = None
        self.age0_keys = None
        self.ft2_keys = None
        self.non0_dr_keys = None
        self.attributes_to_sum = None

    def init_from_file(self, filepath, general_inputs, program, options, adjustments):
        """

        Parameters:
            filepath: Path to the specified file.\n
            general_inputs: object; the GeneralInputs class object.\n
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n
            adjustments: object; the MovesAdj class object.

        Returns:
            Reads file at filepath; creates a dictionary and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath)

        df.insert(0, 'DiscountRate', 0)
        df.insert(df.columns.get_loc('modelYearID') + 1, 'ageID', df['yearID'] - df['modelYearID'])

        year_min = self.get_age0_min_year(df, 'yearID')
        self.year_min = year_min

        year_max = df['yearID'].max()
        self.year_max = year_max

        years = range(year_min, year_max + 1)
        self.years = years

        self.define_attributes_with_tech(program)

        df = self.create_fleet_df(df, year_min, program, options, adjustments)
        self.fleet_df = df.copy()

        new_attributes = create_new_attributes(general_inputs, program)

        df['VMT_PerVeh'] = df['VMT'] / df['VPOP']

        for new_attribute in new_attributes:
            df.insert(len(df.columns), f'{new_attribute}', 0)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']),
                            df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        self.calc_per_veh_cumulative_vmt()

        add_keys_for_discounting(general_inputs, self._dict)

        # set keys
        self.keys = tuple([k for k in self._dict.keys()])
        self.age0_keys = tuple([k for k, v in self._dict.items() if v['ageID'] == 0])
        self.ft2_keys = tuple([k for k, v in self._dict.items() if v['fuelTypeID'] == 2])
        self.non0_dr_keys = tuple([k for k, v in self._dict.items() if v['DiscountRate'] != 0])

        # define attributes to sum
        self.define_attributes_to_sum(program)

        InputFiles().input_files_pathlist.append(filepath)

    def get_attribute_values(self, key, *attribute_names):
        """

        Parameters:
            key: tuple; ((sourcetype_id, regclass_id, fueltype_id), option_id, model_year, age_id, discount_rate).\n
            *attribute_names: str(s); the attribute names for which values are sought.

        Returns:
            A list of attribute values associated with attribute_names for the given key.

        """
        attribute_values = list()
        for attribute_name in attribute_names:
            attribute_values.append(self._dict[key][attribute_name])

        return attribute_values

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: ((sourcetype_id, regclass_id, fueltype_id), option_id, model_year, age_id, discount_rate).\n
            attribute_name: str; the attribute name for which the value is sought.

        Returns:
            The attribute value associated with the attribute_name for the given key.

        """
        return self._dict[key][attribute_name]

    def create_fleet_df(self, df, year_min, program, options, adjustments):
        """

        Parameters:
            df: DataFrame; the raw fleet input data (e.g., from MOVES). \n
            year_min: int; the first model year to include in the returned DataFrame.\n
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n
            options: object; the options class object.\n
            adjustments: object; the MovesAdj class object.

        Returns:
            A DataFrame of the MOVES inputs with necessary MOVES adjustments made according to the MOVES adjustments
            input file.

        """
        _df = df.copy()
        if 'Alternative' in _df.columns.tolist():
            _df.rename(columns={'Alternative': 'optionID'}, inplace=True)

        # remove data we don't need for the project
        _df = _df.loc[(_df['regClassID'] != 41) | (_df['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
        _df = _df.loc[_df['regClassID'] != 49, :]  # eliminate Gliders
        _df = _df.loc[_df['fuelTypeID'] != 5, :]  # eliminate E85
        _df = _df.loc[_df['regClassID'] >= 41, :]  # eliminate non-project regclasses

        _df = pd.DataFrame(_df.loc[_df['modelYearID'] >= year_min, :]).reset_index(drop=True)

        # select only the options included in the options.csv input file
        option_id_list = [key for key in options._dict.keys()]
        df_alts = dict()
        df_return = pd.DataFrame()
        for alt in option_id_list:
            df_alts[alt] = _df.loc[_df['optionID'] == alt, :]
            df_return = pd.concat([df_return, df_alts[alt]], axis=0, ignore_index=True)

        df_return.reset_index(drop=True, inplace=True)

        # sum the PM constituents into a single constituent
        cols = [col for col in df_return.columns if 'PM25' in col]
        df_return.insert(len(df_return.columns), 'PM25_UStons', df_return[cols].sum(axis=1))  # sum PM25 metrics

        # make adjustments to MOVES values as needed for analysis
        st_vehicles = pd.Series(
            zip(zip(df_return['sourceTypeID'], df_return['regClassID'], df_return['fuelTypeID']),
                df_return['optionID'])).unique()

        for (vehicle, alt) in st_vehicles:
            st, rc, ft = vehicle
            adjustment = adjustments.get_attribute_value(vehicle, alt, 'percent')
            growth = adjustments.get_attribute_value(vehicle, alt, 'growth')

            for arg in self.attributes_with_tech:
                arg_with_tech = df_return.loc[(df_return['optionID'] == alt)
                                              & (df_return['sourceTypeID'] == st)
                                              & (df_return['regClassID'] == rc)
                                              & (df_return['fuelTypeID'] == ft), arg] * adjustment * (1 + growth)
                if program == 'CAP':
                    df_return.loc[(df_return['optionID'] == alt)
                                  & (df_return['sourceTypeID'] == st)
                                  & (df_return['regClassID'] == rc)
                                  & (df_return['fuelTypeID'] == ft), f'{arg}'] = arg_with_tech
                else:
                    df_return.loc[(df_return['optionID'] == alt)
                                  & (df_return['sourceTypeID'] == st)
                                  & (df_return['regClassID'] == rc)
                                  & (df_return['fuelTypeID'] == ft), f'{arg}_withTech'] = arg_with_tech

        return df_return

    def get_age0_min_year(self, df, attribute):
        """

        Parameters:
            df: DataFrame; the input data (i.e., the MOVES data).\n
            attribute: str; the attribute for which the age=0 minimum is sought (e.g., calendar year).

        Returns:
            A single value representing the minimum value of attribute for which age=0.

        """
        return df.loc[df['ageID'] == 0, attribute].min()

    def calc_per_veh_cumulative_vmt(self):
        """

        This method calculates cumulative average VMT/vehicle year-over-year for use in estimating a typical VMT
        per year and for estimating emission repair costs.

        Returns:
            Updates the fleet object dictionary with cumulative annual average VMT/vehicle.

        """
        # this loop calculates the cumulative vmt for each key and saves it in the cumulative_vmt_dict
        cumulative_vmt_dict = dict()
        for key in self._dict.keys():
            vehicle, alt, model_year, age_id, disc_rate = key
            if (vehicle, alt, model_year, age_id - 1, 0) in cumulative_vmt_dict.keys():
                cumulative_vmt = cumulative_vmt_dict[(vehicle, 0, model_year, age_id - 1, 0)] \
                                 + self.get_attribute_value(key, 'VMT_PerVeh')
            else:
                cumulative_vmt = self.get_attribute_value(key, 'VMT_PerVeh')
            cumulative_vmt_dict[key] = cumulative_vmt

        # this loop updates the data object with the contents of the cumulative_vmt_dict
        for key in self._dict.keys():
            cumulative_vmt = cumulative_vmt_dict[key]
            self.update_dict(key, {'VMT_PerVeh_Cumulative': cumulative_vmt})

    def define_attributes_to_sum(self, program):
        """

        Parameters:
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n

        Returns:
            Updates the attributes_to_sum object dictionary.

        """
        # create a dictionary of attributes to be summed (dict keys) and what attributes to include in the sum (dict values)
        # use pre-tax fuel price for total costs since it serves as the basis for social costs; use retail for averages
        if program == 'CAP':
            self.attributes_to_sum = {'OperatingCost':
                                          ['DEFCost', 'FuelCost_Pretax', 'EmissionRepairCost'],
                                      'TechAndOperatingCost':
                                          ['TechCost', 'OperatingCost'],
                                      'OperatingCost_Owner_PerMile':
                                          ['DEFCost_PerMile', 'FuelCost_Retail_PerMile', 'EmissionRepairCost_PerMile'],
                                      'OperatingCost_Owner_PerVeh':
                                          ['DEFCost_PerVeh', 'FuelCost_Retail_PerVeh', 'EmissionRepairCost_PerVeh']}
        else:
            self.attributes_to_sum = {'OperatingCost':
                                          ['FuelCost_Pretax'],
                                      'TechAndOperatingCost':
                                          ['TechCost', 'OperatingCost'],
                                      'OperatingCost_Owner_PerMile':
                                          ['FuelCost_Retail_PerMile'],
                                      'OperatingCost_Owner_PerVeh':
                                          ['FuelCost_Retail_PerVeh']}

    def define_attributes_with_tech(self, program):
        """

        Parameters:
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n

        Returns:
            Updates the attributes_with_tech object dictionary.

        """
        if program == 'CAP':
            self.attributes_with_tech = ['VPOP', 'VMT', 'Gallons']
        else:
            self.attributes_with_tech = ['VPOP']

    def update_dict(self, key, input_dict):
        """

        Parameters:
            key: tuple; ((sourcetype_id, regclass_id, fueltype_id), option_id, model_year, age_id, discount_rate).\n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        Note:
            The method updates an existing key having attribute_name with attribute_value.

        """
        for attribute_name, attribute_value in input_dict.items():
            self._dict[key][attribute_name] = attribute_value

    def add_key_value_pairs(self, key, input_dict):
        """

        Parameters:
            key: tuple; ((sourcetype_id, regclass_id, fueltype_id), option_id, model_year, age_id, discount_rate).\n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        Note:
            This method updates the dictionary with a key with input_dict as a nested dictionary.

        """
        self._dict[key] = input_dict


def create_new_attributes(general_inputs, program):
    """

    Parameters:
        general_inputs: object; the GeneralInputs class object. \n
        program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').

    Returns:
        A list of new attributes to be added to the data_object dictionary.

    """
    if program == 'CAP':
        new_attributes = ['DirectCost',
                          'WarrantyCost',
                          'RnDCost',
                          'OtherCost',
                          'ProfitCost',
                          'IndirectCost',
                          'TechCost',
                          'DEF_Gallons',
                          'DEFCost',
                          'GallonsCaptured_byORVR',
                          'FuelCost_Retail',
                          'FuelCost_Pretax',
                          'EmissionRepairCost',
                          'OperatingCost',
                          'TechAndOperatingCost'
                          'VMT_PerVeh',
                          'VMT_PerVeh_Cumulative',
                          'DirectCost_PerVeh',
                          'WarrantyCost_PerVeh',
                          'RnDCost_PerVeh',
                          'OtherCost_PerVeh',
                          'ProfitCost_PerVeh',
                          'IndirectCost_PerVeh',
                          'TechCost_PerVeh',
                          'DEFCost_PerMile',
                          'DEFCost_PerVeh',
                          'FuelCost_Retail_PerMile',
                          'FuelCost_Retail_PerVeh',
                          'EmissionRepairCost_PerMile',
                          'EmissionRepairCost_PerVeh',
                          'OperatingCost_Owner_PerMile',
                          'OperatingCost_Owner_PerVeh',
                          ]
    else:
        new_attributes = ['TechCost',
                          'FuelCost_Retail',
                          'FuelCost_Pretax',
                          'OperatingCost',
                          'TechAndOperatingCost'
                          'VMT_PerVeh',
                          'VMT_PerVeh_Cumulative',
                          'TechCost_PerVeh',
                          'FuelCost_Retail_PerMile',
                          'FuelCost_Retail_PerVeh',
                          'OperatingCost_Owner_PerMile',
                          'OperatingCost_Owner_PerVeh',
                          ]

    if general_inputs.get_attribute_value('calculate_cap_pollution_effects') == 'Y':
        cap_attributes = ['PM25Cost_tailpipe_0.03', 'NOxCost_tailpipe_0.03',
                          'PM25Cost_tailpipe_0.07', 'NOxCost_tailpipe_0.07',
                          'CriteriaCost_tailpipe_0.03', 'CriteriaCost_tailpipe_0.07',
                          ]
        new_attributes = new_attributes + cap_attributes

    if general_inputs.get_attribute_value('calculate_ghg_pollution_effects') == 'Y':
        ghg_attributes = ['CO2Cost_tailpipe_0.05', 'CO2Cost_tailpipe_0.03', 'CO2Cost_tailpipe_0.025',
                          'CO2Cost_tailpipe_0.03_95',
                          'CH4Cost_tailpipe_0.05', 'CH4Cost_tailpipe_0.03', 'CH4Cost_tailpipe_0.025',
                          'CH4Cost_tailpipe_0.03_95',
                          'N2OCost_tailpipe_0.05', 'N2OCost_tailpipe_0.03', 'N2OCost_tailpipe_0.025',
                          'N2OCost_tailpipe_0.03_95',
                          'GHGCost_tailpipe_0.05', 'GHGCost_tailpipe_0.03', 'GHGCost_tailpipe_0.025',
                          'GHGCost_tailpipe_0.03_95',
                          ]
        new_attributes = new_attributes + ghg_attributes

    return new_attributes


def add_keys_for_discounting(general_inputs, input_dict):
    """

    Parameters:
        general_inputs: object; the GeneralInputs class object.\n
        input_dict: Dictionary; into which new keys will be added that provide room for discounting data.

    Returns:
        The passed dictionary with new keys added.

    """
    rates = [general_inputs.get_attribute_value('social_discount_rate_1'),
             general_inputs.get_attribute_value('social_discount_rate_2')]
    rates = [pd.to_numeric(rate) for rate in rates]
    for rate in rates:
        update_dict = dict()
        for key in input_dict.keys():
            vehicle, alt, model_year, age, discount_rate = key
            update_dict[vehicle, alt, model_year, age, rate] = input_dict[key].copy()
            update_dict[vehicle, alt, model_year, age, rate]['DiscountRate'] = rate
        input_dict.update(update_dict)
