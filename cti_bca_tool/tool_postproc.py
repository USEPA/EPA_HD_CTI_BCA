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
    tech_by_alt_by_ft_by_year_table_pv = preamble_ria_tables(df, index_by_alt_by_ft, sum, 1000000, 2 *tech_args)
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

    return document_tables_file, preamble_program_table


def preamble_ria_tables(input_df, index_list, function, divisor, sig_dig, *args):
    """

    :param metrics: The list of metrics within the passed DataFrame to include as data in the returned table.
    :param index_list: The list of metrics within the passed DataFrame to include as the row index of the returned table.
    :param function: The function to use (e.g., 'sum', 'mean')
    :return: A pivot table.
    """
    args = [arg for arg in args]
    table = pd.pivot_table(input_df, args, index_list, aggfunc=function)
    table = table.reindex(args, axis=1)
    table = table.reset_index(drop=False)
    table = gen_fxns.round_sig(table, divisor, sig_dig, *args)
    table.insert(len(table.columns), 'Units_SignificantDigits', f'Millions of USD; {sig_dig} sig digits')
    return table


def bca_tables(input_df, index_list, cols, function, *args):
    """

    :param metrics: The list of metrics within the passed DataFrame to include as data in the returned table.
    :param index_list: The list of metrics within the passed DataFrame to include as the row index of the returned table.
    :param function: The function to use (e.g., 'sum', 'mean')
    :return: A pivot table.
    """
    args = [arg for arg in args]
    table = pd.pivot_table(input_df, args, index_list, columns=cols, aggfunc=function)
    table = table.reset_index(drop=False)
    table.insert(len(table.columns), 'Units_SignificantDigits', f'USD; No rounding')
    return table


def create_output_paths(settings):
    settings.path_outputs.mkdir(exist_ok=True)
    # if settings.run_folder_identifier == 'test':
    #     path_of_run_results_folder = settings.path_test
    #     path_of_run_results_folder.mkdir(exist_ok=True)
    #     return path_of_run_results_folder
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


