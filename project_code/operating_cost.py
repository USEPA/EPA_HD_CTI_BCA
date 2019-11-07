import pandas as pd
from project_code.vehicle import fuelTypeID

GRAMSperSHORTTON = 907185
GALLONSperML = 0.000264172

class OperatingCost:
    """The OperatingCost class calculates the operating costs (DEF (urea), fuel, etc.).

    :param input_df: The data that provides the necessary physical parameters.
    :type input_df: DataFrame
    """

    def __init__(self, input_df):
        self.input_df = input_df

    def def_doserate_scaling_factor(self):
        """Return the dose rate scaling factor to apply to fuel consumption in calculating urea operating costs."""
        def_doserates = self.input_df.copy()
        def_doserates.insert(len(def_doserates.columns), 'DEFDoseRate_PercentOfFuel', 0)
        def_doserates['DEFDoseRate_PercentOfFuel'] = ((def_doserates['standard_NOx'] - def_doserates['engineout_NOx'])
                                                      - def_doserates['intercept_DEFdoserate']) \
                                                     / def_doserates['slope_DEFdoserate']
        def_doserates.drop(columns=['engineout_NOx', 'standard_NOx', 'intercept_DEFdoserate', 'slope_DEFdoserate'], inplace=True)
        return def_doserates

    def def_cost_df(self, def_doserates, prices):
        """

        :param def_doserates: DEF scaling factors (dose rate inputs).
        :type def_doserates: DataFrame
        :param prices: DEF prices.
        :type prices: DataFrame
        :return: The passed DataFrame after adding the DEF operating cost metrics:
                ['DoseRate_PercentOfFuel', 'DEF_USDperGal', 'OperatingCost_Urea_TotalCost']
        """
        df = self.input_df.copy()
        df = df.merge(def_doserates, on=['optionID', 'modelYearID', 'regClassID', 'fuelTypeID'], how='left')
        df['DEFDoseRate_PercentOfFuel'].fillna(method='ffill', inplace=True)
        df.loc[df['fuelTypeID'] != 2, 'DEFDoseRate_PercentOfFuel'] = 0
        df['DEFDoseRate_PercentOfFuel'].fillna(0, inplace=True)
        df = df.merge(prices, on='yearID', how='left')
        df.insert(len(df.columns), 'OperatingCost_Urea_TotalCost', df[['Gallons', 'DEFDoseRate_PercentOfFuel', 'DEF_USDperGal']].product(axis=1))
        df.insert(len(df.columns), 'OperatingCost_Urea_CPM', df['OperatingCost_Urea_TotalCost'] / df['VMT'])
        return df

    def orvr_fuel_impacts_pct(self, _fuelchanges):
        """

        :param _fuelchanges: Adjustments to the MOVES run values to account for fuel impacts not captured in MOVES.
        :type _fuelchanges: DataFrame
        :return: The passed DataFrame after adding the fuel consumption metrics:
                ['Change_PercentOfFuel', 'Gallons' (adjusted)]
        """
        _fuelchanges.drop(columns='ml/g', inplace=True)
        df = self.input_df.copy()
        df = df.merge(_fuelchanges, on=['optionID', 'fuelTypeID'], how='left')
        df['Change_PercentOfFuel'].fillna(0, inplace=True)
        df['Gallons'] = df['Gallons'] * (1 + df['Change_PercentOfFuel'])
        return df

    def orvr_fuel_impacts_mlpergram(self, orvr_fuelchanges):
        """

        :param _fuelchanges: Adjustments to the MOVES run values to account for fuel impacts not captured in MOVES.
        :type _fuelchanges: DataFrame
        :return: The passed DataFrame after adding the fuel consumption metrics:
                ['Change_PercentOfFuel', 'Gallons' (adjusted)]
        """
        fuelchanges = orvr_fuelchanges.copy()
        fuelchanges.drop(columns='Change_PercentOfFuel', inplace=True)
        df = self.input_df.copy()
        df2 = pd.DataFrame(df.loc[df['optionID'] == 0, ['yearID', 'modelYearID', 'ageID', 'sourcetypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID', 'THC (US tons)']])
        df2.rename(columns={'THC (US tons)': 'THC_Option0'}, inplace=True)
        df = df.merge(df2, on=['yearID', 'modelYearID', 'ageID', 'sourcetypeID', 'regClassID', 'fuelTypeID', 'zerogramTechID'], how='left')
        df.insert(len(df.columns), 'THC_delta', df['THC (US tons)'] - df['THC_Option0'])
        df = df.merge(fuelchanges, on=['optionID', 'regClassID', 'fuelTypeID'], how='left')
        df['ml/g'].fillna(0, inplace=True)
        df['Gallons'] = df['Gallons'] + df['THC_delta'] * df['ml/g'] * GRAMSperSHORTTON * GALLONSperML
        df.drop(columns=['THC_Option0'], inplace=True)
        return df

    def fuel_costs(self, _prices):
        """

        :param _prices:  The fuel prices being used for the given run.
        :type _prices: DataFrame
        :return: The passed DataFrame after adding the fuel cost metrics:
                 ['pretax_fuelprice', 'retail_fuelprice', 'OperatingCost_Fuel_Pretax_TotalCost', 'OperatingCost_Fuel_Retail_TotalCost']
        """
        df = self.input_df.copy()
        prices_gasoline = pd.DataFrame(_prices, columns=['yearID', 'gasoline_retail', 'gasoline_pretax'])
        prices_diesel = pd.DataFrame(_prices, columns=['yearID', 'diesel_retail', 'diesel_pretax'])
        prices_gasoline.rename(columns={'gasoline_retail': 'retail_fuelprice', 'gasoline_pretax': 'pretax_fuelprice'}, inplace=True)
        prices_diesel.rename(columns={'diesel_retail': 'retail_fuelprice', 'diesel_pretax': 'pretax_fuelprice'}, inplace=True)
        id_gasoline = [k for k, v in fuelTypeID.items() if v == 'Gasoline'][0] # this determines the fuelTypeID of Gasoline
        id_diesel = [k for k, v in fuelTypeID.items() if v == 'Diesel'][0] # this determines the fuelTypeID of Diesel
        prices_gasoline.insert(0, 'fuelTypeID', id_gasoline)
        prices_diesel.insert(0, 'fuelTypeID', id_diesel)
        prices = pd.concat([prices_gasoline, prices_diesel], ignore_index=True)
        df = df.merge(prices, on=['yearID', 'fuelTypeID'], how='left')
        df['pretax_fuelprice'].fillna(method='ffill', inplace=True)
        df['retail_fuelprice'].fillna(method='ffill', inplace=True)
        df.insert(len(df.columns), 'OperatingCost_Fuel_Pretax_TotalCost', df[['Gallons', 'pretax_fuelprice']].product(axis=1))
        df.insert(len(df.columns), 'OperatingCost_Fuel_Retail_TotalCost', df[['Gallons', 'retail_fuelprice']].product(axis=1))
        df.insert(len(df.columns), 'OperatingCost_Fuel_Retail_CPM', df['OperatingCost_Fuel_Retail_TotalCost'] / df['VMT'])
        return df
