import pandas as pd
from pathlib import Path
from datetime import datetime
import time

import bca_tool_code
import bca_tool_code.general_functions as gen_fxns
from bca_tool_code.get_context_data import GetFuelPrices, GetDeflators
from bca_tool_code.project_dicts import InputFileDict #, MilesAndAgesDict


class SetPaths:
    """

    The SetPaths class sets the paths and run_id info used by the tool.

    """
    def __init__(self):
        self.path_code = Path(__file__).parent
        self.path_project = self.path_code.parent
        self.path_inputs = self.path_project / 'inputs'
        self.path_outputs = self.path_project / 'outputs'
        self.path_test = self.path_project / 'test'

    def files_in_code_folder(self):
        """

        This is just a generator that allows for copy/paste of tool code into a bundle of folders and files saved to the outputs folder.

        Returns:
            A generator object.

        """
        files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())
        return files_in_path_code

    def input_files_pathlist(self, df):
        """

        Parameters:
            df: A DataFrame of input filenames based on the General_Inputs.csv file.

        Returns:
            A list of full path details for each of the input files allowing for copy/paste of those files into a bundle of folders and files saved to the outputs folder.

        """
        input_files_pathlist = [self.path_inputs / item for item in pd.Series(df['UserEntry.csv'])]
        input_files_pathlist.append(self.path_inputs / 'Input_Files.csv')
        return input_files_pathlist

    @staticmethod
    def run_id():
        """

        This method allows for a user-interactive identifier (name) for the given run.

        Returns:
            A console prompt to enter a run identifier; entering "test" sends outputs to a test folder; if left blank a default name is used.

        """
        # set run id and files to generate
        run_folder_identifier = input('\nProvide a run identifier for your output folder name (press return to use the default name)\n')
        run_folder_identifier = run_folder_identifier if run_folder_identifier != '' else 'BCA-Tool-Results'
        return run_folder_identifier

    def create_output_paths(self, start_time_readable, run_id):
        """

        Parameters::
            start_time_readable: String; the start time of the run, in text readable format.\n
            run_id: The run ID entered by the user or the default value if the user does not provide an ID.

        Returns:
            Output paths into which to save outputs of the given run.

        """
        self.path_outputs.mkdir(exist_ok=True)
        path_of_run_folder = self.path_outputs / f'{start_time_readable}_{run_id}'
        path_of_run_folder.mkdir(exist_ok=False)
        path_of_run_inputs_folder = path_of_run_folder / 'run_inputs'
        path_of_run_inputs_folder.mkdir(exist_ok=False)
        path_of_run_results_folder = path_of_run_folder / 'run_results'
        path_of_run_results_folder.mkdir(exist_ok=False)
        path_of_modified_inputs_folder = path_of_run_folder / 'modified_inputs'
        path_of_modified_inputs_folder.mkdir(exist_ok=False)
        path_of_code_folder = path_of_run_folder / 'code'
        path_of_code_folder.mkdir(exist_ok=False)

        return path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder


