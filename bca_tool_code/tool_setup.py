import pandas as pd
from pathlib import Path
from time import time
from datetime import datetime
import shutil

from bca_tool_code.general_input_modules.input_files import InputFiles
from bca_tool_code.general_input_modules.general_inputs import GeneralInputs
from bca_tool_code.general_input_modules.deflators import Deflators
from bca_tool_code.general_input_modules.fuel_prices import FuelPrices
from bca_tool_code.general_input_modules.def_prices import DefPrices
from bca_tool_code.general_input_modules.markups import Markups
from bca_tool_code.general_input_modules.warranty import Warranty
from bca_tool_code.general_input_modules.useful_life import UsefulLife
from bca_tool_code.general_input_modules.dollar_per_ton_cap import DollarPerTonCAP

from bca_tool_code.cap_input_modules.options_cap import OptionsCAP
from bca_tool_code.cap_input_modules.moves_adjustments_cap import MovesAdjCAP
from bca_tool_code.cap_input_modules.regclass_costs import RegclassCosts
from bca_tool_code.cap_input_modules.regclass_learning_scalers import RegclassLearningScalers
from bca_tool_code.cap_input_modules.def_doserates import DefDoseRates
from bca_tool_code.cap_input_modules.orvr_fuelchanges_cap import OrvrFuelChangesCAP
from bca_tool_code.cap_input_modules.repair_and_maintenance import RepairAndMaintenance
from bca_tool_code.cap_modules.fleet_cap import FleetCAP
from bca_tool_code.cap_modules.regclass_sales import RegClassSales
from bca_tool_code.cap_modules.annual_summary import AnnualSummaryCAP

