"""
cti_bca_tool.tool_main.py

This is the main module of the tool.

"""
import pandas as pd
import shutil
from datetime import datetime
import time
import cti_bca_tool
from cti_bca_tool.project_fleet import create_fleet_df
from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
from cti_bca_tool.direct_costs import calc_regclass_yoy_costs_per_step, calc_per_veh_direct_costs, calc_direct_costs
from cti_bca_tool.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs
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
from cti_bca_tool.tool_postproc import run_postproc, create_output_paths

from cti_bca_tool.general_functions import save_dict_to_csv, inputs_filenames, get_file_datetime


def main(settings):
    """

    Parameters::
        settings: The SetInputs class.

    Returns:
        The results of the current run of the cti_bca_tool.

    """
    print("\nDoing the work....")
    start_time_calcs = time.time()
    # create project fleet DataFrame which will include adjustments to the MOVES input file that are unique to the project.
    project_fleet_df = create_fleet_df(settings)

    # create a sales (by regclass) and fleet dictionaries
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

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
    # the totals_dict here uses pre-tax fuel price since it serves as the basis for social costs
    # the averages_dict uses retail fuel prices since it serves as the basis for average operating costs which are relevant to owners
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

    # discount monetized values; if calculating emission costs, the discount rates entered in the BCA_General_Inputs workbook should be consistent with the
    # criteria cost factors input workbook
    fleet_totals_dict = discount_values(settings, fleet_totals_dict, settings.discrate_social_low, settings.discrate_social_high)
    fleet_averages_dict = discount_values(settings, fleet_averages_dict, settings.discrate_social_low, settings.discrate_social_high)

    # calculate deltas relative to the passed no action alternative ID
    fleet_totals_dict = calc_deltas(settings, fleet_totals_dict)
    fleet_averages_dict = calc_deltas(settings, fleet_averages_dict)
    wtd_def_cpm_dict = calc_deltas_weighted(settings, wtd_def_cpm_dict, 'DEFCost_AvgPerMile')
    wtd_fuel_cpm_dict = calc_deltas_weighted(settings, wtd_fuel_cpm_dict, 'FuelCost_Retail_AvgPerMile')
    wtd_repair_cpm_dict = calc_deltas_weighted(settings, wtd_repair_cpm_dict, 'EmissionRepairCost_AvgPerMile')

    elapsed_time_calcs = time.time() - start_time_calcs

    # determine run output paths
    if settings.run_folder_identifier == 'test':
        path_of_run_results_folder = settings.path_test
        path_of_run_results_folder.mkdir(exist_ok=True)
        path_of_run_folder = path_of_run_results_folder
    else:
        path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder \
            = create_output_paths(settings)

    start_time_postproc = time.time()

    # do the post-processing to generate document tables, an annual summary and some figures
    document_tables_file = run_postproc(settings, path_of_run_results_folder, fleet_totals_dict)

    elapsed_time_postproc = time.time() - start_time_postproc

    start_time_outputs = time.time()

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    print('Copy input files and code to the outputs folder.')
    if settings.run_folder_identifier == 'test':
        pass
    else:
        inputs_filename_list = inputs_filenames(settings.input_files_pathlist)

        for file in inputs_filename_list:
            path_source = settings.path_inputs / file
            path_destination = path_of_run_inputs_folder / file
            shutil.copy2(path_source, path_destination)
        for file in settings.files_in_path_code:
            try:
                shutil.copy2(file, path_of_code_folder / file.name)
            except:
                print('Unable to copy Python code to run results folder when using the executable.')
        settings.fuel_prices.to_csv(path_of_modified_inputs_folder / f'fuel_prices_{settings.aeo_case}.csv', index=False)
        settings.regclass_costs.to_csv(path_of_modified_inputs_folder / 'regclass_costs.csv', index=False)
        settings.repair_and_maintenance.to_csv(path_of_modified_inputs_folder / 'repair_and_maintenance.csv')
        settings.def_prices.to_csv(path_of_modified_inputs_folder / 'def_prices.csv', index=False)
        gdp_deflators = pd.DataFrame(settings.gdp_deflators)  # from dict to df
        gdp_deflators.to_csv(path_of_modified_inputs_folder / 'gdp_deflators.csv', index=True)

    # save dictionaries to csv
    print("\nSaving the output files....")
    save_dict_to_csv(fleet_totals_dict, path_of_run_results_folder / 'cti_bca_fleet_totals', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(fleet_averages_dict, path_of_run_results_folder / 'cti_bca_fleet_averages', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')
    save_dict_to_csv(estimated_ages_dict, path_of_run_results_folder / 'cti_bca_estimated_ages', 'vehicle', 'modelYearID', 'identifier')
    save_dict_to_csv(repair_cpm_dict, path_of_run_results_folder / 'cti_bca_repair_cpm_details', 'vehicle', 'modelYearID', 'ageID', 'DiscountRate')

    save_dict_to_csv(wtd_def_cpm_dict, path_of_run_results_folder / 'cti_bca_vmt_weighted_def_cpm', 'vehicle', 'modelYearID')
    save_dict_to_csv(wtd_fuel_cpm_dict, path_of_run_results_folder / 'cti_bca_vmt_weighted_fuel_cpm', 'vehicle', 'modelYearID')
    save_dict_to_csv(wtd_repair_cpm_dict, path_of_run_results_folder / 'cti_bca_vmt_weighted_emission_repair_cpm', 'vehicle', 'modelYearID')

    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder', 'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time post-processing', 'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [cti_bca_tool.__version__, path_of_run_folder, settings.start_time_readable, settings.elapsed_time_read, elapsed_time_calcs, elapsed_time_postproc, elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log = pd.concat([summary_log, get_file_datetime(settings.input_files_pathlist)], axis=0, sort=False, ignore_index=True)

    # add summary log to document_tables_file for tracking this file which is the most likely to be shared
    summary_log.to_excel(document_tables_file, sheet_name='summary_log', index=False)
    document_tables_file.save()
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)
    print(f'\nOutput files have been saved to {path_of_run_folder}')


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    main(settings)
