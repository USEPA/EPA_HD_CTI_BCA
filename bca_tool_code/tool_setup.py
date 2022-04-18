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
from bca_tool_code.general_input_modules.options import Options
from bca_tool_code.general_input_modules.moves_adjustments import MovesAdj

from bca_tool_code.fleet import Fleet
from bca_tool_code.annual_summary import AnnualSummary

from bca_tool_code.cap_input_modules.regclass_costs import RegclassCosts
from bca_tool_code.cap_input_modules.regclass_learning_scalers import RegclassLearningScalers
from bca_tool_code.cap_input_modules.def_doserates import DefDoseRates
from bca_tool_code.cap_input_modules.orvr_fuelchanges import OrvrFuelChanges
from bca_tool_code.cap_input_modules.repair_and_maintenance import RepairAndMaintenance
from bca_tool_code.cap_modules.regclass_sales import RegClassSales

from bca_tool_code.ghg_input_modules.sourcetype_costs import SourceTypeCosts
from bca_tool_code.ghg_input_modules.sourcetype_learning_scalers import SourceTypeLearningScalers
from bca_tool_code.ghg_modules.sourcetype_sales import SourceTypeSales


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

    @staticmethod
    def run_id():
        """

        This method allows for a user-interactive identifier (name) for the given run.

        Returns:
            A console prompt to enter a run identifier; entering "test" sends outputs to a test folder; if left blank a
            default name is used.

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

        The SetInputs class establishes the input files to use and other input settings set in the BCA_Inputs file and
        needed within the tool.

        """
        set_paths = SetPaths()
        self.start_time = time()
        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

        self.input_files = InputFiles()
        self.input_files.init_from_file(set_paths.path_inputs / 'Input_Files.csv')

        self.general_inputs = GeneralInputs()
        self.general_inputs.init_from_file(set_paths.path_inputs / self.input_files.get_filename('bca_inputs'))

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

        self.input_files_pathlist = self.input_files.input_files_pathlist
        
        self.deflators = Deflators()
        self.deflators.init_from_file(set_paths.path_inputs / self.input_files.get_filename('deflators'),
                                      self.general_inputs)
        
        self.fuel_prices = FuelPrices()
        self.fuel_prices.init_from_file(set_paths.path_inputs / self.input_files.get_filename('fuel_prices'),
                                        self.general_inputs, self.deflators)
        
        self.def_prices = DefPrices()
        self.def_prices.init_from_file(set_paths.path_inputs / self.input_files.get_filename('def_prices'),
                                       self.general_inputs, self.deflators)

        if self.calc_cap_costs:
            self.options_cap = Options()
            self.options_cap.init_from_file(set_paths.path_inputs / self.input_files.get_filename('options_cap'))

            self.moves_adj_cap = MovesAdj()
            self.moves_adj_cap.init_from_file(set_paths.path_inputs / self.input_files.get_filename('moves_adjustments_cap'))

            self.fleet_cap = Fleet()
            self.fleet_cap.init_from_file(set_paths.path_inputs / self.input_files.get_filename('fleet_cap'),
                                          self.general_inputs, 'CAP', self.options_cap, self.moves_adj_cap)

            self.regclass_costs = RegclassCosts()
            self.regclass_costs.init_from_file(set_paths.path_inputs / self.input_files.get_filename('regclass_costs'),
                                               self.general_inputs, self.deflators)
            
            self.regclass_learning_scalers = RegclassLearningScalers()
            self.regclass_learning_scalers.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('regclass_learning_scalers'))

            self.markups = Markups()
            self.markups.init_from_file(set_paths.path_inputs / self.input_files.get_filename('markups'))
            
            self.warranty = Warranty()
            self.warranty.init_from_file(set_paths.path_inputs / self.input_files.get_filename('warranty'))
            
            self.useful_life = UsefulLife()
            self.useful_life.init_from_file(set_paths.path_inputs / self.input_files.get_filename('useful_life'))

            self.def_doserates = DefDoseRates()
            self.def_doserates.init_from_file(set_paths.path_inputs / self.input_files.get_filename('def_doserates'))

            self.orvr_fuelchanges_cap = OrvrFuelChanges()
            self.orvr_fuelchanges_cap.init_from_file(set_paths.path_inputs / self.input_files.get_filename('orvr_fuelchanges_cap'))

            self.repair_and_maintenance = RepairAndMaintenance()
            self.repair_and_maintenance.init_from_file(set_paths.path_inputs / self.input_files.get_filename('repair_and_maintenance'),
                                                       self.general_inputs, self.deflators)

            # create additional and useful dicts and DataFrames
            self.regclass_sales = RegClassSales()
            self.regclass_sales.create_regclass_sales_dict(self.fleet_cap.fleet_df, self.regclass_costs.cost_steps)

            self.repair_cpm_dict = dict()
            self.estimated_ages_dict = dict()
            self.wtd_def_cpm_dict = dict()
            self.wtd_repair_cpm_dict = dict()
            self.wtd_cap_fuel_cpm_dict = dict()
            self.annual_summary_cap = AnnualSummary()

        if self.calc_cap_pollution:
            self.dollar_per_ton_cap = DollarPerTonCAP()
            self.dollar_per_ton_cap.init_from_file(set_paths.path_inputs / self.input_files.get_filename('dollar_per_ton_cap'))

        if self.calc_ghg_costs:

            self.options_ghg = Options()
            self.options_ghg.init_from_file(set_paths.path_inputs / self.input_files.get_filename('options_ghg'))

            self.moves_adj_ghg = MovesAdj()
            self.moves_adj_ghg.init_from_file(set_paths.path_inputs / self.input_files.get_filename('moves_adjustments_ghg'))

            self.fleet_ghg = Fleet()
            self.fleet_ghg.init_from_file(set_paths.path_inputs / self.input_files.get_filename('fleet_ghg'),
                                          self.general_inputs, 'GHG', self.options_ghg, self.moves_adj_ghg)

            self.sourcetype_costs = SourceTypeCosts()
            self.sourcetype_costs.init_from_file(set_paths.path_inputs / self.input_files.get_filename('sourcetype_costs'),
                                                 self.general_inputs, self.deflators)

            self.sourcetype_learning_scalers = SourceTypeLearningScalers()
            self.sourcetype_learning_scalers.init_from_file(set_paths.path_inputs / self.input_files.get_filename('sourcetype_learning_scalers'))

            # create additional and useful dicts and DataFrames
            self.sourcetype_sales = SourceTypeSales()
            self.sourcetype_sales.create_sourcetype_sales_dict(self.fleet_ghg.fleet_df, self.sourcetype_costs.cost_steps)

            self.wtd_ghg_fuel_cpm_dict = dict()
            self.annual_summary_ghg = AnnualSummary()

            if self.calc_cap_costs:
                pass
            else:
                self.markups = Markups()
                self.markups.init_from_file(set_paths.path_inputs / self.input_files.get_filename('markups'))

                self.warranty = Warranty()
                self.warranty.init_from_file(set_paths.path_inputs / self.input_files.get_filename('warranty'))

                self.useful_life = UsefulLife()
                self.useful_life.init_from_file(set_paths.path_inputs / self.input_files.get_filename('useful_life'))

        self.row_header_for_fleet_files = ['yearID', 'modelYearID', 'ageID', 'optionID', 'OptionName',
                                           'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName', 'fuelTypeID',
                                           'fuelTypeName',
                                           'DiscountRate',
                                           ]
        self.row_header_for_annual_summary_files = ['yearID', 'optionID', 'OptionName', 'DiscountRate']

        self.end_time_inputs = time()
        self.elapsed_time_inputs = self.end_time_inputs - self.start_time