class SetInputs:
    def __init__(self):
        """

        The SetInputs class establishes the input files to use and other input settings set in the BCA_Inputs file and needed within the tool.

        """
        set_paths = SetPaths()

        self.start_time = time.time()
        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
        print(f'\nHD BCA tool version: {bca_tool_code.__version__}')
        print(f'\nStart date and time:  {self.start_time_readable}')
        print("\nReading input files...")

        self.start_time_read = time.time()
        self.input_files_df = gen_fxns.read_input_files(set_paths.path_inputs, 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
        self.input_files_dict = self.input_files_df.to_dict('index')

        self.bca_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['bca_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.regclass_costs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['regclass_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.sourcetype_costs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['sourcetype_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.regclass_learningscalers = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['regclass_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.sourcetype_learningscalers = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['sourcetype_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.markups_regclass = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['markups_regclass']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.markups_sourcetype = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['markups_sourcetype']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.warranty_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['warranty_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.usefullife_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['usefullife_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_adjustments_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_adjustments_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_adjustments_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_adjustments_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.options_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['options_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.options_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['options_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.options_cap_dict = self.options_cap.to_dict('index')
        self.options_ghg_dict = self.options_ghg.to_dict('index')
        self.def_doserate_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['def_doserate_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.def_prices = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['def_prices']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.orvr_fuelchanges_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['orvr_fuelchanges_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.orvr_fuelchanges_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['orvr_fuelchanges_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.repair_and_maintenance = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['repair_and_maintenance']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.unit_conversions = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['unit_conversions']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)

        self.fuel_prices_file = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['fuel_prices_file']['UserEntry.csv'], skiprows=4, reset_index=True)
        self.deflators_file = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['deflators_file']['UserEntry.csv'], skiprows=4, reset_index=True)

        self.input_files_pathlist = SetPaths().input_files_pathlist(self.input_files_df)

        self.elapsed_time_read = time.time() - self.start_time_read
    
        # set some year data
        self.moves_cap.insert(self.moves_cap.columns.get_loc('modelYearID') + 1, 'ageID', self.moves_cap['yearID'] - self.moves_cap['modelYearID'])
        self.moves_ghg.insert(self.moves_ghg.columns.get_loc('modelYearID') + 1, 'ageID', self.moves_ghg['yearID'] - self.moves_ghg['modelYearID'])
        self.year_min = self.moves_cap.loc[self.moves_cap['ageID'] == 0, 'yearID'].min() # this will work for both calendar year and model year
        self.year_max = self.moves_cap['yearID'].max() # this is the last calendar year included
        self.model_year_max = self.moves_cap.loc[self.moves_cap['ageID'] == 0, 'modelYearID'].max() # calendar years could extend beyond the last model year included
        self.years = range(self.year_min, self.year_max + 1)
        self.model_years = range(self.year_min, self.model_year_max + 1)
    
        # parse values from the input files
        self.calc_cap_value = self.bca_inputs.at['calculate_cap_costs', 'UserEntry']
        self.calc_ghg_value = self.bca_inputs.at['calculate_ghg_costs', 'UserEntry']
        self.calc_cap_pollution_effects_value = self.bca_inputs.at['calculate_cap_pollution_effects', 'UserEntry']
        self.calc_ghg_pollution_effects_value = self.bca_inputs.at['calculate_ghg_pollution_effects', 'UserEntry']

        self.dollar_basis_analysis = pd.to_numeric(self.bca_inputs.at['dollar_basis_analysis', 'UserEntry'])
        self.no_action_alt = pd.to_numeric(self.bca_inputs.at['no_action_alt', 'UserEntry'])
        self.aeo_case = self.bca_inputs.at['aeo_fuel_price_case', 'UserEntry']
        self.discrate_social_low = pd.to_numeric(self.bca_inputs.at['discrate_social_low', 'UserEntry'])
        self.discrate_social_high = pd.to_numeric(self.bca_inputs.at['discrate_social_high', 'UserEntry'])
        self.discount_to_yearID = pd.to_numeric(self.bca_inputs.at['discount_to_yearID', 'UserEntry'])
        self.costs_start = self.bca_inputs.at['costs_start', 'UserEntry']
        self.learning_rate = pd.to_numeric(self.bca_inputs.at['learning_rate', 'UserEntry'])

        self.warranty_vmt_share = pd.to_numeric(self.bca_inputs.at['warranty_vmt_share', 'UserEntry'])
        self.r_and_d_vmt_share = pd.to_numeric(self.bca_inputs.at['r_and_d_vmt_share', 'UserEntry'])
        self.indirect_cost_scaling_metric = self.bca_inputs.at['scale_indirect_costs_by', 'UserEntry']
        self.def_gallons_per_ton_nox_reduction = pd.to_numeric(self.bca_inputs.at['def_gallons_per_ton_nox_reduction', 'UserEntry'])
        self.max_age_included = pd.to_numeric(self.bca_inputs.at['weighted_operating_cost_thru_ageID', 'UserEntry'])
        self.social_discount_rate_1 = pd.to_numeric(self.bca_inputs.at['social_discount_rate_1', 'UserEntry'])
        self.social_discount_rate_2 = pd.to_numeric(self.bca_inputs.at['social_discount_rate_2', 'UserEntry'])
        self.criteria_discount_rate_1 = pd.to_numeric(self.bca_inputs.at['criteria_discount_rate_1', 'UserEntry'])
        self.criteria_discount_rate_2 = pd.to_numeric(self.bca_inputs.at['criteria_discount_rate_2', 'UserEntry'])
    
        self.grams_per_short_ton = self.unit_conversions.at['grams_per_short_ton', 'UserEntry']
        self.gallons_per_ml = self.unit_conversions.at['gallons_per_ml', 'UserEntry']

        self.calc_cap = True if self.calc_cap_value == 'Y' else None
        self.calc_ghg = True if self.calc_ghg_value == 'Y' else None
        self.calc_cap_pollution_effects = True if self.calc_cap_pollution_effects_value == 'Y' else None
        self.calc_ghg_pollution_effects = True if self.calc_ghg_pollution_effects_value == 'Y' else None
    
        # now adjust some things as needed
        if 'Alternative' in self.moves_cap.columns.tolist():
            self.moves_cap.rename(columns={'Alternative': 'optionID'}, inplace=True)
        if 'Alternative' in self.moves_ghg.columns.tolist():
            self.moves_ghg.rename(columns={'Alternative': 'optionID'}, inplace=True)
        self.number_alts_cap = len(self.options_cap['OptionName'].unique())
        self.number_alts_ghg = len(self.options_ghg['OptionName'].unique())
    
        # get the fuel price inputs and usd basis for the analysis
        self.fuel_prices_obj = GetFuelPrices(self.fuel_prices_file, self.aeo_case, 'full name', 'Motor Gasoline', 'Diesel')
        print(self.fuel_prices_obj)
        self.fuel_prices = self.fuel_prices_obj.get_prices()
        # self.dollar_basis_analysis = self.fuel_prices_obj.aeo_dollars()
    
        # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
        self.deflators_obj = GetDeflators(self.deflators_file, 'Unnamed: 1', 'Gross domestic product')
        self.gdp_deflators = self.deflators_obj.calc_adjustment_factors(self.dollar_basis_analysis)
        self.cost_steps_regclass = [col for col in self.regclass_costs.columns if '20' in col]
        self.cost_steps_sourcetype = [col for col in self.sourcetype_costs.columns if '20' in col]
        gen_fxns.convert_dollars_to_analysis_basis(self.regclass_costs, self.gdp_deflators, self.dollar_basis_analysis, [step for step in self.cost_steps_regclass])
        gen_fxns.convert_dollars_to_analysis_basis(self.sourcetype_costs, self.gdp_deflators, self.dollar_basis_analysis, [step for step in self.cost_steps_sourcetype])
        gen_fxns.convert_dollars_to_analysis_basis(self.def_prices, self.gdp_deflators, self.dollar_basis_analysis, 'DEF_USDperGal')
        gen_fxns.convert_dollars_to_analysis_basis(self.repair_and_maintenance, self.gdp_deflators, self.dollar_basis_analysis, 'Value')
        gen_fxns.convert_dollars_to_analysis_basis(self.fuel_prices, self.gdp_deflators, self.dollar_basis_analysis, 'retail_fuel_price', 'pretax_fuel_price')
    
        # create any DataFrames and dictionaries and lists that are useful as part of settings (used throughout project)
        # self.regclass_costs_dict,
        # self.sourcetype_costs_dict = dict()
        self.moves_adjustments_cap_dict, self.moves_adjustments_ghg_dict = dict(), dict()
        self.seedvol_factor_regclass_dict, self.seedvol_factor_sourcetype_dict = dict(), dict()
        self.markup_inputs_regclass_dict, self.markup_inputs_sourcetype_dict = dict(), dict()
        self.orvr_inputs_dict_cap, self.orvr_inputs_dict_ghg, self.fuel_prices_dict = dict(), dict(), dict()
        self.def_doserate_inputs_dict, self.def_prices_dict = dict(), dict()
        self.required_miles_and_ages_dict, self.criteria_cost_factors_dict = dict(), dict()
        self.warranty_inputs_dict, self.usefullife_inputs_dict = dict(), dict()

        # self.regclass_costs_dict = InputFileDict(self.regclass_costs_dict) \
        #     .create_project_dict(self.regclass_costs, 'regClassID', 'fuelTypeID', 'TechPackageDescription', 'optionID') # TechPkg added here to make unique keys
        # self.sourcetype_costs_dict = InputFileDict(self.sourcetype_costs_dict) \
        #     .create_project_dict(self.sourcetype_costs, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')

        self.moves_adjustments_cap_dict = InputFileDict(self.moves_adjustments_cap_dict)\
            .create_project_dict(self.moves_adjustments_cap, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')
        self.moves_adjustments_ghg_dict = InputFileDict(self.moves_adjustments_ghg_dict)\
            .create_project_dict(self.moves_adjustments_ghg, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')

        self.seedvol_factor_regclass_dict = InputFileDict(self.seedvol_factor_regclass_dict)\
            .create_project_dict(self.regclass_learningscalers, 'regClassID', 'fuelTypeID', 'optionID')
        self.seedvol_factor_sourcetype_dict = InputFileDict(self.seedvol_factor_sourcetype_dict)\
            .create_project_dict(self.sourcetype_learningscalers, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')

        self.markup_inputs_regclass_dict = InputFileDict(self.markup_inputs_regclass_dict)\
            .create_project_dict(self.markups_regclass, 'fuelTypeID', 'Markup_Factor', 'optionID')
        self.markup_inputs_sourcetype_dict = InputFileDict(self.markup_inputs_sourcetype_dict)\
            .create_project_dict(self.markups_regclass, 'fuelTypeID', 'Markup_Factor', 'optionID')

        self.orvr_inputs_dict_cap = InputFileDict(self.orvr_inputs_dict_cap)\
            .create_project_dict(self.orvr_fuelchanges_cap, 'regClassID', 'fuelTypeID', 'optionID')
        self.orvr_inputs_dict_ghg = InputFileDict(self.orvr_inputs_dict_ghg) \
            .create_project_dict(self.orvr_fuelchanges_ghg, 'regClassID', 'fuelTypeID', 'optionID')
        self.fuel_prices_dict = InputFileDict(self.fuel_prices_dict)\
            .create_project_dict(self.fuel_prices, 'yearID', 'fuelTypeID')

        self.def_doserate_inputs_dict = InputFileDict(self.def_doserate_inputs_dict)\
            .create_project_dict(self.def_doserate_inputs, 'regClassID', 'fuelTypeID')
        self.def_prices_dict = InputFileDict(self.def_prices_dict)\
            .create_project_dict(self.def_prices, 'yearID')

        self.warranty_inputs_dict = InputFileDict(self.warranty_inputs_dict)\
            .create_project_dict(self.warranty_inputs, 'regClassID', 'fuelTypeID', 'period', 'optionID')
        self.usefullife_inputs_dict = InputFileDict(self.usefullife_inputs_dict) \
            .create_project_dict(self.usefullife_inputs, 'regClassID', 'fuelTypeID', 'period', 'optionID')
        self.repair_inputs_dict = self.repair_and_maintenance.to_dict('index')
        # self.moves_adjustments_cap_dict = create_project_dict(self.moves_adjustments_cap, 'regClassID', 'fuelTypeID', 'optionID')
        # self.moves_adjustments_ghg_dict = create_project_dict(self.moves_adjustments_ghg, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')

        # self.seedvol_factor_regclass_dict = create_project_dict(self.regclass_learningscalers, 'regClassID', 'fuelTypeID', 'optionID')
        # self.seedvol_factor_sourcetype_dict = create_project_dict(self.sourcetype_learningscalers, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')

        # self.markup_inputs_regclass_dict = create_project_dict(self.markups_regclass, 'fuelTypeID', 'Markup_Factor', 'optionID')
        # self.markup_inputs_sourcetype_dict = create_project_dict(self.markups_regclass, 'fuelTypeID', 'Markup_Factor', 'optionID')

        # self.orvr_inputs_dict = create_project_dict(self.orvr_fuelchanges, 'regClassID', 'fuelTypeID', 'optionID')
        # self.fuel_prices_dict = create_project_dict(self.fuel_prices, 'yearID', 'fuelTypeID')

        # self.def_doserate_inputs_dict = create_project_dict(self.def_doserate_inputs, 'regClassID', 'fuelTypeID')
        # self.def_prices_dict = create_def_prices_dict(self.def_prices)

        self.markup_factors_unique_names = [arg for arg in self.markups_regclass['Markup_Factor'].unique()]
        self.markup_factors_sourcetype = [arg for arg in self.markups_sourcetype['Markup_Factor'].unique()]

        # self.required_miles_and_ages_dict = MilesAndAgesDict(self.required_miles_and_ages_dict)\
        #     .create_required_miles_and_ages_dict(self.warranty_inputs, self.usefullife_inputs, 'Warranty', 'Usefullife')

        # read criteria cost factors if needed
        if self.calc_cap_pollution_effects:
            self.criteria_cost_factors = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['criteria_emission_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.criteria_cost_factors_dict = InputFileDict(self.criteria_cost_factors_dict)\
                .create_project_dict(self.criteria_cost_factors, 'yearID')

        if self.calc_ghg_pollution_effects:
            print('\nWARNING: The tool is not configured to calculate GHG effects at this time.')

        self.row_header_for_fleet_files = ['yearID', 'modelYearID', 'ageID', 'optionID', 'OptionName',
                                           'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName', 'fuelTypeID', 'fuelTypeName',
                                           'DiscountRate',
                                           ]
        self.row_header_for_annual_summary_files = ['yearID', 'optionID', 'OptionName', 'DiscountRate']
