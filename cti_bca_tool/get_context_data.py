import pandas as pd


class GetFuelPrices:

    def __init__(self, input_file, aeo_case, id_col, *fuels):
        """The GetFuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.

        Parameters:
            input_file: The file containing fuel price data.\n
            aeo_case: From the BCA inputs sheet - the AEO fuel case to use (a CSV of fuel prices must exist in the aeo directory).\n
            id_col: The column name where id data can be found.\n
            *fuels: AEO descriptor for the fuel prices needed in the project (e.g., Motor Gasoline, Diesel).

        Note:
            This class assumes a file structured like those published by EIA in the Annual Energy Outlook.

        """
        self.input_file = input_file
        self.aeo_case = aeo_case
        self.id_col = id_col
        self.fuels = fuels
        self.fuel_dict = {'Motor Gasoline': 1,
                          'Diesel': 2,
                          'CNG': 3,
                          }

    def __repr__(self):
        return f'\n{self.__class__.__name__}: AEO {self.aeo_case}'

    def aeo_dollars(self):
        """

        Returns:
            An integer value representing the dollar basis of the AEO report.

        """
        return int(self.input_file.at[0, 'units'][0: 4])

    def select_aeo_table_rows(self, df_source, row):
        """

        Parameters:
            df_source: The DataFrame of AEO fuel prices.\n
            row: The specific row to select.

        Returns:
            A DataFrame of the specific fuel price row.

        """
        df_return = df_source.loc[df_source[self.id_col] == row[self.id_col], :]
        df_return = df_return.iloc[:, :-1]
        return df_return

    def row_dict(self, fuel):
        """

        Parameters:
            fuel: The fuel (gasoline/diesel).

        Returns:
            A dictionary of fuel prices.

        """
        return_dict = dict()
        return_dict['retail_prices'] = {self.id_col: f'Price Components: {fuel}: End-User Price: {self.aeo_case}'}
        return_dict['distribution_costs'] = {self.id_col: f'Price Components: {fuel}: End-User Price: Distribution Costs: {self.aeo_case}'}
        return_dict['wholesale_price'] = {self.id_col: f'Price Components: {fuel}: End-User Price: Wholesale Price: {self.aeo_case}'}
        # return_dict['tax_allowance'] = {self.id_col: f'Price Components: {fuel}: End-User Price: Tax/Allowance: {self.aeo_case}'}
        return return_dict

    def melt_df(self, df, value_name):
        """

        Parameters:
            df: The DataFrame of fuel prices to melt.\n
            value_name: The name of the melted values.

        Returns:
            A DataFrame of melted value_name data by year.

        """
        df = pd.melt(df, id_vars=[self.id_col], value_vars=[col for col in df.columns if '20' in col], var_name='yearID', value_name=value_name)
        df['yearID'] = df['yearID'].astype(int)
        return df

    def get_prices(self):
        """

        Returns:
            A DataFrame of fuel prices for the given AEO case. Note that CNG prices are set equivalent to gasoline prices.

        """
        fuel_prices_dict = dict()
        fuel_prices_df = pd.DataFrame()
        for fuel in self.fuels:
            retail_prices = self.select_aeo_table_rows(self.input_file, self.row_dict(fuel)['retail_prices'])
            fuel_prices_dict[fuel] = self.melt_df(retail_prices, 'retail_fuel_price')

            distribution_costs = self.select_aeo_table_rows(self.input_file, self.row_dict(fuel)['distribution_costs'])
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(self.melt_df(distribution_costs, 'distribution_costs'), on='yearID')

            wholesale_price = self.select_aeo_table_rows(self.input_file, self.row_dict(fuel)['wholesale_price'])
            fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(self.melt_df(wholesale_price, 'wholesale_price'), on='yearID')

            # tax_allowance = self.select_aeo_table_rows(prices_full, self.row_dict(fuel)['tax_allowance'])
            # fuel_prices_dict[fuel] = fuel_prices_dict[fuel].merge(self.melt_df(tax_allowance, 'tax_allowance'), on='yearID')

            fuel_prices_dict[fuel].insert(len(fuel_prices_dict[fuel].columns),
                                          'pretax_fuel_price',
                                          fuel_prices_dict[fuel]['distribution_costs'] + fuel_prices_dict[fuel]['wholesale_price'])
            fuel_prices_dict[fuel].insert(0, 'fuelTypeID', self.fuel_dict[fuel])
            fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict[fuel]], ignore_index=True, axis=0)
        fuel_prices_dict['CNG'] = fuel_prices_dict['Motor Gasoline'].copy()
        fuel_prices_dict['CNG']['fuelTypeID'] = self.fuel_dict['CNG']
        fuel_prices_df = pd.concat([fuel_prices_df, fuel_prices_dict['CNG']], ignore_index=True, axis=0)
        fuel_prices_df = fuel_prices_df[['yearID', 'fuelTypeID', 'retail_fuel_price', 'pretax_fuel_price']]
        return fuel_prices_df


