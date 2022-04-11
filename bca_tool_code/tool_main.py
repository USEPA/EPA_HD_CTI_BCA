"""
cti_bca_tool.tool_main.py

This is the main module of the tool.

"""
import pandas as pd
from datetime import datetime
from time import time
# from bca_tool_code.input_dict import InputFiles
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


def main():
    """

    Returns:
        The results of the current run of the tool.

    """
    start_time_calcs = time()
    set_paths = SetPaths()
    run_id = set_paths.run_id()

    settings = SetInputs()

    print("\nDoing the work...\n")

    if settings.calc_cap_costs:

        # calculate package costs based on cumulative sales (learning is applied to cumulative sales)
        bca_tool_code.cap_modules.package_costs.calc_avg_package_cost_per_step(
            settings, settings.regclass_costs, settings.regclass_learning_scalers, settings.regclass_sales)
        bca_tool_code.cap_modules.package_costs.calc_package_costs_per_veh(
            settings, settings.fleet_cap, settings.regclass_sales, 'Direct')
        bca_tool_code.cap_modules.package_costs.calc_package_costs(settings.fleet_cap, 'Direct', 'VPOP_withTech')

        # calculate indirect costs
        calc_indirect_costs_per_veh(settings, settings.fleet_cap, 'Direct')
        calc_indirect_costs(settings, settings.fleet_cap, 'VPOP_withTech')

        # calculate total tech costs as direct plus indirect
        calc_tech_costs_per_veh(settings.fleet_cap, 'Direct')
        calc_tech_costs(settings.fleet_cap, 'VPOP_withTech')

        # calculate DEF costs
        calc_def_costs(settings, settings.fleet_cap)
        calc_def_costs_per_veh(settings.fleet_cap, 'VPOP_withTech')

        # calculate fuel costs, including adjustments for fuel consumption associated with ORVR
        bca_tool_code.cap_modules.fuel_costs.calc_fuel_costs(settings, settings.fleet_cap)
        bca_tool_code.cap_modules.fuel_costs.calc_fuel_costs_per_veh(settings.fleet_cap, 'VPOP_withTech', 'VMT_withTech')

        # calculate emission repair costs
        calc_emission_repair_costs_per_mile(settings, settings.fleet_cap)
        calc_emission_repair_costs_per_veh(settings.fleet_cap)
        calc_emission_repair_costs(settings.fleet_cap, 'VPOP_withTech')

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
        AnnualSummaryCAP.annual_summary(settings, settings.fleet_cap, settings.annual_summary_cap, settings.options_cap)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, settings.fleet_cap)
        calc_deltas(settings, settings.annual_summary_cap)

        settings.wtd_def_cpm_dict = calc_deltas_weighted(settings, settings.wtd_def_cpm_dict)
        settings.wtd_repair_cpm_dict = calc_deltas_weighted(settings, settings.wtd_repair_cpm_dict)
        settings.wtd_cap_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_cap_fuel_cpm_dict)

    if settings.calc_ghg_costs:

        # calculate package costs based on cumulative sales (learning is applied to cumulative sales)
        bca_tool_code.ghg_modules.package_costs.calc_avg_package_cost_per_step(
            settings, settings.sourcetype_costs, settings.sourcetype_learning_scalers, settings.sourcetype_sales)
        bca_tool_code.ghg_modules.package_costs.calc_package_costs_per_veh(
            settings, settings.fleet_ghg, settings.sourcetype_sales, 'Tech')
        bca_tool_code.ghg_modules.package_costs.calc_package_costs(settings.fleet_ghg, 'Tech', 'VPOP')

        bca_tool_code.ghg_modules.fuel_costs.calc_fuel_costs(settings, settings.fleet_ghg)
        bca_tool_code.ghg_modules.fuel_costs.calc_fuel_costs_per_veh(settings.fleet_ghg, 'VPOP', 'VMT')

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
        AnnualSummaryGHG.annual_summary(settings, settings.fleet_ghg, settings.annual_summary_ghg, settings.options_ghg)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, settings.fleet_ghg)
        calc_deltas(settings, settings.annual_summary_ghg)

        settings.wtd_ghg_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_ghg_fuel_cpm_dict)

    elapsed_time_calcs = time() - start_time_calcs

    # determine run output paths
    if run_id == 'test':
        path_of_run_results_folder = set_paths.path_test
        path_of_run_results_folder.mkdir(exist_ok=True)
        path_of_run_folder = path_of_run_results_folder
    else:
        path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder \
            = set_paths.create_output_paths(settings.start_time_readable, run_id)

    start_time_postproc = time()

    for obj in [settings.fleet_cap, settings.regclass_sales]:
        Vehicle().vehicle_name(data_object=obj, data_dict=None)
        Vehicle().option_name(settings, settings.options_cap, data_object=obj, data_dict=None)
    Vehicle().option_name(settings, settings.options_cap, data_object=settings.annual_summary_cap, data_dict=None)

    for obj in [settings.wtd_cap_fuel_cpm_dict, settings.wtd_ghg_fuel_cpm_dict,
                settings.wtd_repair_cpm_dict, settings.wtd_def_cpm_dict,
                ]:
        Vehicle().vehicle_name(data_object=None, data_dict=obj)
        Vehicle().option_name(settings, settings.options_cap, data_object=None, data_dict=obj)

    for obj in [settings.fleet_ghg, settings.sourcetype_sales]:
        Vehicle().vehicle_name(data_object=obj, data_dict=None)
        Vehicle().option_name(settings, settings.options_ghg, data_object=obj, data_dict=None)
    Vehicle().option_name(settings, settings.options_ghg, data_object=settings.annual_summary_ghg, data_dict=None)

    for obj in [settings.wtd_ghg_fuel_cpm_dict]:
        Vehicle().vehicle_name(data_object=None, data_dict=obj)
        Vehicle().option_name(settings, settings.options_ghg, data_object=None, data_dict=obj)
    #
    # # pass dicts thru the vehicle_name and/or option_name function to add some identifiers and generate some figures
    # if settings.calc_cap:
    #     # add identifier attributes
    #     cap_totals_dict = Vehicle().vehicle_name(settings, settings.options_cap_dict, cap_totals_dict)
    #     cap_averages_dict = Vehicle().vehicle_name(settings, settings.options_cap_dict, cap_averages_dict)
    #     cap_pv_annualized_dict = Vehicle().option_name(settings, settings.options_cap_dict, cap_pv_annualized_dict)
    #
    #     # rearrange columns for better presentation
    #     cap_totals_df = pd.DataFrame(cap_totals_dict).transpose()
    #     cols = [col for col in cap_totals_df.columns if col not in settings.row_header_for_fleet_files]
    #     cap_totals_df = pd.DataFrame(cap_totals_df, columns=settings.row_header_for_fleet_files + cols)
    #
    #     cap_averages_df = pd.DataFrame(cap_averages_dict).transpose()
    #     cols = [col for col in cap_averages_df.columns if col not in settings.row_header_for_fleet_files]
    #     cap_averages_df = pd.DataFrame(cap_averages_df, columns=settings.row_header_for_fleet_files + cols)
    #
    #     cap_pv_annualized_df = pd.DataFrame(cap_pv_annualized_dict).transpose()
    #     cols = [col for col in cap_pv_annualized_df.columns if col not in settings.row_header_for_annual_summary_files]
    #     cap_pv_annualized_df = pd.DataFrame(cap_pv_annualized_df, columns=settings.row_header_for_annual_summary_files + cols)
    #
    # if settings.calc_ghg:
    #     # add identifier attributes
    #     ghg_totals_dict = Vehicle().vehicle_name(settings, settings.options_ghg_dict, ghg_totals_dict)
    #     ghg_averages_dict = Vehicle().vehicle_name(settings, settings.options_ghg_dict, ghg_averages_dict)
    #     ghg_pv_annualized_dict = Vehicle().option_name(settings, settings.options_ghg_dict, ghg_pv_annualized_dict)
    #
    #     # rearrange columns for better presentation
    #     ghg_totals_df = pd.DataFrame(ghg_totals_dict).transpose()
    #     cols = [col for col in ghg_totals_df.columns if col not in settings.row_header_for_fleet_files]
    #     ghg_totals_df = pd.DataFrame(ghg_totals_df, columns=settings.row_header_for_fleet_files + cols)
    #
    #     ghg_averages_df = pd.DataFrame(ghg_averages_dict).transpose()
    #     cols = [col for col in ghg_averages_df.columns if col not in settings.row_header_for_fleet_files]
    #     ghg_averages_df = pd.DataFrame(ghg_averages_df, columns=settings.row_header_for_fleet_files + cols)
    #
    #     ghg_pv_annualized_df = pd.DataFrame(ghg_pv_annualized_dict).transpose()
    #     cols = [col for col in ghg_pv_annualized_df.columns if col not in settings.row_header_for_annual_summary_files]
    #     ghg_pv_annualized_df = pd.DataFrame(ghg_pv_annualized_df, columns=settings.row_header_for_annual_summary_files + cols)
    #
    elapsed_time_postproc = time() - start_time_postproc

    start_time_outputs = time()
    #
    # # copy input files into results folder; also save fuel_prices and reshaped files to this folder
    # print('\nCopying input files and code to the outputs folder...\n')
    #
    # if run_id == 'test':
    #     pass
    # else:
    #     inputs_filename_list = inputs_filenames(settings.input_files_pathlist)
    #
    #     for file in inputs_filename_list:
    #         path_source = set_paths.path_inputs / file
    #         path_destination = path_of_run_inputs_folder / file
    #         shutil.copy2(path_source, path_destination)
    #     for file in set_paths.files_in_code_folder():
    #         try:
    #             shutil.copy2(file, path_of_code_folder / file.name)
    #         except:
    #             print('\nUnable to copy Python code to run results folder when using the executable.\n')
    #     settings.fuel_prices.to_csv(path_of_modified_inputs_folder / f'fuel_prices_{settings.aeo_case}.csv', index=False)
    #     settings.regclass_costs.to_csv(path_of_modified_inputs_folder / 'regclass_costs.csv', index=False)
    #     settings.sourcetype_costs.to_csv(path_of_modified_inputs_folder / 'sourcetype_costs.csv', index=False)
    #     settings.repair_and_maintenance.to_csv(path_of_modified_inputs_folder / 'repair_and_maintenance.csv')
    #     settings.def_prices.to_csv(path_of_modified_inputs_folder / 'def_prices.csv', index=False)
    #     gdp_deflators = pd.DataFrame(settings.gdp_deflators)  # from dict to df
    #     gdp_deflators.to_csv(path_of_modified_inputs_folder / 'gdp_deflators.csv', index=True)
    #
    # # save dictionaries to csv and also add some identifying info using the vehicle_name function
    # print("\nSaving the output files...\n")
    #
    # if settings.calc_cap:
    #     cap_totals_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_fleet_totals_{settings.start_time_readable}.csv', index=False)
    #     cap_averages_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_fleet_averages_{settings.start_time_readable}.csv', index=False)
    #     cap_pv_annualized_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_annual_summary_{settings.start_time_readable}.csv', index=False)
    #
    #     save_dict_to_csv(Vehicle().vehicle_name(settings, settings.options_cap_dict, estimated_ages_dict),
    #                      path_of_run_results_folder / f'CAP_bca_tool_estimated_ages_{settings.start_time_readable}',
    #                      list(),
    #                      'vehicle', 'optionID', 'modelYearID', 'identifier')
    #     save_dict_to_csv(Vehicle().vehicle_name(settings, settings.options_cap_dict, repair_cpm_dict),
    #                      path_of_run_results_folder / f'CAP_bca_tool_repair_cpm_details_{settings.start_time_readable}',
    #                      list(),
    #                      'vehicle', 'optionID', 'modelYearID', 'ageID', 'DiscountRate')
    #
    #     save_dict_to_csv(wtd_def_cpm_dict,
    #                      path_of_run_results_folder / f'CAP_bca_tool_vmt_weighted_def_cpm_{settings.start_time_readable}',
    #                      list(),
    #                      'vehicle', 'optionID', 'modelYearID')
    #     save_dict_to_csv(wtd_repair_cpm_dict,
    #                      path_of_run_results_folder / f'CAP_bca_tool_vmt_weighted_emission_repair_cpm_{settings.start_time_readable}',
    #                      list(),
    #                      'vehicle', 'optionID', 'modelYearID')
    #     save_dict_to_csv(wtd_cap_fuel_cpm_dict,
    #                      path_of_run_results_folder / f'CAP_bca_tool_vmt_weighted_fuel_cpm_{settings.start_time_readable}',
    #                      list(),
    #                      'vehicle', 'optionID', 'modelYearID')
    #
    #     # create figures
    #     arg_list = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
    #     CreateFigures(cap_pv_annualized_df, 'US Dollars', path_of_run_results_folder, 'CAP').create_figures(arg_list)
    #
    # if settings.calc_ghg:
    #     ghg_totals_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_fleet_totals_{settings.start_time_readable}.csv', index=False)
    #     ghg_averages_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_fleet_averages_{settings.start_time_readable}.csv', index=False)
    #     ghg_pv_annualized_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_annual_summary_{settings.start_time_readable}.csv', index=False)
    #
    #     # create figures
    #     arg_list = ['TechCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
    #     CreateFigures(ghg_pv_annualized_df, 'US Dollars', path_of_run_results_folder, 'GHG').create_figures(arg_list)
    #
    elapsed_time_outputs = time() - start_time_outputs
    end_time = time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    if settings.calc_cap_costs:
        cap_df = pd.DataFrame(settings.fleet_cap._dict).transpose()
        cols = [col for col in cap_df.columns if col not in settings.row_header_for_fleet_files]
        cap_df = pd.DataFrame(cap_df, columns=settings.row_header_for_fleet_files + cols)
        cap_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_{settings.start_time_readable}.csv', index=False)

        rc_sales_df = pd.DataFrame(settings.regclass_sales._dict).transpose()
        rc_sales_df.to_csv(path_of_run_results_folder / f'CAP_sales_and_costs_by_step_{settings.start_time_readable}.csv', index=False)

        rc_costs_df = pd.DataFrame(settings.regclass_costs._dict).transpose()
        rc_costs_df.to_csv(path_of_modified_inputs_folder / f'regclass_costs_{settings.start_time_readable}.csv', index=False)
        wtd_cap_fuel_df = pd.DataFrame(settings.wtd_cap_fuel_cpm_dict).transpose()
        wtd_def_df = pd.DataFrame(settings.wtd_def_cpm_dict).transpose()
        wtd_repair_df = pd.DataFrame(settings.wtd_repair_cpm_dict).transpose()

        wtd_cap_fuel_df.to_csv(path_of_run_results_folder / f'CAP_vmt_weighted_fuel_cpm_{settings.start_time_readable}.csv')
        wtd_def_df.to_csv(path_of_run_results_folder / f'CAP_vmt_weighted_def_cpm_{settings.start_time_readable}.csv')
        wtd_repair_df.to_csv(path_of_run_results_folder / f'CAP_vmt_weighted_repair_cpm_{settings.start_time_readable}.csv')

    if settings.calc_ghg_costs:
        ghg_df = pd.DataFrame(settings.fleet_ghg._dict).transpose()
        cols = [col for col in ghg_df.columns if col not in settings.row_header_for_fleet_files]
        ghg_df = pd.DataFrame(ghg_df, columns=settings.row_header_for_fleet_files + cols)
        ghg_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_{settings.start_time_readable}.csv', index=False)

        st_sales_df = pd.DataFrame(settings.sourcetype_sales._dict).transpose()
        st_sales_df.to_csv(path_of_run_results_folder / f'GHG_sales_and_costs_by_step_{settings.start_time_readable}.csv', index=False)

        wtd_ghg_fuel_df = pd.DataFrame(settings.wtd_cap_fuel_cpm_dict).transpose()
        wtd_ghg_fuel_df.to_csv(path_of_run_results_folder / f'GHG_vmt_weighted_fuel_cpm_{settings.start_time_readable}.csv')

    settings.fuel_prices.fuel_prices_in_analysis_dollars.to_csv(
        path_of_modified_inputs_folder / f'fuel_prices_{settings.general_inputs.get_attribute_value("aeo_fuel_price_case")}.csv')

    settings.def_prices.def_prices_in_analysis_dollars.to_csv(path_of_modified_inputs_folder / 'def_prices.csv')

    settings.deflators.deflators_and_adj_factors.to_csv(path_of_modified_inputs_folder / 'deflators.csv')

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder',
                                              'Calc CAP costs', 'Calc CAP pollution',
                                              'Calc GHG costs', 'Calc GHG pollution',
                                              'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time post-processing',
                                              'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [bca_tool_code.__version__, path_of_run_folder,
                                                 settings.calc_cap_costs, settings.calc_cap_pollution,
                                                 settings.calc_ghg_costs, settings.calc_ghg_pollution,
                                                 settings.start_time_readable, settings.elapsed_time_inputs,
                                                 elapsed_time_calcs, elapsed_time_postproc,
                                                 elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', '', '', '', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    # summary_log = pd.concat([summary_log, get_file_datetime(settings.input_files_pathlist)], axis=0, sort=False, ignore_index=True)
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)

    print(f'\nOutput files have been saved to {path_of_run_folder}\n')


if __name__ == '__main__':
    main()
