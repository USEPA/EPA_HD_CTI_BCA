import project_code
from project_code import cti_bca
import project_code.general_functions as gen_fxns
from pathlib import Path
from datetime import datetime
import pandas as pd
import time


if __name__ == '__main__':


    class SetInputs:
        def __init__(self):
            self.path_project = Path.cwd()  # the 'Working directory'
            # TODO base discount rate low/high on criteria inputs since can't mix and match rates anyway?
            # TODO update introduction/other documentation per recent changes (0.22.0 thru 0.24.X)
            # TODO check general_functions module and later for docstrings in documentation build
            self.path_inputs = self.path_project / 'inputs'
            self.path_outputs = self.path_project / 'outputs'
            self.run_folder_identifier = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
            self.run_folder_identifier = self.run_folder_identifier if self.run_folder_identifier != '' else 'BCA-Results'
            self.create_all_files = input('Create and save the large "all_calcs" file? (y)es or (n)o?\n')
            self.start_time = time.time()
            self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
            print(f'\nCTI BCA tool version: {project_code.__version__}')
            print(f'\nStart date and time:  {self.start_time_readable}')

            print("\nReading input files....")
            self.start_time_read = time.time()
            self.input_files_df = pd.read_csv(self.path_inputs / 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
            self.input_files_dict = self.input_files_df.to_dict('index')

            self.bca_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['bca_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)
            self.regclass_costs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['regclass_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.regclass_learningscalers = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['regclass_learningscalers']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.markups = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['markups']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.warranty_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['warranty_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.usefullife_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['usefullife_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.moves = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['moves']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.moves_adjustments = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['moves_adjustments']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.options = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['options']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)
            self.options_dict = self.options.to_dict('index')
            self.def_doserate_inputs = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['def_doserate_inputs']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.def_prices = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['def_prices']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.orvr_fuelchanges = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['orvr_fuelchanges']['UserEntry.csv'], lambda x: 'Notes' not in x)
            self.repair_and_maintenance = gen_fxns.read_input_files(self.path_inputs, self.input_files_dict['repair_and_maintenance']['UserEntry.csv'], lambda x: 'Notes' not in x, 0)

            self.input_files_pathlist = [self.path_inputs / item for item in pd.Series(self.input_files_df['UserEntry.csv'])]
            self.input_files_pathlist.append(self.path_inputs / 'Input_Files.csv')

            self.elapsed_time_read = time.time() - self.start_time_read

            self.aeo_case = self.bca_inputs.at['aeo_fuel_price_case', 'UserEntry']
            self.discrate_social_low = pd.to_numeric(self.bca_inputs.at['discrate_social_low', 'UserEntry'])
            self.discrate_social_high = pd.to_numeric(self.bca_inputs.at['discrate_social_high', 'UserEntry'])
            self.discount_to_yearID = pd.to_numeric(self.bca_inputs.at['discount_to_yearID', 'UserEntry'])
            self.costs_start = self.bca_inputs.at['costs_start', 'UserEntry']
            self.learning_rate = pd.to_numeric(self.bca_inputs.at['learning_rate', 'UserEntry'])
            self.warranty_vmt_share = pd.to_numeric(self.bca_inputs.at['warranty_vmt_share', 'UserEntry'])
            self.r_and_d_vmt_share = pd.to_numeric(self.bca_inputs.at['r_and_d_vmt_share', 'UserEntry'])
            self.indirect_cost_scaling_metric = self.bca_inputs.at['scale_indirect_costs_by', 'UserEntry']
            self.calc_pollution_effects = self.bca_inputs.at['calculate_pollution_effects', 'UserEntry']
            self.def_gallons_perTonNOxReduction = pd.to_numeric(self.bca_inputs.at['def_gallons_per_ton_nox_reduction', 'UserEntry'])
            self.weighted_operating_cost_years = self.bca_inputs.at['weighted_operating_cost_years', 'UserEntry']
            self.weighted_operating_cost_years = self.weighted_operating_cost_years.split(',')
            for i, v in enumerate(self.weighted_operating_cost_years):
                self.weighted_operating_cost_years[i] = pd.to_numeric(self.weighted_operating_cost_years[i])
            self.max_age_included = pd.to_numeric(self.bca_inputs.at['weighted_operating_cost_thru_ageID', 'UserEntry'])
            self.techcost_summary_years = self.bca_inputs.at['techcost_summary_years', 'UserEntry']
            self.techcost_summary_years = self.techcost_summary_years.split(',')
            for i, v in enumerate(self.techcost_summary_years):
                self.techcost_summary_years[i] = pd.to_numeric(self.techcost_summary_years[i])
            self.bca_summary_years = self.bca_inputs.at['bca_summary_years', 'UserEntry']
            self.bca_summary_years = self.bca_summary_years.split(',')
            for i, v in enumerate(self.bca_summary_years):
                self.bca_summary_years[i] = pd.to_numeric(self.bca_summary_years[i])
            self.generate_emissionrepair_cpm_figures = self.bca_inputs.at['generate_emissionrepair_cpm_figures', 'UserEntry']
            self.generate_BCA_ArgsByOption_figures = self.bca_inputs.at['generate_BCA_ArgsByOption_figures', 'UserEntry']
            self.generate_BCA_ArgByOptions_figures = self.bca_inputs.at['generate_BCA_ArgByOptions_figures', 'UserEntry']

    bca_tool = SetInputs()
    cti_bca.main(bca_tool)
