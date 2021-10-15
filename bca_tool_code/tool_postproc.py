"""
cti_bca_tool.tool_postproc.py

This is the post-processing module of the tool. The run_postproc function is called by tool_main.main().

"""
import pandas as pd

import bca_tool_code.general_functions as gen_fxns
from bca_tool_code.discounting import annualize_values
from bca_tool_code.figures import create_figures


# lists of args to summarize for document tables
preamble_cap_program_args = ['DirectCost', 'WarrantyCost', 'RnDCost', 'OtherCost', 'ProfitCost', 'TechCost',
                             'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'OperatingCost', 'TechAndOperatingCost']
preamble_ghg_program_args = ['TechCost', 'FuelCost_Pretax', 'OperatingCost', 'TechAndOperatingCost']
ria_program_args = ['TechCost', 'OperatingCost', 'TechAndOperatingCost']
tech_args_cap = ['DirectCost', 'WarrantyCost', 'RnDCost', 'OtherCost', 'ProfitCost', 'TechCost']
tech_args_ghg = ['TechCost']
operating_args_cap = ['EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'OperatingCost']
operating_args_ghg = ['FuelCost_Pretax', 'OperatingCost']
econ_args = ['TechCost']
bca_cost_args = ['TechAndOperatingCost']

# lists of indexes for summary tables
index_by_alt_by_year = ['DiscountRate', 'optionID', 'OptionName', 'yearID']
index_by_alt = ['DiscountRate', 'optionID', 'OptionName']
index_by_alt_by_ft_by_year = ['DiscountRate', 'optionID', 'fuelTypeID', 'OptionName', 'fuelTypeName', 'yearID']
index_by_alt_by_ft = ['DiscountRate', 'optionID', 'fuelTypeID', 'OptionName', 'fuelTypeName']
index_by_ft_by_alt_by_rc = ['DiscountRate', 'fuelTypeID', 'optionID', 'regClassID', 'OptionName', 'regClassName', 'fuelTypeName']
index_by_ft_by_alt = ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'fuelTypeName']
index_by_year = ['DiscountRate', 'yearID']


def run_postproc(settings, path_save, totals_dict, program):
    """

    Parameters::
        settings: The SetInputs class.\n
        path_save: The path to which to save output files.\n
        totals_dict: A dictionary containing the annual totals to be post-processed.
        program: The program identifier string (i.e., 'CAP' or 'GHG') to include in the saved filename.

    Returns:
        A postproc_file that provides annual results and annualized monetized results. This function also calls the function to generate document tables
        for copy/paste into documents.

    """
    print('\nDoing some post-processing....')
    # Convert dictionary to DataFrame to generate summaries via pandas.
    totals_df = gen_fxns.convert_dict_to_df(totals_dict, 'vehicle', 'optionID', 'modelYearID', 'ageID', 'DiscountRate')

    annual_df = create_annual_summary_df(totals_df)
    annual_df = annualize_values(settings, annual_df)

    postproc_file = doc_tables_post_process(settings, path_save, totals_df, program)
    annual_df.to_excel(postproc_file, sheet_name='annualized', index=False)

    if program == 'CAP': arg_list = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
    else: arg_list = ['TechCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
    create_figures(annual_df, 'US Dollars', path_save, program, arg_list)

    return postproc_file, totals_df


def doc_tables_post_process(settings, path_for_save, fleet_totals_df, program):
    """

    Parameters::
        path_for_save: The path to which to save output files.\n
        fleet_totals_df: A DataFrame containing the data to be used in generating pivot tables for use in documents.
        program: The program identifier string (i.e., 'CAP' or 'GHG') to include in the saved filename.

    Returns:
        An Excel writer object containing several individual worksheets that are pivot tables of the fleet_totals_df DataFrame.

    """
    df = fleet_totals_df.copy()

    if program == 'CAP': preamble_program_args = preamble_cap_program_args
    else: preamble_program_args = preamble_ghg_program_args
    preamble_program_table = preamble_ria_tables(df, index_by_alt_by_year, sum, 1000000, 2, *preamble_program_args)
    preamble_program_table_pv = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *preamble_program_args)

    ria_program_table = preamble_ria_tables(df, index_by_alt_by_year, sum, 1000000, 2, *ria_program_args)
    ria_program_table_pv = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *ria_program_args)

    if program == 'CAP': tech_args = tech_args_cap
    else: tech_args = tech_args_ghg
    tech_by_alt_by_ft_by_year_table = preamble_ria_tables(df, index_by_alt_by_ft_by_year, sum, 1000000, 2, *tech_args)
    tech_by_alt_by_ft_by_year_table_pv = preamble_ria_tables(df, index_by_alt_by_ft, sum, 1000000, 2, *tech_args)
    tech_by_ft_by_alt_by_rc_table = preamble_ria_tables(df, index_by_ft_by_alt_by_rc, sum, 1000000, 2, *tech_args)
    tech_by_ft_by_alt_table = preamble_ria_tables(df, index_by_ft_by_alt, sum, 1000000, 2, *tech_args)
    tech_by_alt_table = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *tech_args)

    if program == 'CAP': operating_args = operating_args_cap
    else: operating_args = operating_args_ghg
    operating_by_alt_by_ft_by_year_table = preamble_ria_tables(df, index_by_alt_by_ft_by_year, sum, 1000000, 2, *operating_args)
    operating_by_alt_by_ft_by_year_table_pv = preamble_ria_tables(df, index_by_alt_by_ft, sum, 1000000, 2, *operating_args)
    operating_by_ft_by_alt_by_rc_table = preamble_ria_tables(df, index_by_ft_by_alt_by_rc, sum, 1000000, 2, *operating_args)
    operating_by_ft_by_alt_table = preamble_ria_tables(df, index_by_ft_by_alt, sum, 1000000, 2, *operating_args)
    operating_by_alt_table = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *operating_args)

    econ_table = bca_tables(df, index_by_year, ['optionID', 'OptionName'], sum, *econ_args)
    bca_cost_table = bca_tables(df, index_by_year, ['optionID', 'OptionName'], sum, *bca_cost_args)
    bca_cost_table_pv = bca_tables(df, ['DiscountRate'], ['optionID', 'OptionName'], sum, *bca_cost_args)

    doc_table_dict = {'program': preamble_program_table,
                      'program_pv': preamble_program_table_pv,
                      'ria_program': ria_program_table,
                      'ria_program_pv': ria_program_table_pv,
                      'tech': tech_by_alt_by_ft_by_year_table,
                      'tech_pv': tech_by_alt_by_ft_by_year_table_pv,
                      'tech_byRC': tech_by_ft_by_alt_by_rc_table,
                      'tech_byFT': tech_by_ft_by_alt_table,
                      'tech_byOption': tech_by_alt_table,
                      'operating': operating_by_alt_by_ft_by_year_table,
                      'operating_pv': operating_by_alt_by_ft_by_year_table_pv,
                      'operating_byRC': operating_by_ft_by_alt_by_rc_table,
                      'operating_byFT': operating_by_ft_by_alt_table,
                      'operating_byOption': operating_by_alt_table,
                      'econ': econ_table,
                      'bca_cost': bca_cost_table,
                      'bca_cost_pv': bca_cost_table_pv,
                      }

    document_tables_file = pd.ExcelWriter(path_for_save / f'{program}_bca_tool_preamble_ria_tables_{settings.start_time_readable}.xlsx')
    for sheet_name in doc_table_dict:
        doc_table_dict[sheet_name].to_excel(document_tables_file, sheet_name=sheet_name)

    return document_tables_file


