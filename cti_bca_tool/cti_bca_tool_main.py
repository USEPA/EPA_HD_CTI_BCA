"""
cti_bca.py

This is the primary module of the benefit cost analysis tool. This module reads input files, calls other modules and generates output files.

"""
import pandas as pd
# import numpy as np
import shutil
from datetime import datetime
# from itertools import product
import time
import cti_bca_tool
from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_per_veh_direct_costs, calc_direct_costs
from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
from cti_bca_tool.tech_costs import calc_per_veh_tech_costs, calc_tech_costs
from cti_bca_tool.def_costs import calc_def_costs, calc_average_def_costs
from cti_bca_tool.fuel_costs import calc_fuel_costs, calc_average_fuel_costs
from cti_bca_tool.repair_costs import calc_emission_repair_costs_per_mile, calc_per_veh_emission_repair_costs, \
    calc_emission_repair_costs, estimated_ages_dict, repair_cpm_dict
from cti_bca_tool.emission_costs import calc_criteria_emission_costs
from cti_bca_tool.sum_by_vehicle import calc_sum_of_costs
from cti_bca_tool.discounting import discount_values
from cti_bca_tool.weighted_results import create_weighted_cost_dict
from cti_bca_tool.calc_deltas import calc_deltas, calc_deltas_weighted
from cti_bca_tool.cti_bca_tool_postproc import doc_tables_post_process, create_output_paths

from cti_bca_tool.general_functions import save_dict_to_csv, convert_dict_to_df, inputs_filenames, get_file_datetime