# class DocTables:
#     """
#     The DocTables class generates Excel files that contain simple tables meant for copy/paste into documents. These tables are high-level summary tables only.
#
#     :param input_df: The source of data to be used to generate the summary table(s).
#     :type input_df: DataFrame
#     """
#
#     def __init__(self, input_df):
#         self.input_df = input_df
#
#     def techcost_per_veh_table(self, discount_rates, years, regclasses, fueltypes, df_cols, writer):
#         """
#
#         :param discount_rates: A list of discount rates for which tables are to be generated.
#         :param years: A list of model years for which tables are to be generated.
#         :param regclasses: A list of RegClasses for which tables are to be generated.
#         :param fueltypes: A list of FuelTypes for which tables are to be generated.
#         :param df_cols: A list of column headers (column index values) to use.
#         :param writer: The Excel Writer object into which to place the summary tables.
#         :return: An Excel Writer object containing the summary tables.
#         """
#         for dr in discount_rates:
#             for fueltype in fueltypes:
#                 for regclass in regclasses:
#                     for yr in years:
#                         data = pd.DataFrame(self.input_df.loc[(self.input_df['DiscountRate'] == dr)
#                                                               & (self.input_df['yearID'] == yr)
#                                                               & (self.input_df['regclass'] == regclass)
#                                                               & (self.input_df['fueltype'] == fueltype)],
#                                             columns=df_cols)
#                         cols_to_round = [col for col in data.columns if 'AvgPerVeh' in col]
#                         for col in cols_to_round:
#                             data[col] = data[col].round(0)
#                         sh_name = f'{dr}DR_MY{yr}_{regclass}_{fueltype}'
#                         data.to_excel(writer, sheet_name=sh_name, index=False)
#         return writer
#
#     def bca_yearID_tables(self, suffix, discrate, years, units, df_cols, writer, low_series='', high_series=''):
#         """
#
#         :param suffix: The metric suffix to use: '' for annual values; '_CumSum' for NPVs; '_Annualized' for annualized values.
#         :param discrate: The discount rate to use.
#         :param low_series: The low mortality estimate series to use.
#         :param high_series: The high mortality estimate series to use.
#         :param years: The years to summarize. For NPVs and annualized values, the years through which to summarize.
#         :param units: The units of table values: 'dollars'; 'thousands'; 'millions'; 'billions'
#         :param df_cols: The primary column headers (column index values) to use.
#         :param writer: The Excel Writer object into which to place the summary tables.
#         :return: An Excel Writer object containing the summary tables.
#         """
#         units_df = pd.DataFrame({'units': ['dollars', 'thousands', 'millions', 'billions'], 'divisor': [1, 1e3, 1e6, 1e9]})
#         units_df.set_index('units', inplace=True)
#         divisor = units_df.at[units, 'divisor']
#         for yr in years:
#             data = pd.DataFrame(self.input_df.loc[(self.input_df['DiscountRate'] == discrate)
#                                                   & (self.input_df['yearID'] == yr)],
#                                 columns=['OptionName', 'DiscountRate']
#                                         + [item + suffix for item in df_cols if 'OptionName' not in item and 'DiscountRate' not in item]
#                                         + [low_series + suffix, high_series + suffix])
#             cols_new_units = [col for col in data.columns if 'OptionName' not in col and 'DiscountRate' not in col]
#             for col in cols_new_units:
#                 data[col] = (data[col] / divisor).round(1)
#             data.loc[len(data.index), 'OptionName'] = f'Table values are in {units}'
#             sh_name = f'CY{yr}_DR{discrate}'
#             data.to_excel(writer, sheet_name=sh_name, index=False)
#         return writer
#
#     def inventory_tables1(self, years, df_cols, writer):
#         """
#
#         :param years: The years to summarize.
#         :param df_cols: The primary column headers (column index values) to use.
#         :param writer: The Excel Writer object into which to place the summary tables.
#         :return: An Excel Writer object containing the summary tables.
#         """
#         for yr in years:
#             data = pd.DataFrame(self.input_df.loc[(self.input_df['DiscountRate'] == 0)
#                                                   & (self.input_df['yearID'] == yr)],
#                                 columns=df_cols)
#             data = data.round({'PM25_onroad': -1, 'NOx_onroad': -3})
#             data.loc[len(data.index), 'OptionName'] = 'Table values are in short tons'
#             sh_name = f'CY{yr}'
#             data.to_excel(writer, sheet_name=sh_name, index=False)
#         return writer
#
#     def inventory_tables2(self, years, df_cols, writer):
#         """
#
#         :param years: The years to summarize.
#         :param df_cols: The primary column headers (column index values) to use.
#         :param writer: The Excel Writer object into which to place the summary tables.
#         :return: An Excel Writer object containing the summary tables.
#         """
#         for yr in years:
#             data = pd.DataFrame(self.input_df.loc[self.input_df['yearID'] == yr],
#                                 columns=df_cols)
#             data = data.round({'PM25_tailpipe': -1, 'NOx_tailpipe': -3})
#             data.loc[len(data.index), 'OptionName'] = 'Table values are in short tons'
#             sh_name = f'CY{yr}'
#             data.to_excel(writer, sheet_name=sh_name, index=False)
#         return writer
#
#     def preamble_ria_tables(self, metrics, index_list, function):
#         """
#
#         :param metrics: The list of metrics within the passed DataFrame to include as data in the returned table.
#         :param index_list: The list of metrics within the passed DataFrame to include as the row index of the returned table.
#         :param function: The function to use (e.g., 'sum', 'mean')
#         :return: A pivot table.
#         """
#         table = pd.pivot_table(self.input_df, metrics, index_list, aggfunc=function)
#         table = table.reindex(metrics, axis=1)
#         table = table.reset_index(drop=False)
#         return table
