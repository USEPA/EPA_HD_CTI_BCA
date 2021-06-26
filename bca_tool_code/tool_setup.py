
from pathlib import Path
from datetime import datetime
import time
import attr

import bca_tool_code
# from cti_bca_tool.input_output import get_folder
from bca_tool_code import tool_main
import bca_tool_code.general_functions as gen_fxns
from bca_tool_code.get_context_data import GetFuelPrices, GetDeflators
from bca_tool_code.project_dicts import *


@attr.s
class SetInputs:
    """

    The SetInputs class establishes the input files to use and other input settings set in the BCA_Inputs file and needed within the tool.

    """
    # set paths
    path_project = Path.cwd()
    path_code = path_project / 'bca_tool_code'
    path_inputs = path_project / 'inputs'
    # path_inputs = get_folder('folder containing input files for the run')
    path_outputs = path_project / 'outputs'
    path_test = path_project / 'test'

    # create generator of files in path_code
    files_in_path_code = (entry for entry in path_code.iterdir() if entry.is_file())

    # set run id and files to generate
    run_folder_identifier = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
    run_folder_identifier = run_folder_identifier if run_folder_identifier != '' else 'BCA-Tool-Results'

    generate_post_processing_files = True

    start_time = time.time()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    print(f'\nHD BCA tool version: {bca_tool_code.__version__}')
    print(f'\nStart date and time:  {start_time_readable}')

    print("\nReading input files....")
    start_time_read = time.time()
    input_files_df = gen_fxns.read_input_files(path_inputs, 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    input_files_dict = input_files_df.to_dict('index')

    bca_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['bca_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
    regclass_costs = gen_fxns.read_input_files(path_inputs, input_files_dict['regclass_costs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    regclass_learningscalers = gen_fxns.read_input_files(path_inputs, input_files_dict['regclass_learningscalers']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    markups = gen_fxns.read_input_files(path_inputs, input_files_dict['markups']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    warranty_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['warranty_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    usefullife_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['usefullife_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    moves = gen_fxns.read_input_files(path_inputs, input_files_dict['moves']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    moves_adjustments = gen_fxns.read_input_files(path_inputs, input_files_dict['moves_adjustments']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    options = gen_fxns.read_input_files(path_inputs, input_files_dict['options']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
    options_dict = options.to_dict('index')
    def_doserate_inputs = gen_fxns.read_input_files(path_inputs, input_files_dict['def_doserate_inputs']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    def_prices = gen_fxns.read_input_files(path_inputs, input_files_dict['def_prices']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    orvr_fuelchanges = gen_fxns.read_input_files(path_inputs, input_files_dict['orvr_fuelchanges']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x)
    repair_and_maintenance = gen_fxns.read_input_files(path_inputs, input_files_dict['repair_and_maintenance']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)
    unit_conversions = gen_fxns.read_input_files(path_inputs, input_files_dict['unit_conversions']['UserEntry.csv'], usecols=lambda x: 'Notes' not in x, index_col=0)

    fuel_prices_file = gen_fxns.read_input_files(path_inputs, input_files_dict['fuel_prices_file']['UserEntry.csv'], skiprows=4, reset_index=True)
    deflators_file = gen_fxns.read_input_files(path_inputs, input_files_dict['deflators_file']['UserEntry.csv'], skiprows=4, reset_index=True)

    input_files_pathlist = list()
    for item in pd.Series(input_files_df['UserEntry.csv']):
        input_files_pathlist.append(path_inputs / item)
    # input_files_pathlist = [path_inputs / item for item in pd.Series(input_files_df['UserEntry.csv'])] -- cannot get this list comprehension to work with attr
    input_files_pathlist.append(path_inputs / 'Input_Files.csv')

    elapsed_time_read = time.time() - start_time_read

    # set some year data
    moves.insert(moves.columns.get_loc('modelYearID') + 1, 'ageID', moves['yearID'] - moves['modelYearID'])
    year_min = moves.loc[moves['ageID'] == 0, 'yearID'].min() # this will work for both calendar year and model year
    year_max = moves['yearID'].max() # this is the last calendar year included
    model_year_max = moves.loc[moves['ageID'] == 0, 'modelYearID'].max() # calendar years could extend beyond the last model year included
    years = range(year_min, year_max + 1)
    model_years = range(year_min, model_year_max + 1)

    # parse values from the input files
    no_action_alt = pd.to_numeric(bca_inputs.at['no_action_alt', 'UserEntry'])
    aeo_case = bca_inputs.at['aeo_fuel_price_case', 'UserEntry']
    discrate_social_low = pd.to_numeric(bca_inputs.at['discrate_social_low', 'UserEntry'])
    discrate_social_high = pd.to_numeric(bca_inputs.at['discrate_social_high', 'UserEntry'])
    discount_to_yearID = pd.to_numeric(bca_inputs.at['discount_to_yearID', 'UserEntry'])
    costs_start = bca_inputs.at['costs_start', 'UserEntry']
    learning_rate = pd.to_numeric(bca_inputs.at['learning_rate', 'UserEntry'])
    warranty_vmt_share = pd.to_numeric(bca_inputs.at['warranty_vmt_share', 'UserEntry'])
    r_and_d_vmt_share = pd.to_numeric(bca_inputs.at['r_and_d_vmt_share', 'UserEntry'])
    indirect_cost_scaling_metric = bca_inputs.at['scale_indirect_costs_by', 'UserEntry']
    calc_pollution_effects = bca_inputs.at['calculate_pollution_effects', 'UserEntry']
    def_gallons_per_ton_nox_reduction = pd.to_numeric(bca_inputs.at['def_gallons_per_ton_nox_reduction', 'UserEntry'])
    max_age_included = pd.to_numeric(bca_inputs.at['weighted_operating_cost_thru_ageID', 'UserEntry'])
    social_discount_rate_1 = pd.to_numeric(bca_inputs.at['social_discount_rate_1', 'UserEntry'])
    social_discount_rate_2 = pd.to_numeric(bca_inputs.at['social_discount_rate_2', 'UserEntry'])
    criteria_discount_rate_1 = pd.to_numeric(bca_inputs.at['criteria_discount_rate_1', 'UserEntry'])
    criteria_discount_rate_2 = pd.to_numeric(bca_inputs.at['criteria_discount_rate_2', 'UserEntry'])

    grams_per_short_ton = unit_conversions.at['grams_per_short_ton', 'UserEntry']
    gallons_per_ml = unit_conversions.at['gallons_per_ml', 'UserEntry']

    # now adjust some things and get dollar values on a consistent valuation
    if 'Alternative' in moves.columns.tolist():
        moves.rename(columns={'Alternative': 'optionID'}, inplace=True)
    number_alts = len(moves['optionID'].unique())

    # get the fuel price inputs and usd basis for the analysis
    fuel_prices_obj = GetFuelPrices(fuel_prices_file, aeo_case, 'full name', 'Motor Gasoline', 'Diesel')
    print(fuel_prices_obj)
    fuel_prices = fuel_prices_obj.get_prices()
    dollar_basis_analysis = fuel_prices_obj.aeo_dollars()

    # generate a dictionary of gdp deflators, calc adjustment values and apply adjustment values to cost inputs
    deflators_obj = GetDeflators(deflators_file, 'Unnamed: 1', 'Gross domestic product')
    gdp_deflators = deflators_obj.calc_adjustment_factors(dollar_basis_analysis)
    cost_steps = [col for col in regclass_costs.columns if '20' in col]
    gen_fxns.convert_dollars_to_analysis_basis(regclass_costs, gdp_deflators, dollar_basis_analysis, [step for step in cost_steps])
    gen_fxns.convert_dollars_to_analysis_basis(def_prices, gdp_deflators, dollar_basis_analysis, 'DEF_USDperGal')
    gen_fxns.convert_dollars_to_analysis_basis(repair_and_maintenance, gdp_deflators, dollar_basis_analysis, 'Value')

    # create any DataFrames and dictionaries and lists that are useful as part of settings (used throughout project)
    moves_adjustments_dict = create_moves_adjustments_dict(moves_adjustments, 'regClassID', 'fuelTypeID', 'optionID')
    seedvol_factor_dict = create_seedvol_factor_dict(regclass_learningscalers)
    markup_inputs_dict = create_markup_inputs_dict(markups)
    markup_factors = [arg for arg in markups['Markup_Factor'].unique()]
    required_miles_and_ages_dict = create_required_miles_and_ages_dict(warranty_inputs, 'Warranty', usefullife_inputs, 'Usefullife')
    def_doserate_inputs_dict = create_def_doserate_inputs_dict(def_doserate_inputs)
    def_prices_dict = create_def_prices_dict(def_prices)
    orvr_inputs_dict = create_orvr_inputs_dict(orvr_fuelchanges)
    fuel_prices_dict = create_fuel_prices_dict(fuel_prices)
    repair_inputs_dict = repair_and_maintenance.to_dict('index')

    # read criteria cost factors if needed
    if calc_pollution_effects == 'Y':
        criteria_cost_factors = gen_fxns.read_input_files(path_inputs, input_files_dict['criteria_emission_costs']['UserEntry.csv'], lambda x: 'Notes' not in x)
        criteria_cost_factors_dict = create_criteria_cost_factors_dict(criteria_cost_factors)

    # create a row header list for the structure of the main output files
    row_header_for_fleet_files = ['vehicle', 'yearID', 'modelYearID', 'ageID', 'optionID', 'OptionName',
                                  'sourceTypeID', 'sourceTypeName', 'regClassID', 'regClassName', 'fuelTypeID', 'fuelTypeName',
                                  'DiscountRate',
                                   ]


if __name__ == '__main__':
    settings = SetInputs()
    tool_main.main(settings)
