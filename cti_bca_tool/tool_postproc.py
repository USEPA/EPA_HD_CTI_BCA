"""
doc_tables.py

Contains the DocTables class.

"""
import pandas as pd

import cti_bca_tool.general_functions as gen_fxns


# lists of args to summarize for document tables
preamble_program_args = ['DirectCost', 'WarrantyCost', 'RnDCost', 'OtherCost', 'ProfitCost', 'TechCost',
                         'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'OperatingCost', 'TechAndOperatingCost']
ria_program_args = ['TechCost', 'OperatingCost', 'TechAndOperatingCost']
tech_args = ['DirectCost', 'WarrantyCost', 'RnDCost', 'OtherCost', 'ProfitCost', 'TechCost']
operating_args = ['EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'OperatingCost']
econ_args = ['TechCost']
bca_cost_args = ['TechAndOperatingCost']

# lists of indexes for summary tables
index_by_alt_by_year = ['DiscountRate', 'optionID', 'OptionName', 'yearID']
index_by_alt = ['DiscountRate', 'optionID', 'OptionName']
index_by_alt_by_ft_by_year = ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID', 'yearID']
index_by_alt_by_ft = ['DiscountRate', 'optionID', 'OptionName', 'fuelTypeID']
index_by_ft_by_alt_by_rc = ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName', 'regClassID']
index_by_ft_by_alt = ['DiscountRate', 'fuelTypeID', 'optionID', 'OptionName']
index_by_year = ['DiscountRate', 'yearID']


def doc_tables_post_process(path_for_save, fleet_totals_df):
    print('\nDoing some post-processing....')
    df = fleet_totals_df.copy()

    preamble_program_table = preamble_ria_tables(df, index_by_alt_by_year, sum, 1000000, 2, *preamble_program_args)
    preamble_program_table_pv = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *preamble_program_args)

    ria_program_table = preamble_ria_tables(df, index_by_alt_by_year, sum, 1000000, 2, *ria_program_args)
    ria_program_table_pv = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *ria_program_args)

    tech_by_alt_by_ft_by_year_table = preamble_ria_tables(df, index_by_alt_by_ft_by_year, sum, 1000000, 2, *tech_args)
    tech_by_alt_by_ft_by_year_table_pv = preamble_ria_tables(df, index_by_alt_by_ft, sum, 1000000, 2, *tech_args)
    tech_by_ft_by_alt_by_rc_table = preamble_ria_tables(df, index_by_ft_by_alt_by_rc, sum, 1000000, 2, *tech_args)
    tech_by_ft_by_alt_table = preamble_ria_tables(df, index_by_ft_by_alt, sum, 1000000, 2, *tech_args)
    tech_by_alt_table = preamble_ria_tables(df, index_by_alt, sum, 1000000, 2, *tech_args)

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

    document_tables_file = pd.ExcelWriter(path_for_save / 'cti_bca_preamble_ria_tables.xlsx')
    for sheet_name in doc_table_dict:
        doc_table_dict[sheet_name].to_excel(document_tables_file, sheet_name=sheet_name)

    return document_tables_file


def figure_tables_post_process(fleet_totals_df):
    df = fleet_totals_df.copy()
    program_table = preamble_ria_tables(df, index_by_alt_by_year, sum, 1, 10, *preamble_program_args)
    return program_table


def preamble_ria_tables(input_df, index_list, function, divisor, sig_dig, *args):
    """

    :param metrics: The list of metrics within the passed DataFrame to include as data in the returned table.
    :param index_list: The list of metrics within the passed DataFrame to include as the row index of the returned table.
    :param function: The function to use (e.g., 'sum', 'mean')
    :return: A pivot table.
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

    :param metrics: The list of metrics within the passed DataFrame to include as data in the returned table.
    :param index_list: The list of metrics within the passed DataFrame to include as the row index of the returned table.
    :param function: The function to use (e.g., 'sum', 'mean')
    :return: A pivot table.
    """
    args = [arg for arg in args]
    print(f'Creating pivot table for {args}')
    table = pd.pivot_table(input_df, args, index_list, columns=cols, aggfunc=function)
    table = table.reset_index(drop=False)
    table.insert(len(table.columns), 'Units', 'USD')
    table.insert(len(table.columns), 'SignificantDigits', 'No rounding')
    return table


def create_output_paths(settings):
    settings.path_outputs.mkdir(exist_ok=True)
    path_of_run_folder = settings.path_outputs / f'{settings.start_time_readable}_CTI_{settings.run_folder_identifier}'
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