class GetDeflators:
    def __init__(self, input_file, id_col, id_value):
        """The GetDeflators class returns the GDP Implicit Price Deflators for use in adjusting monetized values to a consistent cost basis.

        Parameters:
            input_file: The file containing price deflator data.\n
            id_col: The column name where id data can be found.\n
            id_value: The value within id_col to return.

        Note:
             This class assumes a file structured like those published by the Bureau of Economic Analysis.
        """
        self.input_file = input_file
        self.id_col = id_col
        self.id_value = id_value

    def __repr__(self):
        return f'{self.__class__.__name__}: {self.id_value}'

    def deflator_df(self):
        """

        Returns:
            A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed from the 'full name' column entries.

        """
        df_return = pd.DataFrame(self.input_file)
        df_return = pd.DataFrame(df_return.loc[df_return[self.id_col].str.endswith(f'{self.id_value}'), :]).reset_index(drop=True)
        df_return.replace({self.id_col: f': {self.id_value}'}, {self.id_col: ''}, regex=True, inplace=True)
        return df_return

    def melt_df(self, value_name, drop_col=None):
        """

        Parameters:
            value_name: The name for the resultant data column.\n
            drop_col: The name of any columns to be dropped after melt.

        Returns:
            The melted DataFrame with a column of data named value_name.

        """
        deflator_df = self.deflator_df()
        melt_df = pd.melt(deflator_df, id_vars=[self.id_col], value_vars=[col for col in deflator_df.columns if '20' in col], var_name='yearID', value_name=value_name)
        melt_df['yearID'] = melt_df['yearID'].astype(int)
        if drop_col:
            melt_df.drop(columns=drop_col, inplace=True)
        return melt_df

    def calc_adjustment_factors(self, dollar_basis):
        """

        Parameters:
            dollar_basis: The dollar basis for the analysis which is determined in-code using the AEO file.

        Returns:
            A dictionary of deflators and adjustment_factors to apply to monetized values to put them all on a consistent dollar basis.

        """
        deflators = self.melt_df('price_deflator', self.id_col)
        deflators['price_deflator'] = deflators['price_deflator'].astype(float)
        basis_factor_df = pd.DataFrame(deflators.loc[deflators['yearID'] == dollar_basis, 'price_deflator']).reset_index(drop=True)
        basis_factor = basis_factor_df.at[0, 'price_deflator']
        deflators.insert(len(deflators.columns),
                         'adjustment_factor',
                         basis_factor / deflators['price_deflator'])
        deflators = deflators.set_index('yearID')
        deflators_dict = deflators.to_dict('index')
        return deflators_dict


if __name__ == '__main__':
    """
    This tests the context data creation if run as a script (python -m cti_bca_tool.get_context_data).
    """
    from pathlib import Path
    import cti_bca_tool.general_functions as gen_fxns

    path_project = Path.cwd()
    path_dev = path_project / 'dev'
    path_dev.mkdir(exist_ok=True)
    path_inputs = path_project / 'inputs'
    path_context = path_project / 'context_inputs'

    input_files_df = gen_fxns.read_input_files(path_inputs, 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    input_files_dict = input_files_df.to_dict('index')    
    context_files_df = gen_fxns.read_input_files(path_inputs, 'Context_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    context_files_dict = context_files_df.to_dict('index')
    fuel_prices_file = gen_fxns.read_input_files(path_context, context_files_dict['fuel_prices_file']['UserEntry.csv'], skiprows=4, reset_index=True)
    deflators_file = gen_fxns.read_input_files(path_context, context_files_dict['deflators_file']['UserEntry.csv'], skiprows=4, reset_index=True)

    aeo_case_1 = 'Reference case'
    fuel_prices_obj = GetFuelPrices(fuel_prices_file, aeo_case_1, 'full name', 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()
    fuel_prices.to_csv(path_project / f'dev/fuel_prices_{aeo_case_1}.csv', index=False)

    aeo_case_2 = 'High oil price'
    fuel_prices_obj = GetFuelPrices(fuel_prices_file, aeo_case_2, 'full name', 'Motor Gasoline', 'Diesel')
    fuel_prices = fuel_prices_obj.get_prices()
    fuel_prices.to_csv(path_project / f'dev/fuel_prices_{aeo_case_2}.csv', index=False)

    deflators_obj = GetDeflators(deflators_file, 'Unnamed: 1', 'Gross domestic product')
    dollar_basis_analysis = fuel_prices_obj.aeo_dollars()
    deflators = deflators_obj.calc_adjustment_factors(dollar_basis_analysis)
    deflators = pd.DataFrame(deflators)
    deflators.to_csv(path_project / f'dev/gdp_deflators.csv', index=True)

    print(f'\nfuel_prices_{aeo_case_1}.csv, fuel_prices_{aeo_case_2}.csv & gdp_deflators.csv (dollar basis = {dollar_basis_analysis}) have been saved to the {path_dev} folder.')
