import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.ghg_input_modules.options_ghg import OptionsGHG
from bca_tool_code.ghg_input_modules.moves_adjustments_ghg import MovesAdjGHG


class FleetGHG:
    """

    The FleetGHG class reads the MOVES input data file and provides methods to query its contents.

    """

    _dict = dict()
    args_with_tech = ['VPOP']
    year_min = 0
    year_max = 0
    years = 0
    fleet_df = pd.DataFrame()

    # create a dictionary of attributes to be summed (dict keys) and what attributes to include in the sum (dict values)
    attributes_to_sum = {'OperatingCost':
                             ['FuelCost_Pretax'],
                         'TechAndOperatingCost':
                             ['TechCost', 'OperatingCost'],
                         'OperatingCost_Owner_PerMile':
                             ['FuelCost_Retail_PerMile'],
                         'OperatingCost_Owner_PerVeh':
                             ['FuelCost_Retail_PerVeh']}

    @staticmethod
    def init_from_file(filepath, general_inputs):

        FleetGHG._dict.clear()

        df = read_input_file(filepath)

        df.insert(0, 'DiscountRate', 0)
        df.insert(df.columns.get_loc('modelYearID') + 1, 'ageID', df['yearID'] - df['modelYearID'])

        year_min = FleetGHG.get_age0_min_year(df, 'yearID')
        FleetGHG.year_min = year_min

        year_max = df['yearID'].max()
        FleetGHG.year_max = year_max

        years = range(year_min, year_max + 1)
        FleetGHG.years = years

        df = FleetGHG.create_fleet_df(df, year_min)
        FleetGHG.fleet_df = df.copy()

        new_attributes = FleetGHG.create_new_attributes(general_inputs)

        df['VMT_PerVeh'] = df['VMT'] / df['VPOP']

        for attribute in new_attributes:
            df.insert(len(df.columns), f'{attribute}', 0)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']),
                            df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.set_index(key, inplace=True)

        FleetGHG._dict = df.to_dict('index')

        FleetGHG.calc_per_veh_cumulative_vmt()

        FleetGHG.add_keys_for_discounting(general_inputs)

    @staticmethod
    def get_attribute_values(key, *attribute_names):

        attribute_values = list()
        for attribute_name in attribute_names:
            attribute_values.append(FleetGHG._dict[key][attribute_name])

        return attribute_values

    @staticmethod
    def get_attribute_value(key, attribute_name):

        return FleetGHG._dict[key][attribute_name]

    @staticmethod
    def create_new_attributes(general_inputs):
        """

        Parameters:
            calc_cap_pollution: True or None. \n
            calc_ghg_pollution: True or None.

        Returns:
            A list of new attributes to be calculated and provided in output files.

        """
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
            ghg_attributes = ['CO2Cost_tailpipe_0.05', 'CO2Cost_tailpipe_0.03', 'CO2Cost_tailpipe_0.025', 'CO2Cost_tailpipe_0.03_95',
                              'CH4Cost_tailpipe_0.05', 'CH4Cost_tailpipe_0.03', 'CH4Cost_tailpipe_0.025', 'CH4Cost_tailpipe_0.03_95',
                              'N2OCost_tailpipe_0.05', 'N2OCost_tailpipe_0.03', 'N2OCost_tailpipe_0.025', 'N2OCost_tailpipe_0.03_95',
                              'GHGCost_tailpipe_0.05', 'GHGCost_tailpipe_0.03', 'GHGCost_tailpipe_0.025', 'GHGCost_tailpipe_0.03_95',
                              ]
            new_attributes = new_attributes + ghg_attributes

        return new_attributes

    @staticmethod
    def add_keys_for_discounting(general_inputs):
        """

        Parameters:
            input_dict: Dictionary; into which new keys will be added that provide room for discounting data. \n
            rates: Numeric; the discount rate keys to add.

        Returns:
            The passed dictionary with new keys added.

        """
        rates = [general_inputs.get_attribute_value('social_discount_rate_1'), general_inputs.get_attribute_value('social_discount_rate_2')]
        rates = [pd.to_numeric(rate) for rate in rates]
        for rate in rates:
            update_dict = dict()
            for key in FleetGHG._dict.keys():
                vehicle, alt, model_year, age, discount_rate = key
                update_dict[vehicle, alt, model_year, age, rate] = FleetGHG._dict[key].copy()
                update_dict[vehicle, alt, model_year, age, rate]['DiscountRate'] = rate
            FleetGHG._dict.update(update_dict)

    @staticmethod
    def create_fleet_df(df, year_min):
        """

        Parameters:
            df: DataFrame; the raw fleet input data (e.g., from MOVES). \n
            year_min: Int; the first model year for the DataFrame.

        Returns:
            A DataFrame of the MOVES inputs with necessary MOVES adjustments made according to the MOVES adjustments input file. The DataFrame will also add
            optionID/sourceTypeID/regClassID/fuelTypeID names and will use only those options included in the options.csv input file.

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
        option_id_list = [key for key in OptionsGHG._dict.keys()]
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
            zip(zip(df_return['sourceTypeID'], df_return['regClassID'], df_return['fuelTypeID']), df_return['optionID'])).unique()

        for arg in FleetGHG.args_with_tech:
            df_return.insert(df_return.columns.get_loc(arg) + 1, f'{arg}_withTech', 0)

        for (vehicle, alt) in st_vehicles:
            st, rc, ft = vehicle
            adjustment = MovesAdjGHG.get_attribute_value(vehicle, alt, 'percent')
            growth = MovesAdjGHG.get_attribute_value(vehicle, alt, 'growth')

            for arg in FleetGHG.args_with_tech:
                arg_with_tech = df_return.loc[(df_return['optionID'] == alt)
                                              & (df_return['sourceTypeID'] == st)
                                              & (df_return['regClassID'] == rc)
                                              & (df_return['fuelTypeID'] == ft), arg] * adjustment * (1 + growth)
                df_return.loc[(df_return['optionID'] == alt)
                              & (df_return['sourceTypeID'] == st)
                              & (df_return['regClassID'] == rc)
                              & (df_return['fuelTypeID'] == ft), f'{arg}_withTech'] = arg_with_tech

        return df_return

    @staticmethod
    def get_age0_min_year(df, attribute):

        return df.loc[df['ageID'] == 0, attribute].min()

    @staticmethod
    def calc_per_veh_cumulative_vmt():
        """This function calculates cumulative average VMT/vehicle year-over-year for use in estimating a typical VMT
        per year and for estimating emission repair costs.

        Parameters:
            fleet_dict: Dictionary; the fleet data.

        Returns:
            The dictionary updated with cumulative annual average VMT/vehicle.

        """
        # this loop calculates the cumulative vmt for each key with the averages_dict and saves it in the cumulative_vmt_dict
        cumulative_vmt_dict = dict()
        for key in FleetGHG._dict.keys():
            vehicle, alt, model_year, age_id, disc_rate = key
            if (vehicle, alt, model_year, age_id-1, 0) in cumulative_vmt_dict.keys():
                cumulative_vmt = cumulative_vmt_dict[(vehicle, 0, model_year, age_id-1, 0)] \
                                 + FleetGHG.get_attribute_value(key, 'VMT_PerVeh')
            else:
                cumulative_vmt = FleetGHG.get_attribute_value(key, 'VMT_PerVeh')
            cumulative_vmt_dict[key] = cumulative_vmt

        # this loop updates the averages_dict with the contents of the cumulative_vmt_dict
        for key in FleetGHG._dict.keys():
            cumulative_vmt = cumulative_vmt_dict[key]
            FleetGHG.update_dict(key, {'VMT_PerVeh_Cumulative': cumulative_vmt})

    @staticmethod
    def update_dict(key, input_dict):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        """
        for attribute_name, attribute_value in input_dict.items():
            FleetGHG._dict[key][attribute_name] = attribute_value

    @staticmethod
    def add_key_value_pairs(key, input_dict):

        FleetGHG._dict[key] = input_dict
