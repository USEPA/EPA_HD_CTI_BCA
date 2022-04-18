"""
bca_tool_code.tool_main.py

This is the main module of the tool.

"""
import pandas as pd
import shutil
from datetime import datetime
from time import time
from bca_tool_code.tool_setup import SetInputs, SetPaths

import bca_tool_code.cap_modules.package_costs
from bca_tool_code.cap_modules.indirect_costs import calc_indirect_costs_per_veh, calc_indirect_costs
from bca_tool_code.cap_modules.tech_costs import calc_tech_costs_per_veh, calc_tech_costs

from bca_tool_code.cap_modules.def_costs import calc_def_costs_per_veh, calc_def_costs
import bca_tool_code.cap_modules.fuel_costs
from bca_tool_code.cap_modules.repair_costs import calc_emission_repair_costs_per_mile, calc_emission_repair_costs_per_veh, \
    calc_emission_repair_costs

from bca_tool_code.emission_costs import calc_criteria_emission_costs

import bca_tool_code.ghg_modules.package_costs
import bca_tool_code.ghg_modules.fuel_costs

from bca_tool_code.sum_by_vehicle import calc_sum_of_costs
from bca_tool_code.discounting import discount_values
from bca_tool_code.cap_modules.annual_summary import AnnualSummaryCAP
from bca_tool_code.ghg_modules.annual_summary import AnnualSummaryGHG
from bca_tool_code.weighted_results import create_weighted_cost_dict
from bca_tool_code.calc_deltas import calc_deltas, calc_deltas_weighted
from bca_tool_code.vehicle import Vehicle
from bca_tool_code.general_input_modules.general_functions import save_dict, save_dict_return_df, get_file_datetime, \
    inputs_filenames
from bca_tool_code.create_figures import CreateFigures


