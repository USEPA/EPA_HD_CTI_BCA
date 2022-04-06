import pandas as pd

from bca_tool_code.general_functions import read_input_file
from bca_tool_code.options_cap import OptionsCAP
from bca_tool_code.moves_adjustments_cap import MovesAdjCAP


class MovesCAP:
    """

    The MovesCAP class reads the MOVES input data file and provides methods to query its contents.

    """

    _data = dict()
    args_with_tech = ['VPOP', 'VMT', 'Gallons']

    @staticmethod
    def init_from_file(filepath):

        MovesCAP._data.clear()

        df = read_input_file(filepath)

        df.insert(0, 'DiscountRate', 0)
        df.insert(df.columns.get_loc('modelYearID') + 1, 'ageID', df['yearID'] - df['modelYearID'])
        year_min = MovesCAP.get_age0_min_year(df, 'yearID')

        df = MovesCAP.create_fleet_df(df, year_min)

        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))

        df.set_index(key, inplace=True)

        MovesCAP._data = df.to_dict('index')

    @staticmethod
    def get_attribute(attribute_name):

        return MovesCAP._data[attribute_name]['UserEntry']

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

        for arg in MovesCAP.args_with_tech:
            df_return.insert(df_return.columns.get_loc(arg) + 1, f'{arg}_withTech', 0)

        for (vehicle, alt) in st_vehicles:
            st, rc, ft = vehicle
            adjustment = MovesAdjCAP.get_attribute(vehicle, alt, 'percent')
            growth = MovesAdjCAP.get_attribute(vehicle, alt, 'growth')

            for arg in MovesCAP.args_with_tech:
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
