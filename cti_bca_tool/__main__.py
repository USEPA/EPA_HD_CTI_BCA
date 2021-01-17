import cti_bca_tool
from cti_bca_tool import cti_bca
import cti_bca_tool.general_functions as gen_fxns
from pathlib import Path
from datetime import datetime
import pandas as pd
import time
import attr

from cti_bca_tool.get_context_data import GetFuelPrices, GetDeflators
from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
from project_dicts import *


@attr.s
class SetInputs:
    """
    The SetInputs class establishes the input files to use and other input settings set in the BCA_Inputs file and needed within the tool.
    """
    # set paths
    path_code = Path(__file__).parent
    path_project = Path(path_code).parent
    path_inputs = path_project / 'inputs'
    path_context = path_project / 'context_inputs'
    path_outputs = path_project / 'outputs'

    # create generator of files in path_code
    files_in_path_code = (entry for entry in path_code.iterdir() if entry.is_file())

    # set run id and files to generate
    run_folder_identifier = input('Provide a run identifier for your output folder name (press return to use the default name)\n')
    run_folder_identifier = run_folder_identifier if run_folder_identifier != '' else 'BCA-Results'
    create_all_files = input('Create and save the large "all_calcs" file? (y)es or (n)o?\n')

    start_time = time.time()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    print(f'\nCTI BCA tool version: {cti_bca_tool.__version__}')
    print(f'\nStart date and time:  {start_time_readable}')

    print("\nReading input files....")
    start_time_read = time.time()
    input_files_df = gen_fxns.read_input_files(path_inputs, 'Input_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    input_files_dict = input_files_df.to_dict('index')
    context_files_df = gen_fxns.read_input_files(path_inputs, 'Context_Files.csv', usecols=lambda x: 'Notes' not in x, index_col=0)
    context_files_dict = context_files_df.to_dict('index')

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

    fuel_prices_file = gen_fxns.read_input_files(path_context, context_files_dict['fuel_prices_file']['UserEntry.csv'], skiprows=4, reset_index=True)
    deflators_file = gen_fxns.read_input_files(path_context, context_files_dict['deflators_file']['UserEntry.csv'], skiprows=4, reset_index=True)

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
    weighted_operating_cost_years = bca_inputs.at['weighted_operating_cost_years', 'UserEntry']
    weighted_operating_cost_years = weighted_operating_cost_years.split(',')
    for i, v in enumerate(weighted_operating_cost_years):
        weighted_operating_cost_years[i] = pd.to_numeric(weighted_operating_cost_years[i])
    max_age_included = pd.to_numeric(bca_inputs.at['weighted_operating_cost_thru_ageID', 'UserEntry'])
    techcost_summary_years = bca_inputs.at['techcost_summary_years', 'UserEntry']
    techcost_summary_years = techcost_summary_years.split(',')
    for i, v in enumerate(techcost_summary_years):
        techcost_summary_years[i] = pd.to_numeric(techcost_summary_years[i])
    bca_summary_years = bca_inputs.at['bca_summary_years', 'UserEntry']
    bca_summary_years = bca_summary_years.split(',')
    for i, v in enumerate(bca_summary_years):
        bca_summary_years[i] = pd.to_numeric(bca_summary_years[i])
    generate_emissionrepair_cpm_figures = bca_inputs.at['generate_emissionrepair_cpm_figures', 'UserEntry']
    generate_BCA_ArgsByOption_figures = bca_inputs.at['generate_BCA_ArgsByOption_figures', 'UserEntry']
    generate_BCA_ArgByOptions_figures = bca_inputs.at['generate_BCA_ArgByOptions_figures', 'UserEntry']

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
    print(deflators_obj)
    gdp_deflators = deflators_obj.calc_adjustment_factors(dollar_basis_analysis)
    cost_steps = [col for col in regclass_costs.columns if '20' in col]
    gen_fxns.convert_dollars_to_analysis_basis(regclass_costs, gdp_deflators, dollar_basis_analysis, [step for step in cost_steps])
    gen_fxns.convert_dollars_to_analysis_basis(def_prices, gdp_deflators, dollar_basis_analysis, 'DEF_USDperGal')
    gen_fxns.convert_dollars_to_analysis_basis(repair_and_maintenance, gdp_deflators, dollar_basis_analysis, 'Value')

    # create any DataFrames and dictionaries and lists that are useful as part of settings (used throughout project)
    moves_adjustments_dict = create_moves_adjustments_dict(moves_adjustments, 'optionID', 'regClassID', 'fuelTypeID')
    seedvol_factor_dict = create_seedvol_factor_dict(regclass_learningscalers)
    markup_inputs_dict = create_markup_inputs_dict(markups)
    markup_factors = [arg for arg in markups['Markup_Factor'].unique()]
    def_doserate_inputs_dict = create_def_doserate_inputs_dict(def_doserate_inputs)
    def_prices_dict = create_def_prices_dict(def_prices)
    # project_fleet_df = create_fleet_df(moves, moves_adjustments_dict)
    # vehicles_rc = regclass_vehicles(project_fleet_df)
    # vehicles_st = sourcetype_vehicles(project_fleet_df)
    # regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    # fleet_dict = create_fleet_totals_dict(project_fleet_df)


if __name__ == '__main__':
    settings = SetInputs()
    cti_bca.new_main(settings)
    cti_bca.main(settings)
