"""
bca_tool_code.tool_main.py

This is the main module of the tool.

"""
import pandas as pd
import shutil
from datetime import datetime
from time import time

import bca_tool_code.general_modules.emission_cost
import bca_tool_code.general_modules.sum_by_vehicle
import bca_tool_code.general_modules.discounting
import bca_tool_code.general_modules.weighted_results
import bca_tool_code.general_modules.calc_deltas
import bca_tool_code.general_modules.vehicle
import bca_tool_code.general_modules.create_figures

import bca_tool_code.general_input_modules.general_functions as gen_fxns
import bca_tool_code.engine_cost_modules.engine_package_cost as cap_package_cost
import bca_tool_code.vehicle_cost_modules.vehicle_package_cost as ghg_package_cost

from bca_tool_code.tool_setup import SetInputs, SetPaths
from bca_tool_code.cap_costs import CapCosts
from bca_tool_code.ghg_costs import GhgCosts


def main():
    """

    Returns:
        The results of the current run of the tool.

    """
    set_paths = SetPaths()
    run_id = set_paths.run_id()

    settings = SetInputs()

    start_time_calcs = settings.end_time_inputs

    print("\nDoing the work...\n")

    cap_costs = ghg_costs = None

    if settings.calc_cap_costs:

        for vehicle in settings.fleet_cap.vehicles_age0:
            settings.fleet_cap.engine_sales(vehicle)

        for vehicle in settings.fleet_cap.vehicles_age0:
            for start_year in settings.engine_costs.standardyear_ids:
                settings.fleet_cap.cumulative_engine_sales(vehicle, start_year)

        for vehicle in settings.fleet_cap.vehicles_age0:
            for start_year in settings.engine_costs.standardyear_ids:
                cap_package_cost.calc_avg_package_cost_per_step(settings, vehicle, start_year)

        cap_costs = CapCosts()
        cap_costs.calc_cap_costs(settings)

    if settings.calc_ghg_costs:

        for vehicle in settings.fleet_ghg.vehicles_age0:
            for start_year in settings.vehicle_costs.standardyear_ids:
                settings.fleet_ghg.cumulative_vehicle_sales(vehicle, start_year)

        for vehicle in settings.fleet_ghg.vehicles_age0:
            for start_year in settings.vehicle_costs.standardyear_ids:
                ghg_package_cost.calc_avg_package_cost_per_step(settings, vehicle, start_year)

        ghg_costs = GhgCosts()
        ghg_costs.calc_ghg_costs(settings)

    end_time_calcs = start_time_outputs = time()
    elapsed_time_calcs = end_time_calcs - start_time_calcs

    # determine run output paths
    path_of_run_inputs_folder = path_of_code_folder = path_of_modified_inputs_folder = None
    if run_id == 'test':
        path_of_run_results_folder = set_paths.path_test
        path_of_run_results_folder.mkdir(exist_ok=True)
        path_of_run_folder = path_of_run_results_folder
    else:
        path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder \
            = set_paths.create_output_paths(settings.start_time_readable, run_id)

    # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    print('\nCopying input files and code to the outputs folder...\n')

    if run_id == 'test':
        pass
    else:
        inputs_filename_list = gen_fxns.inputs_filenames(settings.input_files_pathlist)

        for file in inputs_filename_list:
            path_source = set_paths.path_inputs / file
            path_destination = path_of_run_inputs_folder / file
            shutil.copy2(path_source, path_destination)
        try:
            set_paths.copy_code_to_destination(path_of_code_folder)
        except Exception:
            print('\nUnable to copy Python code to run results folder when using the executable.\n')

    print("\nSaving the output files...\n")
    stamp = settings.start_time_readable
    if settings.calc_cap_costs:
        gen_fxns.save_dict(
            cap_costs.results,
            path_of_run_results_folder / 'CAP_bca_tool_all',
            row_header=None, stamp=stamp, index=False
        )
        cap_summary_df = gen_fxns.save_dict_return_df(
            settings.annual_summary_cap.results,
            path_of_run_results_folder / 'CAP_bca_tool_annual_summary',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.fleet_cap.sales_by_start_year,
            path_of_run_results_folder / 'CAP_sales_by_implementation_year',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.engine_costs.package_cost_by_step,
            path_of_run_results_folder / 'CAP_package_costs_by_implementation_year',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.markups.contribution_factors,
            path_of_run_results_folder / 'CAP_indirect_cost_details',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.wtd_cap_fuel_cpm_dict,
            path_of_run_results_folder / 'CAP_vmt_weighted_fuel_cpm',
            row_header=None, stamp=stamp, index=True
        )
        gen_fxns.save_dict(
            settings.wtd_def_cpm_dict,
            path_of_run_results_folder / 'CAP_vmt_weighted_def_cpm',
            row_header=None, stamp=stamp, index=True
        )
        gen_fxns.save_dict(
            settings.wtd_repair_cpm_dict,
            path_of_run_results_folder / 'CAP_vmt_weighted_repair_cpm',
            row_header=None, stamp=stamp, index=True
        )
        gen_fxns.save_dict(
            settings.estimated_age.estimated_ages_dict,
            path_of_run_results_folder / 'CAP_estimated_ages',
            row_header=None, stamp=stamp, index=False
        )
        # gen_fxns.save_dict(
        #     settings.emission_repair_cost.repair_cpm_dict,
        #     path_of_run_results_folder / 'CAP_repair_cpm_details',
        #     row_header=None, stamp=stamp, index=False
        # )
        gen_fxns.save_dict(
            settings.emission_repair_cost.repair_cost_details,
            path_of_run_results_folder / 'CAP_repair_cost_details',
            row_header=None, stamp=stamp, index=False
        )

        # save DataFrames to CSV
        settings.engine_costs.piece_costs_in_analysis_dollars.to_csv(
            path_of_modified_inputs_folder / 'CAP_engine_costs.csv', index=False)
        settings.repair_and_maintenance.repair_and_maintenance_in_analysis_dollars.to_csv(
            path_of_modified_inputs_folder / 'repair_and_maintenance.csv', index=True)

        # create figures
        arg_list = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
        bca_tool_code.general_modules.create_figures.CreateFigures(
            cap_summary_df, 'US Dollars', path_of_run_results_folder, 'CAP').create_figures(arg_list)

    if settings.calc_ghg_costs:
        gen_fxns.save_dict(
            ghg_costs.results,
            path_of_run_results_folder / 'GHG_bca_tool_all',
            row_header=None, stamp=stamp, index=False
        )
        ghg_summary_df = gen_fxns.save_dict_return_df(
            settings.annual_summary_ghg.results,
            path_of_run_results_folder / 'GHG_bca_tool_annual_summary',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.fleet_ghg.sales_by_start_year,
            path_of_run_results_folder / 'GHG_sales_by_implementation_year',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.vehicle_costs.package_cost_by_step,
            path_of_run_results_folder / 'GHG_package_costs_by_implementation_year',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.wtd_ghg_fuel_cpm_dict,
            path_of_run_results_folder / 'GHG_vmt_weighted_fuel_cpm',
            row_header=None, stamp=stamp, index=True
        )

        # save DataFrames to CSV
        settings.vehicle_costs.piece_costs_in_analysis_dollars.to_csv(
            path_of_modified_inputs_folder / 'GHG_vehicle_costs.csv', index=False)

        # create figures
        arg_list = ['TechCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
        bca_tool_code.general_modules.create_figures.CreateFigures(
            ghg_summary_df, 'US Dollars', path_of_run_results_folder, 'GHG').create_figures(arg_list)

    # save additional DataFrames to CSV
    settings.fuel_prices.fuel_prices_in_analysis_dollars.to_csv(
        path_of_modified_inputs_folder /
        f'fuel_prices_{settings.general_inputs.get_attribute_value("aeo_fuel_price_case")}.csv', index=False)
    settings.def_prices.def_prices_in_analysis_dollars.to_csv(path_of_modified_inputs_folder / 'def_prices.csv', index=True)
    settings.deflators.deflators_and_adj_factors.to_csv(path_of_modified_inputs_folder / 'deflators.csv', index=True)

    end_time_outputs = end_time = time()
    elapsed_time_outputs = end_time_outputs - start_time_outputs
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    # create and save a summary log for the run
    summary_log = pd.DataFrame(
        data={
            'Item': [
                'Version',
                'Run folder',
                'Calc CAP costs',
                'Calc CAP pollution',
                'Calc GHG costs',
                'Calc GHG pollution',
                'Start of run',
                'End of run',
                'Elapsed time read inputs',
                'Elapsed time calculations',
                'Elapsed time save outputs',
                'Elapsed runtime',
            ],
            'Results': [
                bca_tool_code.__version__,
                path_of_run_folder,
                settings.calc_cap_costs,
                settings.calc_cap_pollution,
                settings.calc_ghg_costs,
                settings.calc_ghg_pollution,
                settings.start_time_readable,
                end_time_readable,
                settings.elapsed_time_inputs,
                elapsed_time_calcs,
                elapsed_time_outputs,
                elapsed_time,
            ],
            'Units': [
                '',
                '',
                '',
                '',
                '',
                '',
                'YYYYmmdd-HHMMSS',
                'YYYYmmdd-HHMMSS',
                'seconds',
                'seconds',
                'seconds',
                'seconds',
            ]
        })
    summary_log = pd.concat([summary_log, gen_fxns.get_file_datetime(settings.input_files_pathlist)],
                            axis=0, sort=False, ignore_index=True)
    summary_log.to_csv(path_of_run_results_folder / f'summary_log_{stamp}.csv', index=False)

    print(f'\nOutput files have been saved to {path_of_run_folder}\n')


if __name__ == '__main__':
    main()
