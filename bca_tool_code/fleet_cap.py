import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file
from bca_tool_code.input_modules.options_cap import OptionsCAP
from bca_tool_code.input_modules.moves_adjustments_cap import MovesAdjCAP


class FleetCAP:
    """

    The FleetCAP class reads the MOVES input data file and provides methods to query its contents.

    """

    _data = dict()
    args_with_tech = ['VPOP', 'VMT', 'Gallons']
    fleet_df = pd.DataFrame()

    @staticmethod
    def init_from_file(filepath, settings):

        FleetCAP._data.clear()

        df = read_input_file(filepath)

        df.insert(0, 'DiscountRate', 0)
        df.insert(df.columns.get_loc('modelYearID') + 1, 'ageID', df['yearID'] - df['modelYearID'])
        year_min = FleetCAP.get_age0_min_year(df, 'yearID')

        df = FleetCAP.create_fleet_df(df, year_min)
        FleetCAP.fleet_df = df.copy()

        new_attributes = FleetCAP.create_new_attributes(settings)

        for attribute in new_attributes:
            df.insert(len(df.columns), f'{attribute}', 0)

        df['VMT_PerVeh'] = df['VMT'] / df['VPOP']

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']),
                            df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.set_index(key, inplace=True)

        FleetCAP._data = df.to_dict('index')

        FleetCAP.calc_per_veh_cumulative_vmt()

        FleetCAP.add_keys_for_discounting(settings)

    @staticmethod
    def get_attribute_values(key, *attribute_names):

        attribute_values = list()
        for attribute_name in attribute_names:
            attribute_values.append(FleetCAP._data[key][attribute_name])

        return attribute_values

    @staticmethod
    def get_attribute_value(key, attribute_name):

        return FleetCAP._data[key][attribute_name]

    @staticmethod
    def create_new_attributes(settings):
        """

        Parameters:
            calc_cap_pollution: True or None. \n
            calc_ghg_pollution: True or None.

        Returns:
            A list of new attributes to be calculated and provided in output files.

        """
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

        if settings.get_attribute('calculate_cap_pollution_effects') == 'Y':
            cap_attributes = ['PM25Cost_tailpipe_0.03', 'NOxCost_tailpipe_0.03', 'SO2Cost_tailpipe_0.03',
                              'PM25Cost_tailpipe_0.07', 'NOxCost_tailpipe_0.07', 'SO2Cost_tailpipe_0.07',
                              'CriteriaCost_tailpipe_0.03', 'CriteriaCost_tailpipe_0.07',
                              ]
            new_attributes = new_attributes + cap_attributes

        if settings.get_attribute('calculate_ghg_pollution_effects') == 'Y':
            ghg_attributes = ['CO2Cost_tailpipe_0.05', 'CO2Cost_tailpipe_0.03', 'CO2Cost_tailpipe_0.025', 'CO2Cost_tailpipe_0.03_95',
                              'CH4Cost_tailpipe_0.05', 'CH4Cost_tailpipe_0.03', 'CH4Cost_tailpipe_0.025', 'CH4Cost_tailpipe_0.03_95',
                              'N2OCost_tailpipe_0.05', 'N2OCost_tailpipe_0.03', 'N2OCost_tailpipe_0.025', 'N2OCost_tailpipe_0.03_95',
                              'GHGCost_tailpipe_0.05', 'GHGCost_tailpipe_0.03', 'GHGCost_tailpipe_0.025', 'GHGCost_tailpipe_0.03_95',
                              ]
            new_attributes = new_attributes + ghg_attributes

        return new_attributes

    @staticmethod
    def add_keys_for_discounting(settings):
        """

        Parameters:
            input_dict: Dictionary; into which new keys will be added that provide room for discounting data. \n
            rates: Numeric; the discount rate keys to add.

        Returns:
            The passed dictionary with new keys added.

        """
        rates = [settings.get_attribute('social_discount_rate_1'), settings.get_attribute('social_discount_rate_2')]
        rates = [pd.to_numeric(rate) for rate in rates]
        for rate in rates:
            update_dict = dict()
            for key in FleetCAP._data.keys():
                vehicle, alt, model_year, age, discount_rate = key
                update_dict[vehicle, alt, model_year, age, rate] = FleetCAP._data[key].copy()
                update_dict[vehicle, alt, model_year, age, rate]['DiscountRate'] = rate
            FleetCAP._data.update(update_dict)

    @staticmethod
    def create_fleet_df(df, year_min):
        """

        Parameters:
            settings: The SetInputs class.\n
            input_df: DataFrame; the raw fleet input data (e.g., from MOVES). \n
            options_dict: Dictionary; provides the option IDs and names of options being run.\n
            adj_dict: Dictionary; provides any adjustments to be made to the data contained in input_df. \n
            args_with_tech: String(s); the attributes to be adjusted.

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
        option_id_list = [key for key in OptionsCAP._data.keys()]
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

        for arg in FleetCAP.args_with_tech:
            df_return.insert(df_return.columns.get_loc(arg) + 1, f'{arg}_withTech', 0)

        for (vehicle, alt) in st_vehicles:
            st, rc, ft = vehicle
            adjustment = MovesAdjCAP.get_attribute(vehicle, alt, 'percent')
            growth = MovesAdjCAP.get_attribute(vehicle, alt, 'growth')

            for arg in FleetCAP.args_with_tech:
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
        for key in FleetCAP._data.keys():
            vehicle, alt, model_year, age_id, disc_rate = key
            if (vehicle, alt, model_year, age_id-1, 0) in cumulative_vmt_dict.keys():
                cumulative_vmt = cumulative_vmt_dict[(vehicle, 0, model_year, age_id-1, 0)] \
                                 + FleetCAP.get_attribute_value(key, 'VMT_PerVeh')
            else:
                cumulative_vmt = FleetCAP.get_attribute_value(key, 'VMT_PerVeh')
            cumulative_vmt_dict[key] = cumulative_vmt

        # this loop updates the averages_dict with the contents of the cumulative_vmt_dict
        for key in FleetCAP._data.keys():
            cumulative_vmt = cumulative_vmt_dict[key]
            FleetCAP.update_dict(key, {'VMT_PerVeh_Cumulative': cumulative_vmt})

    @staticmethod
    def update_dict(key, input_dict):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        """
        for attribute, value in input_dict.items():
            FleetCAP._data[key][attribute] = value