def add_vehicle_identifiers_to_df(df):
    """

    Args:
        df: A DataFrame having a "vehicle" column of tuples representing an alt, st, rc, ft vehicle.

    Returns:
        The passed DataFrame with four new columns representing the 4 elements of each vehicle tuple.

    """
    alt_list, st_list, rc_list, ft_list = list(), list(), list(), list()
    for veh in df['vehicle']:
        alt, st, rc, ft = veh[0], veh[1], veh[2], veh[3]
        alt_list.append(alt)
        st_list.append(st)
        rc_list.append(rc)
        ft_list.append(ft)
    df.insert(0, 'fuelTypeID', ft_list)
    df.insert(0, 'regClassID', rc_list)
    df.insert(0, 'sourceTypeID', st_list)
    df.insert(0, 'optionID', alt_list)
    return df


def preamble_ria_tables(input_df, index_list, function, divisor, sig_dig, *args):
    """

    Parameters::
        input_df: A DataFrame containing the data to be used for the pivot table.\n
        index_list: The parameters to use as the pivot table row index.\n
        function: The function to be used in generating the pivot table results.\n
        divisor: A divisor to use to express results other than dollars.\n
        sig_dig: The number of significant digits to use (this is not a rounder but a true significant digit determinant).\n
        args: The parameters to include in the pivot table results.

    Returns:
        A pivot table of args by index_list summarized by the function and expressed in divisor terms to sig_dig significant digits.

    """
    args = [arg for arg in args]
    print(f'Creating pivot table for {args}')
    table = pd.pivot_table(input_df, args, index_list, aggfunc=function)
    table = table.reindex(args, axis=1)
    table = table.reset_index(drop=False)
    table = gen_fxns.round_sig(table, divisor, sig_dig, *args)
    units_dict = {1: '', 100: 'Hundred', 1000: 'Thousand', 1000000: 'Million', 1000000000: 'Billion'}
    unit = units_dict[divisor]
    table.insert(len(table.columns), 'Units', f'{unit} USD')
    table.insert(len(table.columns), 'SignificantDigits', f'{sig_dig} significant digits')
    return table


