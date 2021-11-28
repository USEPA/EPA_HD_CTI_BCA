from pathlib import Path
from datetime import datetime
import time

import bca_tool_code
import bca_tool_code.general_functions as gen_fxns
from bca_tool_code.get_context_data import GetFuelPrices, GetDeflators
from bca_tool_code.project_dicts import *


class SetInputs:
    def __init__(self):
        """

        The SetInputs class establishes the input files to use and other input settings set in the BCA_Inputs file and needed within the tool.

        """
        # set paths
        self.path_code = Path(__file__).parent
        self.path_project = self.path_code.parent
        self.path_inputs = self.path_project / 'inputs'
        # path_inputs = get_folder('folder containing input files for the run')
        self.path_outputs = self.path_project / 'outputs'
        self.path_test = self.path_project / 'test'
    
        # create generator of files in path_code
        self.files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())
    
        # set run id and files to generate
        self.run_folder_identifier = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
        self.run_folder_identifier = self.run_folder_identifier if self.run_folder_identifier != '' else 'BCA-Tool-Results'
    
        self.generate_post_processing_files = True
    
        self.start_time = time.time()
        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
        print(f'\nHD BCA tool version: {bca_tool_code.__version__}')
        print(f'\nStart date and time:  {self.start_time_readable}')
        print("\nReading input files...")

        self.start_time_read = time.time()
        self.input_files_df = gen_fxns.read_input_files(self.path_inputs, 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
        self.input_files_dict = self.input_files_df.to_dict('index')
    
        self.bca_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['bca_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.regclass_costs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['regclass_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.sourcetype_costs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['sourcetype_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.regclass_learningscalers = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['regclass_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.sourcetype_learningscalers = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['sourcetype_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.markups_regclass = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['markups_regclass']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.markups_sourcetype = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['markups_sourcetype']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.warranty_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['warranty_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.usefullife_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['usefullife_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_cap = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['moves_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_ghg = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['moves_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_adjustments_cap = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['moves_adjustments_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.moves_adjustments_ghg = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['moves_adjustments_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.options_cap = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['options_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.options_ghg = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['options_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.options_cap_dict = self.options_cap.to_dict('index')
        self.options_ghg_dict = self.options_ghg.to_dict('index')
        self.def_doserate_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['def_doserate_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.def_prices = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['def_prices']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.orvr_fuelchanges = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['orvr_fuelchanges']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        self.repair_and_maintenance = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['repair_and_maintenance']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        self.unit_conversions = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['unit_conversions']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
    
        self.fuel_prices_file = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['fuel_prices_file']['UserEntry.csv'], skiprows=4, reset_index=True)
        self.deflators_file = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['deflators_file']['UserEntry.csv'], skiprows=4, reset_index=True)
    
        self.input_files_pathlist = list()
        for item in pd.Series(self.input_files_df['UserEntry.csv']):
            self.input_files_pathlist.append(self.path_inputs / item)
        # input_files_pathlist = [path_inputs / item for item in pd.Series(input_files_df['UserEntry.csv'])] -- cannot get this list comprehension to work with attr
        self.input_files_pathlist.append(self.path_inputs / 'Input_Files.csv')
    
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
    
        # now adjust some things and get dollar values on a consistent valuation
        if 'Alternative' in self.moves_cap.columns.tolist():
            self.moves_cap.rename(columns={'Alternative': 'optionID'}, inplace=True)
        if 'Alternative' in self.moves_ghg.columns.tolist():
            self.moves_ghg.rename(columns={'Alternative': 'optionID'}, inplace=True)
        self.number_alts = len(self.moves_cap['optionID'].unique())
    
        # get the fuel price inputs and usd basis for the analysis
        self.fuel_prices_obj = GetFuelPrices(self.fuel_prices_file, self.aeo_case, 'full name', 'Motor Gasoline', 'Diesel')
        print(self.fuel_prices_obj)
        self.fuel_prices = self.fuel_prices_obj.get_prices()
        self.dollar_basis_analysis = self.fuel_prices_obj.aeo_dollars()
    
        # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
        self.deflators_obj = GetDeflators(self.deflators_file, 'Unnamed: 1', 'Gross domestic product')
        self.gdp_deflators = self.deflators_obj.calc_adjustment_factors(self.dollar_basis_analysis)
        self.cost_steps_regclass = [col for col in self.regclass_costs.columns if '20' in col]
        self.cost_steps_sourcetype = [col for col in self.sourcetype_costs.columns if '20' in col]
        gen_fxns.convert_dollars_to_analysis_basis(self.regclass_costs, self.gdp_deflators, self.dollar_basis_analysis, [step for step in self.cost_steps_regclass])
        gen_fxns.convert_dollars_to_analysis_basis(self.sourcetype_costs, self.gdp_deflators, self.dollar_basis_analysis, [step for step in self.cost_steps_sourcetype])
        gen_fxns.convert_dollars_to_analysis_basis(self.def_prices, self.gdp_deflators, self.dollar_basis_analysis, 'DEF_USDperGal')
        gen_fxns.convert_dollars_to_analysis_basis(self.repair_and_maintenance, self.gdp_deflators, self.dollar_basis_analysis, 'Value')
    
        # create any DataFrames and dictionaries and lists that are useful as part of settings (used throughout project)
        self.moves_adjustments_cap_dict = create_moves_adjustments_dict(self.moves_adjustments_cap, 'regClassID', 'fuelTypeID', 'optionID')
        self.moves_adjustments_ghg_dict = create_moves_adjustments_dict(self.moves_adjustments_ghg, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')
        self.seedvol_factor_regclass_dict = create_seedvol_factor_dict(self.regclass_learningscalers, 'regClassID', 'fuelTypeID', 'optionID')
        self.seedvol_factor_sourcetype_dict = create_seedvol_factor_dict(self.sourcetype_learningscalers, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')
        self.markup_inputs_regclass_dict = create_markup_inputs_dict(self.markups_regclass)
        self.markup_inputs_sourcetype_dict = create_markup_inputs_dict(self.markups_sourcetype)
        self.markup_factors_unique_names = [arg for arg in self.markups_regclass['Markup_Factor'].unique()]
        self.markup_factors_sourcetype = [arg for arg in self.markups_sourcetype['Markup_Factor'].unique()]
        self.required_miles_and_ages_dict = create_required_miles_and_ages_dict(self.warranty_inputs, 'Warranty', self.usefullife_inputs, 'Usefullife')
        self.def_doserate_inputs_dict = create_def_doserate_inputs_dict(self.def_doserate_inputs)
        self.def_prices_dict = create_def_prices_dict(self.def_prices)
        self.orvr_inputs_dict = create_orvr_inputs_dict(self.orvr_fuelchanges)
        self.fuel_prices_dict = create_fuel_prices_dict(self.fuel_prices)
        self.repair_inputs_dict = self.repair_and_maintenance.to_dict('index')
    
        # read criteria cost factors if needed
        if self.calc_cap_pollution_effects:
            self.criteria_cost_factors = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['criteria_emission_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.criteria_cost_factors_dict = create_criteria_cost_factors_dict(self.criteria_cost_factors)
    
        if self.calc_ghg_pollution_effects:
            print('\nWARNING: The tool is not configured to calculate GHG effects at this time.')
    
        # create a row header list for the structure of the main output files
        self.row_header_for_fleet_files = ['vehicle', 'yearID', 'modelYearID', 'ageID', 'optionID', 'OptionName',
                                           'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName', 'fuelTypeID', 'fuelTypeName',
                                           'DiscountRate',
                                           ]
