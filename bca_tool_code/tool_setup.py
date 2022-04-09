import pandas as pd
from pathlib import Path

from bca_tool_code.input_modules.input_files import InputFiles
from bca_tool_code.input_modules.general_inputs import GeneralInputs
from bca_tool_code.input_modules.deflators import Deflators
from bca_tool_code.input_modules.fuel_prices import FuelPrices
from bca_tool_code.input_modules.options_cap import OptionsCAP
from bca_tool_code.input_modules.options_ghg import OptionsGHG
from bca_tool_code.input_modules.regclass_costs import RegclassCosts
from bca_tool_code.input_modules.regclass_learning_scalers import RegclassLearningScalers
from bca_tool_code.input_modules.markups import Markups
from bca_tool_code.input_modules.warranty import Warranty
from bca_tool_code.input_modules.useful_life import UsefulLife
from bca_tool_code.input_modules.moves_adjustments_cap import MovesAdjCAP
from bca_tool_code.input_modules.dollar_per_ton_cap import DollarPerTonCAP
from bca_tool_code.input_modules.def_prices import DefPrices
from bca_tool_code.input_modules.def_doserates import DefDoseRates
from bca_tool_code.input_modules.orvr_fuelchanges_cap import OrvrFuelChangesCAP
from bca_tool_code.input_modules.repair_and_maintenance import RepairAndMaintenance
from bca_tool_code.annual_summary import AnnualSummary

from bca_tool_code.fleet_cap import FleetCAP
from bca_tool_code.regclass_sales import RegClassSales


