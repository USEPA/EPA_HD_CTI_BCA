import pandas as pd
import shutil
from datetime import datetime
from time import time

from bca_tool_code.set_inputs import SetInputs
from bca_tool_code.set_paths import SetPaths
import bca_tool_code.general_modules.sum_by_vehicle
import bca_tool_code.general_modules.discounting
import bca_tool_code.general_modules.calc_deltas
import bca_tool_code.general_modules.vehicle
import bca_tool_code.general_modules.create_figures
import bca_tool_code.general_input_modules.general_functions as gen_fxns


def main():
    """
    This is the main module of the tool.

    Returns:
        The results of the current run of the tool.

    """
    set_paths = SetPaths()
    run_id = set_paths.run_id()

    settings = SetInputs()

    start_time_calcs = settings.end_time_inputs

    print("\nDoing the work...\n")

    if settings.runtime_options.calc_cap_costs:
        settings.cost_calcs.calc_results(settings)

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
            shutil.copy2(set_paths.path_project / 'requirements.txt', path_of_run_folder)
        except Exception:
            print('\nUnable to copy Python code to run results folder when using the executable.\n')

    print("\nSaving the output files...\n")
    stamp = f'{settings.project_name}_{settings.start_time_readable}'
    if settings.runtime_options.calc_cap_costs:
        gen_fxns.save_dict(
            settings.cost_calcs.results,
            path_of_run_results_folder / 'all_costs',
            row_header=None, stamp=stamp, index=False
        )
        annual_summary_df = gen_fxns.save_dict_return_df(
            settings.annual_summary_cap.results,
            path_of_run_results_folder / 'annual_summary',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.fleet.sales_by_start_year,
            path_of_run_results_folder / 'sales_by_implementation_year',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.engine_costs.package_cost_by_step,
            path_of_run_results_folder / 'package_costs_by_implementation_year',
            row_header=None, stamp=stamp, index=False
        )
        if settings.replacement_costs:
            gen_fxns.save_dict(
                settings.replacement_costs.package_cost_by_step,
                path_of_run_results_folder / 'replacement_costs_by_implementation_year',
                row_header=None, stamp=stamp, index=False
            )
        gen_fxns.save_dict(
            settings.markups.contribution_factors,
            path_of_run_results_folder / 'indirect_cost_details',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.estimated_age.estimated_ages_dict,
            path_of_run_results_folder / 'required_and_estimated_ages',
            row_header=None, stamp=stamp, index=False
        )
        gen_fxns.save_dict(
            settings.emission_repair_cost.repair_cost_details,
            path_of_run_results_folder / 'repair_cost_details',
            row_header=None, stamp=stamp, index=False
        )

        # save DataFrames to CSV
        settings.engine_costs.piece_costs_in_analysis_dollars.to_csv(
            path_of_modified_inputs_folder / f'engine_costs_{stamp}.csv', index=False)
        settings.repair_and_maintenance.repair_and_maintenance_in_analysis_dollars.to_csv(
            path_of_modified_inputs_folder / f'repair_and_maintenance_{stamp}.csv', index=True)
        settings.warranty_base_costs.piece_costs_in_analysis_dollars.to_csv(
            path_of_modified_inputs_folder / f'base_warranty_costs_{stamp}.csv', index=False)
        if settings.replacement_costs:
            settings.replacement_costs.piece_costs_in_analysis_dollars.to_csv(
                path_of_modified_inputs_folder / f'replacement_costs_{stamp}.csv', index=False)

        # create figures, which are based on the annual summary, which requires discounted values
        if settings.runtime_options.discount_values:
            arg_list = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
            bca_tool_code.general_modules.create_figures.CreateFigures(
                annual_summary_df, 'US Dollars', path_of_run_results_folder, settings.project_name).create_figures(arg_list)

    # save additional DataFrames to CSV
    settings.fuel_prices.fuel_prices_in_analysis_dollars.to_csv(
        path_of_modified_inputs_folder /
        f'fuel_prices_{settings.general_inputs.get_attribute_value("aeo_fuel_price_case")}_{stamp}.csv', index=False)
    settings.def_prices.def_prices_in_analysis_dollars.to_csv(path_of_modified_inputs_folder / f'def_prices_{stamp}.csv', index=True)
    settings.deflators.deflators_and_adj_factors.to_csv(path_of_modified_inputs_folder / f'deflators_{stamp}.csv', index=True)

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
                'Discount Values',
                'Calculate Deltas',
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
                settings.runtime_options.calc_cap_costs,
                settings.runtime_options.calc_cap_pollution,
                settings.runtime_options.discount_values,
                settings.runtime_options.calc_deltas,
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
