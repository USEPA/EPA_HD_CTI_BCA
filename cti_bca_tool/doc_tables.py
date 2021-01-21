"""
doc_tables.py

Contains the DocTables class.

"""
import pandas as pd

import cti_bca_tool.general_functions as gen_fxns


def post_process(settings, fleet_totals_df):
    print('\nDoing some post-processing.')
    df = fleet_totals_df.copy()
    index = ['DiscountRate', 'optionID', 'OptionName', 'yearID']
    program_table_args = ['DirectCost', 'WarrantyCost', 'RnDCost', 'OtherCost', 'ProfitCost', 'TechCost',
                          'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'OperatingCost', 'TechAndOperatingCost']
    preamble_program_table = preamble_ria_tables(df, index, sum, *program_table_args)
    preamble_program_table = gen_fxns.round_sig(preamble_program_table, 1000000, 2, *program_table_args)
    preamble_program_table.insert(len(preamble_program_table.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    index = ['DiscountRate', 'optionID', 'OptionName']
    preamble_program_table_pv = preamble_ria_tables(df, index, sum, *program_table_args)
    preamble_program_table_pv = gen_fxns.round_sig(preamble_program_table_pv, 1000000, 2, *program_table_args)
    preamble_program_table_pv.insert(len(preamble_program_table_pv.columns), 'Units_SignificantDigits', 'Millions of USD; 2 sig digits')

    doc_table_dict = {'program': preamble_program_table,
                      'program_pv': preamble_program_table_pv,
                      }

    document_tables_file = pd.ExcelWriter(settings.path_project / 'test/preamble_ria_tables.xlsx')
    for sheet_name in doc_table_dict:
        doc_table_dict[sheet_name].to_excel(document_tables_file, sheet_name=sheet_name)

    # summary_log.to_excel(document_tables_file, sheet_name='summary_log', index=False)
    document_tables_file.save()


def preamble_ria_tables(input_df, index_list, function, *args):
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
    return table


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