class SetPaths:
    """

    The SetPaths class sets the paths and run_id info used by the tool.

    """
    def __init__(self):
        self.path_code = Path(__file__).parent
        self.path_project = self.path_code.parent
        self.path_inputs = self.path_project / 'inputs'
        self.path_input_modules = self.path_project / 'input_modules'
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
            df: DataFrame; contains input filenames based on the General_Inputs.csv file.

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

        InputFiles.init_from_file(set_paths.path_inputs / 'Input_Files.csv')
        GeneralInputs.init_from_file(set_paths.path_inputs / InputFiles.get_filename('bca_inputs'))
        general_inputs = GeneralInputs()

        # determine what's being run
        self.no_action_alt = pd.to_numeric(general_inputs.get_attribute_value('no_action_alt'))
        calc_cap_costs_value = general_inputs.get_attribute_value('calculate_cap_costs')
        calc_cap_pollution_effects_value = general_inputs.get_attribute_value('calculate_cap_pollution_effects')
        calc_ghg_costs_value = general_inputs.get_attribute_value('calculate_ghg_costs')
        calc_ghg_pollution_effects_value = general_inputs.get_attribute_value('calculate_ghg_pollution_effects')

        self.calc_cap_costs = True if calc_cap_costs_value == 'Y' else None
        self.calc_cap_pollution = True if calc_cap_pollution_effects_value == 'Y' else None
        self.calc_ghg_costs = True if calc_ghg_costs_value == 'Y' else None
        self.calc_ghg_pollution = True if calc_ghg_pollution_effects_value == 'Y' else None

        Deflators.init_from_file(set_paths.path_inputs / InputFiles.get_filename('deflators'), general_inputs)
        FuelPrices.init_from_file(set_paths.path_inputs / InputFiles.get_filename('fuel_prices'), general_inputs)

        self.general_inputs = GeneralInputs()
        self.deflators = Deflators()
        self.fuel_prices = FuelPrices()

        if self.calc_cap_costs:

            OptionsCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('options_cap'))
            MovesAdjCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('moves_adjustments_cap'))
            FleetCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('fleet_cap'), general_inputs)
            RegclassCosts.init_from_file(set_paths.path_inputs / InputFiles.get_filename('regclass_costs'), general_inputs)
            RegclassLearningScalers.init_from_file(
                set_paths.path_inputs / InputFiles.get_filename('regclass_learning_scalers'))

            Markups.init_from_file(set_paths.path_inputs / InputFiles.get_filename('markups'))
            Warranty.init_from_file(set_paths.path_inputs / InputFiles.get_filename('warranty'))
            UsefulLife.init_from_file(set_paths.path_inputs / InputFiles.get_filename('useful_life'))
            DefDoseRates.init_from_file(set_paths.path_inputs / InputFiles.get_filename('def_doserates'))
            DefPrices.init_from_file(set_paths.path_inputs / InputFiles.get_filename('def_prices'), general_inputs)
            OrvrFuelChangesCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('orvr_fuelchanges_cap'))
            RepairAndMaintenance.init_from_file(
                set_paths.path_inputs / InputFiles.get_filename('repair_and_maintenance'), general_inputs)

            self.fleet_cap = FleetCAP()
            self.options_cap = OptionsCAP()
            self.regclass_costs = RegclassCosts()
            self.regclass_learning_scalers = RegclassLearningScalers()
            self.markups = Markups()
            self.warranty = Warranty()
            self.useful_life = UsefulLife()
            self.def_prices = DefPrices()
            self.def_doserates = DefDoseRates()
            self.orvr_fuelchanges_cap = OrvrFuelChangesCAP()
            self.repair_and_maintenance = RepairAndMaintenance()

            # create additional and useful dicts and DataFrames
            RegClassSales.create_regclass_sales_dict(FleetCAP.fleet_df, self.regclass_costs.cost_steps)
            self.regclass_sales = RegClassSales()
            self.repair_cpm_dict = dict()
            self.estimated_ages_dict = dict()
            self.wtd_def_cpm_dict = dict()
            self.wtd_repair_cpm_dict = dict()
            self.wtd_cap_fuel_cpm_dict = dict()
            AnnualSummary.create_annual_summary_dict()
            self.annual_summary_cap = AnnualSummary()

        if self.calc_cap_pollution:
            DollarPerTonCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('dollar_per_ton_cap'))
            self.dollar_per_ton_cap = DollarPerTonCAP()

        if self.calc_ghg_costs:

            OptionsGHG.init_from_file(set_paths.path_inputs / InputFiles.get_filename('options_ghg'))
            # MovesAdjustmentsGHG
            # MovesGHG
            # SourcetypeCosts
            # SourcetypeLearningScalers

            self.options_ghg = OptionsGHG()

            if self.calc_cap_costs:
                pass
            else:
                Markups.init_from_file(set_paths.path_inputs / InputFiles.get_filename('markups'))
                Warranty.init_from_file(set_paths.path_inputs / InputFiles.get_filename('warranty'))
                UsefulLife.init_from_file(set_paths.path_inputs / InputFiles.get_filename('useful_life'))
                self.markups = Markups()
                self.warranty = Warranty()
                self.useful_life = UsefulLife()


            # OrvrFuelChangesGHG
        #
        # self.start_time = time.time()
        # self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
        # print(f'\nHD BCA tool version: {bca_tool_code.__version__}')
        # print(f'\nStart date and time:  {self.start_time_readable}')
        # print("\nReading input files...")
        #
        # self.start_time_read = time.time()
        # self.input_files_df = gen_fxns.read_input_file(set_paths.path_inputs / 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
        # self.input_files_dict = self.input_files_df.to_dict('index')

        # self.bca_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['bca_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        # self.deflators_dict = Deflators().init_from_file(
        #     set_paths.path_inputs / self.input_files_dict['deflators_file']['UserEntry.csv'], 2017)
        # self.regclass_costs = DirectCost().init_from_file(set_paths.path_inputs / self.input_files_dict['regclass_costs']['UserEntry.csv'])

        # self.regclass_costs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['regclass_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.sourcetype_costs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['sourcetype_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.regclass_learningscalers = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['regclass_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.sourcetype_learningscalers = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['sourcetype_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.markups_regclass = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['markups_regclass']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.markups_sourcetype = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['markups_sourcetype']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.warranty_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['warranty_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.usefullife_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['usefullife_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.moves_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.moves_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.moves_adjustments_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_adjustments_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.moves_adjustments_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['moves_adjustments_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.options_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['options_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        # self.options_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['options_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        # self.options_cap_dict = self.options_cap.to_dict('index')
        # self.options_ghg_dict = self.options_ghg.to_dict('index')
        # self.def_doserate_inputs = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['def_doserate_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.def_prices = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['def_prices']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.orvr_fuelchanges_cap = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['orvr_fuelchanges_cap']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.orvr_fuelchanges_ghg = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['orvr_fuelchanges_ghg']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
        # self.repair_and_maintenance = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['repair_and_maintenance']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
        # self.unit_conversions = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['unit_conversions']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)

        # self.fuel_prices_file = gen_fxns.read_input_file(set_paths.path_inputs / self.input_files_dict['fuel_prices_file']['UserEntry.csv'], skiprows=4, reset_index=True)

        # self.deflators_file = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['deflators_file']['UserEntry.csv'], skiprows=4, reset_index=True)
        # self.deflators_dict = Deflators().init_from_file(set_paths.path_inputs / self.input_files_dict['deflators_file']['UserEntry.csv'])
        #
        # self.input_files_pathlist = SetPaths().input_files_pathlist(self.input_files_df)
        #
        # self.elapsed_time_read = time.time() - self.start_time_read
        #
        # # set some year data
        # self.moves_cap.insert(self.moves_cap.columns.get_loc('modelYearID') + 1, 'ageID', self.moves_cap['yearID'] - self.moves_cap['modelYearID'])
        # self.moves_ghg.insert(self.moves_ghg.columns.get_loc('modelYearID') + 1, 'ageID', self.moves_ghg['yearID'] - self.moves_ghg['modelYearID'])
        # self.year_min = self.moves_cap.loc[self.moves_cap['ageID'] == 0, 'yearID'].min() # this will work for both calendar year and model year
        # self.year_max = self.moves_cap['yearID'].max() # this is the last calendar year included
        # self.model_year_max = self.moves_cap.loc[self.moves_cap['ageID'] == 0, 'modelYearID'].max() # calendar years could extend beyond the last model year included
        # self.years = range(self.year_min, self.year_max + 1)
        # self.model_years = range(self.year_min, self.model_year_max + 1)
        #
        # # parse values from the input files
        # self.calc_cap_value = self.bca_inputs.at['calculate_cap_costs', 'UserEntry']
        # self.calc_ghg_value = self.bca_inputs.at['calculate_ghg_costs', 'UserEntry']
        # self.calc_cap_pollution_effects_value = self.bca_inputs.at['calculate_cap_pollution_effects', 'UserEntry']
        # self.calc_ghg_pollution_effects_value = self.bca_inputs.at['calculate_ghg_pollution_effects', 'UserEntry']
        #
        # self.dollar_basis_analysis = pd.to_numeric(self.bca_inputs.at['dollar_basis_analysis', 'UserEntry'])
        # self.no_action_alt = pd.to_numeric(self.bca_inputs.at['no_action_alt', 'UserEntry'])
        # self.aeo_case = self.bca_inputs.at['aeo_fuel_price_case', 'UserEntry']
        # self.discount_to_yearID = pd.to_numeric(self.bca_inputs.at['discount_to_yearID', 'UserEntry'])
        # self.costs_start = self.bca_inputs.at['costs_start', 'UserEntry']
        # self.learning_rate = pd.to_numeric(self.bca_inputs.at['learning_rate', 'UserEntry'])
        #
        # self.warranty_vmt_share = pd.to_numeric(self.bca_inputs.at['warranty_vmt_share', 'UserEntry'])
        # self.r_and_d_vmt_share = pd.to_numeric(self.bca_inputs.at['r_and_d_vmt_share', 'UserEntry'])
        # self.indirect_cost_scaling_metric = self.bca_inputs.at['scale_indirect_costs_by', 'UserEntry']
        # self.def_gallons_per_ton_nox_reduction = pd.to_numeric(self.bca_inputs.at['def_gallons_per_ton_nox_reduction', 'UserEntry'])
        # self.max_age_included = pd.to_numeric(self.bca_inputs.at['weighted_operating_cost_thru_ageID', 'UserEntry'])
        # self.social_discount_rate_1 = pd.to_numeric(self.bca_inputs.at['social_discount_rate_1', 'UserEntry'])
        # self.social_discount_rate_2 = pd.to_numeric(self.bca_inputs.at['social_discount_rate_2', 'UserEntry'])
        # self.criteria_discount_rate_1 = pd.to_numeric(self.bca_inputs.at['criteria_discount_rate_1', 'UserEntry'])
        # self.criteria_discount_rate_2 = pd.to_numeric(self.bca_inputs.at['criteria_discount_rate_2', 'UserEntry'])
        #
        # self.grams_per_short_ton = self.unit_conversions.at['grams_per_short_ton', 'UserEntry']
        # self.gallons_per_ml = self.unit_conversions.at['gallons_per_ml', 'UserEntry']
        #
        # self.calc_cap = True if self.calc_cap_value == 'Y' else None
        # self.calc_ghg = True if self.calc_ghg_value == 'Y' else None
        # self.calc_cap_pollution_effects = True if self.calc_cap_pollution_effects_value == 'Y' else None
        # self.calc_ghg_pollution_effects = True if self.calc_ghg_pollution_effects_value == 'Y' else None
        #
        # # now adjust some things as needed
        # if 'Alternative' in self.moves_cap.columns.tolist():
        #     self.moves_cap.rename(columns={'Alternative': 'optionID'}, inplace=True)
        # if 'Alternative' in self.moves_ghg.columns.tolist():
        #     self.moves_ghg.rename(columns={'Alternative': 'optionID'}, inplace=True)
        # self.number_alts_cap = len(self.options_cap['OptionName'].unique())
        # self.number_alts_ghg = len(self.options_ghg['OptionName'].unique())
    
        # get the fuel price inputs and usd basis for the analysis
        # self.fuel_prices_obj = FuelPrices(self.fuel_prices_file, 'Reference case', 'full name', 'Motor Gasoline', 'Diesel')
        # self.fuel_prices_obj = FuelPrices(self.fuel_prices_file, self.aeo_case, 'full name', 'Motor Gasoline', 'Diesel')
        # print(self.fuel_prices_obj)
        # self.fuel_prices = self.fuel_prices_obj.get_prices()
        # self.dollar_basis_analysis = self.fuel_prices_obj.aeo_dollars()
    
        # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
        # self.deflators_obj = GetDeflators(self.deflators_file, 'Unnamed: 1', 'Gross domestic product')
        # self.gdp_deflators = self.deflators_obj.calc_adjustment_factors(self.dollar_basis_analysis)
        # self.cost_steps_regclass = [col for col in self.regclass_costs.columns if '20' in col]

        # self.cost_steps_sourcetype = [col for col in self.sourcetype_costs.columns if '20' in col]
        # # gen_fxns.convert_dollars_to_analysis_basis(self.regclass_costs, self.gdp_deflators, self.dollar_basis_analysis, [step for step in self.cost_steps_regclass])
        # gen_fxns.convert_dollars_to_analysis_basis(self.sourcetype_costs, self.gdp_deflators, self.dollar_basis_analysis, [step for step in self.cost_steps_sourcetype])
        # gen_fxns.convert_dollars_to_analysis_basis(self.def_prices, self.gdp_deflators, self.dollar_basis_analysis, 'DEF_USDperGal')
        # gen_fxns.convert_dollars_to_analysis_basis(self.repair_and_maintenance, self.gdp_deflators, self.dollar_basis_analysis, 'Value')
        # gen_fxns.convert_dollars_to_analysis_basis(self.fuel_prices, self.gdp_deflators, self.dollar_basis_analysis, 'retail_fuel_price', 'pretax_fuel_price')
        #
        # # create any DataFrames and dictionaries and lists that are useful as part of settings (used throughout project)
        # self.moves_adjustments_cap_dict, self.moves_adjustments_ghg_dict = dict(), dict()
        # self.seedvol_factor_regclass_dict, self.seedvol_factor_sourcetype_dict = dict(), dict()
        # self.markup_inputs_regclass_dict, self.markup_inputs_sourcetype_dict = dict(), dict()
        # self.orvr_inputs_dict_cap, self.orvr_inputs_dict_ghg, self.fuel_prices_dict = dict(), dict(), dict()
        # self.def_doserate_inputs_dict, self.def_prices_dict = dict(), dict()
        # self.required_miles_and_ages_dict, self.criteria_cost_factors_dict = dict(), dict()
        # self.warranty_inputs_dict, self.usefullife_inputs_dict = dict(), dict()
        #
        # self.moves_adjustments_cap_dict = InputFileDict(self.moves_adjustments_cap_dict)\
        #     .create_project_dict(self.moves_adjustments_cap, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')
        # self.moves_adjustments_ghg_dict = InputFileDict(self.moves_adjustments_ghg_dict)\
        #     .create_project_dict(self.moves_adjustments_ghg, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')
        #
        # self.seedvol_factor_regclass_dict = InputFileDict(self.seedvol_factor_regclass_dict)\
        #     .create_project_dict(self.regclass_learningscalers, 'regClassID', 'fuelTypeID', 'optionID')
        # self.seedvol_factor_sourcetype_dict = InputFileDict(self.seedvol_factor_sourcetype_dict)\
        #     .create_project_dict(self.sourcetype_learningscalers, 'sourceTypeID', 'regClassID', 'fuelTypeID', 'optionID')
        #
        # self.markup_inputs_regclass_dict = InputFileDict(self.markup_inputs_regclass_dict)\
        #     .create_project_dict(self.markups_regclass, 'fuelTypeID', 'Markup_Factor', 'optionID')
        # self.markup_inputs_sourcetype_dict = InputFileDict(self.markup_inputs_sourcetype_dict)\
        #     .create_project_dict(self.markups_regclass, 'fuelTypeID', 'Markup_Factor', 'optionID')
        #
        # self.orvr_inputs_dict_cap = InputFileDict(self.orvr_inputs_dict_cap)\
        #     .create_project_dict(self.orvr_fuelchanges_cap, 'regClassID', 'fuelTypeID', 'optionID')
        # self.orvr_inputs_dict_ghg = InputFileDict(self.orvr_inputs_dict_ghg) \
        #     .create_project_dict(self.orvr_fuelchanges_ghg, 'regClassID', 'fuelTypeID', 'optionID')
        # self.fuel_prices_dict = InputFileDict(self.fuel_prices_dict)\
        #     .create_project_dict(self.fuel_prices, 'yearID', 'fuelTypeID')
        #
        # self.def_doserate_inputs_dict = InputFileDict(self.def_doserate_inputs_dict)\
        #     .create_project_dict(self.def_doserate_inputs, 'regClassID', 'fuelTypeID')
        # self.def_prices_dict = InputFileDict(self.def_prices_dict)\
        #     .create_project_dict(self.def_prices, 'yearID')
        #
        # self.warranty_inputs_dict = InputFileDict(self.warranty_inputs_dict)\
        #     .create_project_dict(self.warranty_inputs, 'regClassID', 'fuelTypeID', 'period', 'optionID')
        # self.usefullife_inputs_dict = InputFileDict(self.usefullife_inputs_dict) \
        #     .create_project_dict(self.usefullife_inputs, 'regClassID', 'fuelTypeID', 'period', 'optionID')
        # self.repair_inputs_dict = self.repair_and_maintenance.to_dict('index')
        #
        # self.markup_factors_unique_names = [arg for arg in self.markups_regclass['Markup_Factor'].unique()]
        # self.markup_factors_sourcetype = [arg for arg in self.markups_sourcetype['Markup_Factor'].unique()]
        #
        # # read criteria cost factors if needed
        # if self.calc_cap_pollution_effects:
        #     self.criteria_cost_factors = gen_fxns.read_input_files(set_paths.path_inputs, self.input_files_dict['criteria_emission_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
        #     self.criteria_cost_factors_dict = InputFileDict(self.criteria_cost_factors_dict)\
        #         .create_project_dict(self.criteria_cost_factors, 'yearID')
        #
        # if self.calc_ghg_pollution_effects:
        #     print('\nWARNING: The tool is not configured to calculate GHG effects at this time.')
        #
        # self.row_header_for_fleet_files = ['yearID', 'modelYearID', 'ageID', 'optionID', 'OptionName',
        #                                    'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName', 'fuelTypeID', 'fuelTypeName',
        #                                    'DiscountRate',
        #                                    ]
        # self.row_header_for_annual_summary_files = ['yearID', 'optionID', 'OptionName', 'DiscountRate']