def bca_tables(input_df, index_list, cols, function, *args):
    """

    Parameters::
        input_df: A DataFrame containing the data to be used for the pivot table.\n
        index_list: The parameters to use as the pivot table row index.\n
        cols: The columns to use as column headers.\n
        function: The function to be used in generating the pivot table results.\n
        args: The parameters to include in the pivot table results.\n

    Returns:
        A pivot table of args by index_list summarized by the function with col column headers.

    """
    args = [arg for arg in args]
    print(f'Creating pivot table for {args}')
    table = pd.pivot_table(input_df, args, index_list, columns=cols, aggfunc=function)
    table = table.reset_index(drop=False)
    table.insert(len(table.columns), 'Units', 'USD')
    table.insert(len(table.columns), 'SignificantDigits', 'No rounding')
    return table


def create_annual_summary_df(totals_df):
    """

    Parameters::
        totals_df: A DataFrame of monetized values by option name, yearID and DiscountRate; OptionName should exist for figures (as legend entries).

    Returns:
        A DataFrame that summarizes the passed DataFrame by yearID.

    """
    # Create a list of args to groupby and args to group; args should be passed, not hardcoded - lots of this has too much hardcoding making it inflexible
    args_to_groupby = ['optionID', 'OptionName', 'yearID', 'DiscountRate']
    # now create a 'yearID' col since it may not be part of the key that was used to generate the passed totals_df
    if 'yearID' not in totals_df.columns.tolist():
        totals_df.insert(totals_df.columns.get_loc('modelYearID') + 1, 'yearID', totals_df[['modelYearID', 'ageID']].sum(axis=1))
    cost_args = [col for col in totals_df if 'Cost' in col]
    args = args_to_groupby + cost_args

    df = pd.DataFrame(totals_df, columns=args)

    # First sum by args_to_groupby to get annual summaries.
    df_sum = df.groupby(by=args_to_groupby, as_index=False).sum()

    # Now do a cumulative sum of the annual values. Since they are discounted values, the cumulative sum will represent a running present value.
    df_pv = df_sum.groupby(by=['optionID', 'OptionName', 'DiscountRate'], as_index=False).cumsum()
    df_pv.drop(columns='yearID', inplace=True)

    # Rename the args in df_pv to include a present value notation
    for cost_arg in cost_args:
        df_pv.rename(columns={cost_arg: f'{cost_arg}_PresentValue'}, inplace=True)

    # Bring the present values into the annual values
    df = pd.concat([df_sum, df_pv], axis=1, ignore_index=False)

    return df


def create_output_paths(settings):
    """

    Parameters::
        settings: The SetInputs class.

    Returns:
        Output paths into which to save outputs of the given run.

    """
    settings.path_outputs.mkdir(exist_ok=True)
    path_of_run_folder = settings.path_outputs / f'{settings.start_time_readable}_{settings.run_folder_identifier}'
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