def main():
    """

    Returns:
        The results of the current run of the tool.

    """
    # start_time_calcs = time()
    set_paths = SetPaths()
    run_id = set_paths.run_id()

    settings = SetInputs()

    start_time_calcs = settings.end_time_inputs

    print("\nDoing the work...\n")

    if settings.calc_cap_costs:

        # calculate package costs based on cumulative sales (learning is applied to cumulative sales)
        bca_tool_code.cap_modules.package_costs.calc_avg_package_cost_per_step(settings)
        bca_tool_code.cap_modules.package_costs.calc_package_costs_per_veh(settings, settings.fleet_cap)
        bca_tool_code.cap_modules.package_costs.calc_package_costs(settings.fleet_cap)

        # calculate indirect costs
        calc_indirect_costs_per_veh(settings, settings.fleet_cap)
        calc_indirect_costs(settings, settings.fleet_cap)

        # calculate total tech costs as direct plus indirect
        calc_tech_costs_per_veh(settings.fleet_cap)
        calc_tech_costs(settings.fleet_cap)

        # calculate DEF costs
        calc_def_costs(settings, settings.fleet_cap)
        calc_def_costs_per_veh(settings.fleet_cap)

        # calculate fuel costs, including adjustments for fuel consumption associated with ORVR
        bca_tool_code.cap_modules.fuel_costs.calc_fuel_costs(settings, settings.fleet_cap)
        bca_tool_code.cap_modules.fuel_costs.calc_fuel_costs_per_veh(settings.fleet_cap)

        # calculate emission repair costs
        calc_emission_repair_costs_per_mile(settings, settings.fleet_cap)
        calc_emission_repair_costs_per_veh(settings.fleet_cap)
        calc_emission_repair_costs(settings.fleet_cap)

        # sum attributes in the attributes_to_sum dictionary
        for summed_attribute, sum_attributes in settings.fleet_cap.attributes_to_sum.items():
            calc_sum_of_costs(settings.fleet_cap, summed_attribute, *sum_attributes)

        # calc CAP pollution effects, if applicable
        if settings.calc_cap_pollution:
            calc_criteria_emission_costs(settings, settings.fleet_cap)

        create_weighted_cost_dict(settings, settings.fleet_cap, settings.wtd_def_cpm_dict,
                                  'DEFCost_PerMile', 'VMT_PerVeh')
        create_weighted_cost_dict(settings, settings.fleet_cap, settings.wtd_repair_cpm_dict,
                                  'EmissionRepairCost_PerMile', 'VMT_PerVeh')
        create_weighted_cost_dict(settings, settings.fleet_cap, settings.wtd_cap_fuel_cpm_dict,
                                  'FuelCost_Retail_PerMile', 'VMT_PerVeh')

        discount_values(settings, settings.fleet_cap)

        # calc the annual summary, present values and annualized values (excluding cost/veh and cost/mile results)
        settings.annual_summary_cap.annual_summary(settings, settings.fleet_cap, settings.annual_summary_cap, settings.options_cap)
        # AnnualSummaryCAP.annual_summary(settings, settings.fleet_cap, settings.annual_summary_cap, settings.options_cap)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, settings.fleet_cap)
        calc_deltas(settings, settings.annual_summary_cap)

        settings.wtd_def_cpm_dict = calc_deltas_weighted(settings, settings.wtd_def_cpm_dict)
        settings.wtd_repair_cpm_dict = calc_deltas_weighted(settings, settings.wtd_repair_cpm_dict)
        settings.wtd_cap_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_cap_fuel_cpm_dict)

    if settings.calc_ghg_costs:

        # calculate package costs based on cumulative sales (learning is applied to cumulative sales)
        bca_tool_code.ghg_modules.package_costs.calc_avg_package_cost_per_step(settings)
        bca_tool_code.ghg_modules.package_costs.calc_package_costs_per_veh(settings, settings.fleet_ghg)
        bca_tool_code.ghg_modules.package_costs.calc_package_costs(settings.fleet_ghg)

        bca_tool_code.ghg_modules.fuel_costs.calc_fuel_costs(settings, settings.fleet_ghg)
        bca_tool_code.ghg_modules.fuel_costs.calc_fuel_costs_per_veh(settings.fleet_ghg)

        # sum attributes in the attributes_to_sum dictionary
        for summed_attribute, sum_attributes in settings.fleet_ghg.attributes_to_sum.items():
            calc_sum_of_costs(settings.fleet_ghg, summed_attribute, *sum_attributes)

        # calc GHG pollution effects, if applicable
        if settings.calc_ghg_pollution:
            pass

        create_weighted_cost_dict(settings, settings.fleet_ghg, settings.wtd_ghg_fuel_cpm_dict,
                                  'FuelCost_Retail_PerMile', 'VMT_PerVeh')

        discount_values(settings, settings.fleet_ghg)

        # calc the annual summary, present values and annualized values (excluding cost/veh and cost/mile results)
        settings.annual_summary_ghg.annual_summary(settings, settings.fleet_ghg, settings.annual_summary_ghg, settings.options_ghg)
        # AnnualSummaryGHG.annual_summary(settings, settings.fleet_ghg, settings.annual_summary_ghg, settings.options_ghg)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, settings.fleet_ghg)
        calc_deltas(settings, settings.annual_summary_ghg)

        settings.wtd_ghg_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_ghg_fuel_cpm_dict)

    # pass dicts thru the vehicle_name and/or option_name function to add some identifiers and generate some figures
    if settings.calc_cap_costs:
        # add option names using data objects
        for obj in [settings.fleet_cap, settings.regclass_sales, settings.annual_summary_cap]:
            Vehicle().option_name(settings, settings.options_cap, data_object=obj, data_dict=None)

        # add vehicle names using data objects (exclude annual summary objects)
        for obj in [settings.fleet_cap, settings.regclass_sales]:
            Vehicle().vehicle_name(data_object=obj, data_dict=None)

        # add option and vehicle names using data dictionaries
        for obj in [settings.wtd_cap_fuel_cpm_dict, settings.wtd_repair_cpm_dict, settings.wtd_def_cpm_dict]:
            Vehicle().option_name(settings, settings.options_cap, data_object=None, data_dict=obj)
            Vehicle().vehicle_name(data_object=None, data_dict=obj)

    if settings.calc_ghg_costs:
        # add option names using data objects
        for obj in [settings.fleet_ghg, settings.sourcetype_sales, settings.annual_summary_ghg]:
            Vehicle().option_name(settings, settings.options_ghg, data_object=obj, data_dict=None)

        # add vehicle names using data objects (exclude annual summary objects)
        for obj in [settings.fleet_ghg, settings.sourcetype_sales]:
            Vehicle().vehicle_name(data_object=obj, data_dict=None)

        # add option and vehicle names using data dictionaries
        for obj in [settings.wtd_ghg_fuel_cpm_dict]:
            Vehicle().option_name(settings, settings.options_ghg, data_object=None, data_dict=obj)
            Vehicle().vehicle_name(data_object=None, data_dict=obj)

    end_time_calcs = start_time_outputs = time()
    elapsed_time_calcs = end_time_calcs - start_time_calcs

    # determine run output paths
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
        inputs_filename_list = inputs_filenames(settings.input_files_pathlist)

        for file in inputs_filename_list:
            path_source = set_paths.path_inputs / file
            path_destination = path_of_run_inputs_folder / file
            shutil.copy2(path_source, path_destination)
        try:
            set_paths.copy_code_to_destination(path_of_code_folder)
        except Exception:
            print('\nUnable to copy Python code to run results folder when using the executable.\n')

    print("\nSaving the output files...\n")
    if settings.calc_cap_costs:
        stamp = settings.start_time_readable
        header = settings.row_header_for_fleet_files
        save_dict(settings.fleet_cap._dict, path_of_run_results_folder / 'CAP_bca_tool_all',
                  row_header=header, stamp=stamp, index=False)

        header = settings.row_header_for_annual_summary_files
        cap_summary_df = save_dict_return_df(settings.annual_summary_cap._dict,
                                             path_of_run_results_folder / 'CAP_bca_tool_annual_summary',
                                             row_header=header, stamp=stamp, index=False)

        save_dict(settings.regclass_sales._dict, path_of_run_results_folder / 'CAP_sales_and_costs_by_step',
                  row_header=None, stamp=stamp, index=False)
        save_dict(settings.regclass_costs._dict, path_of_modified_inputs_folder / 'regclass_costs',
                  row_header=None, stamp=stamp, index=False)
        save_dict(settings.wtd_cap_fuel_cpm_dict, path_of_run_results_folder / 'CAP_vmt_weighted_fuel_cpm',
                  row_header=None, stamp=stamp, index=True)
        save_dict(settings.wtd_def_cpm_dict, path_of_run_results_folder / 'CAP_vmt_weighted_def_cpm',
                  row_header=None, stamp=stamp, index=True)
        save_dict(settings.wtd_repair_cpm_dict, path_of_run_results_folder / 'CAP_vmt_weighted_repair_cpm',
                  row_header=None, stamp=stamp, index=True)

        # create figures
        arg_list = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
        CreateFigures(cap_summary_df, 'US Dollars', path_of_run_results_folder, 'CAP').create_figures(arg_list)

    stamp = settings.start_time_readable
    if settings.calc_ghg_costs:
        header = settings.row_header_for_fleet_files
        save_dict(settings.fleet_ghg._dict, path_of_run_results_folder / 'GHG_bca_tool_all',
                  row_header=header, stamp=stamp, index=False)

        header = settings.row_header_for_annual_summary_files
        ghg_summary_df = save_dict_return_df(settings.annual_summary_ghg._dict,
                                             path_of_run_results_folder / 'GHG_bca_tool_annual_summary',
                                             row_header=header, stamp=stamp, index=False)

        save_dict(settings.sourcetype_sales._dict, path_of_run_results_folder / 'GHG_sales_and_costs_by_step',
                  row_header=None, stamp=stamp, index=False)
        save_dict(settings.sourcetype_costs._dict, path_of_modified_inputs_folder / 'sourcetype_costs',
                  row_header=None, stamp=stamp, index=False)
        save_dict(settings.wtd_ghg_fuel_cpm_dict, path_of_run_results_folder / 'GHG_vmt_weighted_fuel_cpm',
                  row_header=None, stamp=stamp, index=True)

        # create figures
        arg_list = ['TechCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
        CreateFigures(ghg_summary_df, 'US Dollars', path_of_run_results_folder, 'GHG').create_figures(arg_list)

    save_dict(settings.fuel_prices.fuel_prices_in_analysis_dollars,
              path_of_modified_inputs_folder / f'fuel_prices_{settings.general_inputs.get_attribute_value("aeo_fuel_price_case")}',
              row_header=None, stamp=stamp, index=False)
    save_dict(settings.def_prices.def_prices_in_analysis_dollars,
              path_of_modified_inputs_folder / 'def_prices', row_header=None, stamp=stamp, index=False)
    save_dict(settings.deflators.deflators_and_adj_factors, path_of_modified_inputs_folder / 'deflators',
              row_header=None, stamp=stamp, index=False)

    end_time_outputs = end_time = time()
    elapsed_time_outputs = end_time_outputs - start_time_outputs
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    summary_log = pd.DataFrame(
        data={'Item': ['Version', 'Run folder',
                       'Calc CAP costs', 'Calc CAP pollution',
                       'Calc GHG costs', 'Calc GHG pollution',
                       'Start of run', 'End of run',
                       'Elapsed time read inputs', 'Elapsed time calculations',
                       'Elapsed time save outputs', 'Elapsed runtime',
                       ],
              'Results': [bca_tool_code.__version__, path_of_run_folder,
                          settings.calc_cap_costs, settings.calc_cap_pollution,
                          settings.calc_ghg_costs, settings.calc_ghg_pollution,
                          settings.start_time_readable, end_time_readable,
                          settings.elapsed_time_inputs, elapsed_time_calcs,
                          elapsed_time_outputs, elapsed_time,
                          ],
              'Units': ['', '',
                        '', '',
                        '', '',
                        'YYYYmmdd-HHMMSS', 'YYYYmmdd-HHMMSS',
                        'seconds', 'seconds',
                        'seconds', 'seconds',
                        ]
              })
    summary_log = pd.concat([summary_log, get_file_datetime(settings.input_files_pathlist)],
                            axis=0, sort=False, ignore_index=True)
    summary_log.to_csv(path_of_run_results_folder / f'summary_log_{stamp}.csv', index=False)

    print(f'\nOutput files have been saved to {path_of_run_folder}\n')


if __name__ == '__main__':
    main()