from bca_tool_code.ghg_input_modules.options_ghg import OptionsGHG
from bca_tool_code.ghg_input_modules.moves_adjustments_ghg import MovesAdjGHG
from bca_tool_code.ghg_input_modules.sourcetype_costs import SourceTypeCosts
from bca_tool_code.ghg_input_modules.sourcetype_learning_scalers import SourceTypeLearningScalers
from bca_tool_code.ghg_modules.fleet_ghg import FleetGHG
from bca_tool_code.ghg_modules.sourcetype_sales import SourceTypeSales
from bca_tool_code.ghg_modules.annual_summary import AnnualSummaryGHG


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

    def copy_code_to_destination(self, destination):
        """

        This is just a generator that allows for copy/paste of tool code into a bundle of folders and files saved to the outputs folder.

        Parameters:
            destination: Path; the destination folder; destination folder must exist prior to method call.

        Returns:
            Nothing, but copies contents of code folder to the destination.

        """
        # first copy files in the path_code folder
        files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())
        for file in files_in_path_code:
            shutil.copy2(file, destination / file.name)

        # now make subfolders in destination and copy files from path_code subfolders
        dirs_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_dir())
        for d in dirs_in_path_code:
            source_dir_name = Path(d).name
            destination_subdir = destination / source_dir_name
            destination_subdir.mkdir(exist_ok=False)
            files_in_source_dir = (entry for entry in d.iterdir() if entry.is_file())
            for file in files_in_source_dir:
                shutil.copy2(file, destination_subdir / file.name)

        return

    # def input_files_pathlist(self, df):
    #     """
    #
    #     Parameters:
    #         df: DataFrame; contains input filenames based on the General_Inputs.csv file.
    #
    #     Returns:
    #         A list of full path details for each of the input files allowing for copy/paste of those files into a bundle of folders and files saved to the outputs folder.
    #
    #     """
    #     input_files_pathlist = [self.path_inputs / item for item in pd.Series(df['UserEntry.csv'])]
    #     input_files_pathlist.append(self.path_inputs / 'Input_Files.csv')
    #
    #     return input_files_pathlist

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
        self.start_time = time()
        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

        InputFiles.init_from_file(set_paths.path_inputs / 'Input_Files.csv')
        GeneralInputs.init_from_file(set_paths.path_inputs / InputFiles.get_filename('bca_inputs'))
        self.general_inputs = GeneralInputs()

        # determine what's being run
        self.no_action_alt = pd.to_numeric(self.general_inputs.get_attribute_value('no_action_alt'))
        calc_cap_costs_value = self.general_inputs.get_attribute_value('calculate_cap_costs')
        calc_cap_pollution_effects_value = self.general_inputs.get_attribute_value('calculate_cap_pollution_effects')
        calc_ghg_costs_value = self.general_inputs.get_attribute_value('calculate_ghg_costs')
        calc_ghg_pollution_effects_value = self.general_inputs.get_attribute_value('calculate_ghg_pollution_effects')

        self.calc_cap_costs = True if calc_cap_costs_value == 'Y' else None
        self.calc_cap_pollution = True if calc_cap_pollution_effects_value == 'Y' else None
        self.calc_ghg_costs = True if calc_ghg_costs_value == 'Y' else None
        self.calc_ghg_pollution = True if calc_ghg_pollution_effects_value == 'Y' else None

        Deflators.init_from_file(set_paths.path_inputs / InputFiles.get_filename('deflators'), self.general_inputs)
        FuelPrices.init_from_file(set_paths.path_inputs / InputFiles.get_filename('fuel_prices'), self.general_inputs)
        DefPrices.init_from_file(set_paths.path_inputs / InputFiles.get_filename('def_prices'), self.general_inputs)

        self.input_files_pathlist = InputFiles.input_files_pathlist
        # self.general_inputs = GeneralInputs()
        self.deflators = Deflators()
        self.fuel_prices = FuelPrices()
        self.def_prices = DefPrices()

        if self.calc_cap_costs:
            OptionsCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('options_cap'))
            MovesAdjCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('moves_adjustments_cap'))
            FleetCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('fleet_cap'), self.general_inputs)
            RegclassCosts.init_from_file(set_paths.path_inputs / InputFiles.get_filename('regclass_costs'), self.general_inputs)
            RegclassLearningScalers.init_from_file(
                set_paths.path_inputs / InputFiles.get_filename('regclass_learning_scalers'))

            Markups.init_from_file(set_paths.path_inputs / InputFiles.get_filename('markups'))
            Warranty.init_from_file(set_paths.path_inputs / InputFiles.get_filename('warranty'))
            UsefulLife.init_from_file(set_paths.path_inputs / InputFiles.get_filename('useful_life'))
            DefDoseRates.init_from_file(set_paths.path_inputs / InputFiles.get_filename('def_doserates'))
            OrvrFuelChangesCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('orvr_fuelchanges_cap'))
            RepairAndMaintenance.init_from_file(
                set_paths.path_inputs / InputFiles.get_filename('repair_and_maintenance'), self.general_inputs)

            self.fleet_cap = FleetCAP()
            self.options_cap = OptionsCAP()
            self.regclass_costs = RegclassCosts()
            self.regclass_learning_scalers = RegclassLearningScalers()
            self.markups = Markups()
            self.warranty = Warranty()
            self.useful_life = UsefulLife()
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
            AnnualSummaryCAP.create_annual_summary_dict()
            self.annual_summary_cap = AnnualSummaryCAP()

        if self.calc_cap_pollution:
            DollarPerTonCAP.init_from_file(set_paths.path_inputs / InputFiles.get_filename('dollar_per_ton_cap'))
            self.dollar_per_ton_cap = DollarPerTonCAP()
            # self.input_files_pathlist.append(set_paths.path_inputs / InputFiles.get_filename('dollar_per_ton_cap'))

        if self.calc_ghg_costs:

            OptionsGHG.init_from_file(set_paths.path_inputs / InputFiles.get_filename('options_ghg'))
            MovesAdjGHG.init_from_file(set_paths.path_inputs / InputFiles.get_filename('moves_adjustments_ghg'))
            FleetGHG.init_from_file(set_paths.path_inputs / InputFiles.get_filename('fleet_ghg'), self.general_inputs)
            SourceTypeCosts.init_from_file(set_paths.path_inputs / InputFiles.get_filename('sourcetype_costs'), self.general_inputs)
            SourceTypeLearningScalers.init_from_file(set_paths.path_inputs / InputFiles.get_filename('sourcetype_learning_scalers'))

            self.fleet_ghg = FleetGHG()
            self.options_ghg = OptionsGHG()
            self.sourcetype_costs = SourceTypeCosts()
            self.sourcetype_learning_scalers = SourceTypeLearningScalers()

            # create additional and useful dicts and DataFrames
            SourceTypeSales.create_sourcetype_sales_dict(FleetGHG.fleet_df, self.sourcetype_costs.cost_steps)
            self.sourcetype_sales = SourceTypeSales()
            self.wtd_ghg_fuel_cpm_dict = dict()
            AnnualSummaryGHG.create_annual_summary_dict()
            self.annual_summary_ghg = AnnualSummaryGHG()

            if self.calc_cap_costs:
                pass
            else:
                Markups.init_from_file(set_paths.path_inputs / InputFiles.get_filename('markups'))
                Warranty.init_from_file(set_paths.path_inputs / InputFiles.get_filename('warranty'))
                UsefulLife.init_from_file(set_paths.path_inputs / InputFiles.get_filename('useful_life'))
                self.markups = Markups()
                self.warranty = Warranty()
                self.useful_life = UsefulLife()

        self.row_header_for_fleet_files = ['yearID', 'modelYearID', 'ageID', 'optionID', 'OptionName',
                                           'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName', 'fuelTypeID',
                                           'fuelTypeName',
                                           'DiscountRate',
                                           ]
        self.row_header_for_annual_summary_files = ['yearID', 'optionID', 'OptionName', 'DiscountRate']

        self.elapsed_time_inputs = time() - self.start_time