def main(settings):
    """

    :param settings: The SetInputs class within __main__.py establishes the input files to use and other input settings set in the BCA_Inputs file and needed within the tool.
    :return: The results of the cti_bca_tool.
    """
    print("\nDoing the work....")
    start_time_calcs = time.time()
    # create project fleet data structures, both a DataFrame and a dictionary of regclass based sales
    project_fleet_df = create_fleet_df(settings)

    # create a sales (by regclass) and fleet dictionaries
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(settings, project_fleet_df, 0)
    fleet_averages_dict = create_fleet_averages_dict(settings, project_fleet_df)

    # calculate direct costs per reg class based on cumulative regclass sales (learning is applied to cumulative reg class sales)
    regclass_yoy_costs_per_step = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)

    # calculate total direct costs and then per vehicle costs (per sourcetype)
    fleet_averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step, fleet_averages_dict)
    fleet_totals_dict = calc_direct_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate indirect costs per vehicle and then total indirect costs
    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)

    # calculate tech costs per vehicle and total tech costs
    fleet_averages_dict = calc_per_veh_tech_costs(fleet_averages_dict)
    fleet_totals_dict = calc_tech_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate DEF costs
    fleet_totals_dict = calc_def_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_def_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate fuel costs, including adjustments for fuel consumption associated with ORVR
    fleet_totals_dict = calc_fuel_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_fuel_costs(fleet_totals_dict, fleet_averages_dict)

    # calculate emission repair costs
    fleet_averages_dict = calc_emission_repair_costs_per_mile(settings, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_emission_repair_costs(fleet_averages_dict)
    fleet_totals_dict = calc_emission_repair_costs(fleet_totals_dict, fleet_averages_dict)

    # sum operating costs and operating-tech costs into a single key, value
    fleet_totals_dict = calc_sum_of_costs(fleet_totals_dict, 'OperatingCost', 'DEFCost', 'FuelCost_Pretax', 'EmissionRepairCost')
    fleet_totals_dict = calc_sum_of_costs(fleet_totals_dict, 'TechAndOperatingCost', 'TechCost', 'OperatingCost')
    fleet_averages_dict = calc_sum_of_costs(fleet_averages_dict,
                                            'OperatingCost_Owner_AvgPerMile',
                                            'DEFCost_AvgPerMile', 'FuelCost_Retail_AvgPerMile', 'EmissionRepairCost_AvgPerMile')
    fleet_averages_dict = calc_sum_of_costs(fleet_averages_dict,
                                            'OperatingCost_Owner_AvgPerVeh',
                                            'DEFCost_AvgPerVeh', 'FuelCost_Retail_AvgPerVeh', 'EmissionRepairCost_AvgPerVeh')

    if settings.calc_pollution_effects == 'Y':
        fleet_totals_dict = calc_criteria_emission_costs(settings, fleet_totals_dict)

    # calculate some weighted (wtd) cost per mile (cpm) operating costs
    wtd_def_cpm_dict = create_weighted_cost_dict(settings, fleet_averages_dict, 'DEFCost_AvgPerMile', 'VMT_AvgPerVeh')
    wtd_fuel_cpm_dict = create_weighted_cost_dict(settings, fleet_averages_dict, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh')
    wtd_repair_cpm_dict = create_weighted_cost_dict(settings, fleet_averages_dict, 'EmissionRepairCost_AvgPerMile', 'VMT_AvgPerVeh')

    # discount monetized values
    fleet_totals_dict = discount_values(settings, fleet_totals_dict, 0.03, 0.07)
    fleet_averages_dict = discount_values(settings, fleet_averages_dict, 0.03, 0.07)

    # calculate deltas relative to the passed no action alternative ID
    fleet_totals_dict = calc_deltas(settings, fleet_totals_dict, 0)
    fleet_averages_dict = calc_deltas(settings, fleet_averages_dict, 0)
    wtd_def_cpm_dict = calc_deltas_weighted(wtd_def_cpm_dict, 'DEFCost_AvgPerMile', 0)
    wtd_fuel_cpm_dict = calc_deltas_weighted(wtd_fuel_cpm_dict, 'FuelCost_Retail_AvgPerMile', 0)
    wtd_repair_cpm_dict = calc_deltas_weighted(wtd_repair_cpm_dict, 'EmissionRepairCost_AvgPerMile', 0)

    # convert dictionary to DataFrame to generate pivot tables for copy/past to documents
    fleet_totals_df = convert_dict_to_df(fleet_totals_dict, 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')

    elapsed_time_calcs = time.time() - start_time_calcs

    print("\nSaving the outputs....")
    start_time_outputs = time.time()

    # determine run output paths
    if settings.run_folder_identifier == 'test':
        path_of_run_results_folder = create_output_paths(settings)
    else:
        path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder \
            = create_output_paths(settings)

    document_tables_file = doc_tables_post_process(path_of_run_results_folder, fleet_totals_df)

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    if settings.run_folder_identifier == 'test':
        pass
    else:
        inputs_filename_list = inputs_filenames(settings.input_files_pathlist)

        for file in inputs_filename_list:
            path_source = settings.path_inputs / file
            path_destination = path_of_run_inputs_folder / file
            shutil.copy2(path_source, path_destination)
        for file in settings.files_in_path_code:
            shutil.copy2(file, path_of_code_folder / file.name)
        settings.fuel_prices.to_csv(path_of_modified_inputs_folder / f'fuel_prices_{settings.aeo_case}.csv', index=False)
        settings.regclass_costs.to_csv(path_of_modified_inputs_folder / 'regclass_costs.csv', index=False)
        settings.repair_and_maintenance.to_csv(path_of_modified_inputs_folder / 'repair_and_maintenance.csv')
        settings.def_prices.to_csv(path_of_modified_inputs_folder / 'def_prices.csv', index=False)
        gdp_deflators = pd.DataFrame(settings.gdp_deflators)  # from dict to df
        gdp_deflators.to_csv(path_of_modified_inputs_folder / 'gdp_deflators.csv', index=True)

    # save dictionaries to csv
    print('\nSaving output files.')
    save_dict_to_csv(fleet_totals_dict, path_of_run_results_folder / 'cti_bca_fleet_totals', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(fleet_averages_dict, path_of_run_results_folder / 'cti_bca_fleet_averages', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(estimated_ages_dict, path_of_run_results_folder / 'cti_bca_estimated_ages', 'vehicle', 'modelYearID', 'identifier')
    save_dict_to_csv(repair_cpm_dict, path_of_run_results_folder / 'cti_bca_repair_cpm_details', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')

    save_dict_to_csv(wtd_def_cpm_dict, path_of_run_results_folder / 'vmt_weighted_def_cpm', 'vehicle', 'modelYearID')
    save_dict_to_csv(wtd_fuel_cpm_dict, path_of_run_results_folder / 'vmt_weighted_fuel_cpm', 'vehicle', 'modelYearID')
    save_dict_to_csv(wtd_repair_cpm_dict, path_of_run_results_folder / 'vmt_weighted_emission_repair_cpm', 'vehicle', 'modelYearID')


    # # for figures, an updated options_dict would be nice
    # for alt_num in range(1, len(settings.options_dict)):
    #     k = alt_num * 10
    #     alt0 = settings.options_dict[0]['OptionName']
    #     alt = settings.options_dict[alt_num]['OptionName']
    #     settings.options_dict.update({k: {'OptionName': f'{alt}_minus_{alt0}'}})
    #
    # if settings.generate_emissionrepair_cpm_figures != 'N':
    #     cpm_figure_years = settings.generate_emissionrepair_cpm_figures.split(',')
    #     for i, v in enumerate(cpm_figure_years):
    #         cpm_figure_years[i] = pd.to_numeric(cpm_figure_years[i])
    #     path_figures = path_of_run_results_folder.joinpath('figures')
    #     path_figures.mkdir(exist_ok=True)
    #     alts = pd.Series(bca.loc[bca['optionID'] < 10, 'optionID']).unique()
    #     veh_names = pd.Series(bca['Vehicle_Name_MOVES']).unique()
    #     for veh_name in veh_names:
    #         for cpm_figure_year in cpm_figure_years:
    #             CreateFigures(bca, settings.options_dict, path_figures).line_chart_vs_age(0, alts, cpm_figure_year, veh_name, 'EmissionRepairCost_Owner_AvgPerMile')
    #
    # if settings.generate_BCA_ArgsByOption_figures == 'Y':
    #     yearID_min = int(bca['yearID'].min())
    #     yearID_max = int(bca['yearID'].max())
    #     path_figures = path_of_run_results_folder.joinpath('figures')
    #     path_figures.mkdir(exist_ok=True)
    #     alts = pd.Series(bca.loc[bca['optionID'] >= 10, 'optionID']).unique()
    #     for alt in alts:
    #         CreateFigures(bca_summary, settings.options_dict, path_figures).line_chart_args_by_option(0, alt, yearID_min, yearID_max,
    #                                                                                                   'TechCost_TotalCost',
    #                                                                                                   'EmissionRepairCost_Owner_TotalCost',
    #                                                                                                   'DEFCost_TotalCost',
    #                                                                                                   'FuelCost_Pretax_TotalCost',
    #                                                                                                   'TechAndOperatingCost_BCA_TotalCost'
    #                                                                                                   )
    # if settings.generate_BCA_ArgByOptions_figures == 'Y':
    #     yearID_min = int(bca['yearID'].min())
    #     yearID_max = int(bca['yearID'].max())
    #     path_figures = path_of_run_results_folder.joinpath('figures')
    #     path_figures.mkdir(exist_ok=True)
    #     alts = pd.Series(bca.loc[bca['optionID'] >= 10, 'optionID']).unique()
    #     args = ['TechCost_TotalCost',
    #             'EmissionRepairCost_Owner_TotalCost',
    #             'DEFCost_TotalCost',
    #             'FuelCost_Pretax_TotalCost',
    #             'TechAndOperatingCost_BCA_TotalCost'
    #             ]
    #     for arg in args:
    #         CreateFigures(bca_summary, settings.options_dict, path_figures).line_chart_arg_by_options(0, alts, yearID_min, yearID_max, arg)
    #
    # if settings.create_all_files == 'y' or settings.create_all_files == 'Y' or settings.create_all_files == '':
    #     bca.to_csv(path_of_run_results_folder.joinpath('bca_all_calcs.csv'), index=False)
    #
    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder', 'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [cti_bca_tool.__version__, path_of_run_folder, settings.start_time_readable, settings.elapsed_time_read, elapsed_time_calcs, elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log = pd.concat([summary_log, get_file_datetime(settings.input_files_pathlist)], axis=0, sort=False, ignore_index=True)

    # add summary log to document_tables_file for tracking this file which is the most likely to be shared
    summary_log.to_excel(document_tables_file, sheet_name='summary_log', index=False)
    document_tables_file.save()
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)
    print(f'\nOutput files have been saved to {path_of_run_folder}')


if __name__ == '__main__':
    from cti_bca_tool.cti_bca_tool_setup import SetInputs as settings
    main(settings)
