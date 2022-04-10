"""
cti_bca_tool.tool_main.py

This is the main module of the tool.

"""
import pandas as pd
import shutil
from datetime import datetime
from time import time
import bca_tool_code
# from bca_tool_code.input_dict import InputFiles
# from bca_tool_code.general_inputs import GeneralInputs
from bca_tool_code.tool_setup import SetInputs, SetPaths
# from bca_tool_code.deflators import Deflators
# from bca_tool_code.fuel_prices import FuelPrices
# from bca_tool_code.regclass_costs import RegclassCosts
# from bca_tool_code.regclass_learningscalers import RegclassLearningScalers
# from bca_tool_code.project_fleet import create_fleet_df
# from bca_tool_code.fleet_totals_dict import FleetTotals
# from bca_tool_code.fleet_averages_dict import FleetAverages
from bca_tool_code.package_costs import calc_avg_package_cost_per_step, calc_package_costs_per_veh, calc_package_costs
from bca_tool_code.indirect_costs import calc_indirect_costs_per_veh, calc_indirect_costs
from bca_tool_code.tech_costs import calc_tech_costs_per_veh, calc_tech_costs
from bca_tool_code.def_costs import calc_def_costs_per_veh, calc_def_costs
from bca_tool_code.fuel_costs import calc_fuel_costs_per_veh, calc_fuel_costs_cap, calc_fuel_costs_ghg
from bca_tool_code.repair_costs import calc_emission_repair_costs_per_mile, calc_emission_repair_costs_per_veh, calc_emission_repair_costs
from bca_tool_code.emission_costs import calc_criteria_emission_costs
from bca_tool_code.sum_by_vehicle import calc_sum_of_costs
from bca_tool_code.discounting import discount_values
from bca_tool_code.annual_summary import AnnualSummary
from bca_tool_code.weighted_results import create_weighted_cost_dict
from bca_tool_code.calc_deltas import calc_deltas, calc_deltas_weighted
from bca_tool_code.vehicle import Vehicle
from bca_tool_code.figures import CreateFigures
from bca_tool_code.input_modules.general_functions import save_dict_to_csv, inputs_filenames, get_file_datetime


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
        calc_avg_package_cost_per_step(settings, settings.regclass_sales)
        calc_package_costs_per_veh(settings, settings.fleet_cap, settings.regclass_sales, 'Direct')
        calc_package_costs(settings, settings.fleet_cap, 'Direct', 'VPOP_withTech')

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
        calc_fuel_costs_cap(settings, settings.fleet_cap)
        calc_fuel_costs_per_veh(settings, settings.fleet_cap, 'VPOP_withTech', 'VMT_withTech')

        # calculate emission repair costs
        calc_emission_repair_costs_per_mile(settings)
        calc_emission_repair_costs_per_veh(settings)
        calc_emission_repair_costs(settings, 'VPOP_withTech')

        # sum attributes in the attributes_to_sum dictionary
        for summed_attribute, sum_attributes in settings.fleet_cap.attributes_to_sum.items():
            calc_sum_of_costs(settings, settings.fleet_cap, summed_attribute, *sum_attributes)

        # calc CAP pollution effects, if applicable
        if settings.calc_cap_pollution:
            calc_criteria_emission_costs(settings)

        create_weighted_cost_dict(settings, settings.wtd_def_cpm_dict, 'DEFCost_PerMile', 'VMT_PerVeh')
        create_weighted_cost_dict(settings, settings.wtd_repair_cpm_dict, 'EmissionRepairCost_PerMile', 'VMT_PerVeh')
        create_weighted_cost_dict(settings, settings.wtd_cap_fuel_cpm_dict, 'FuelCost_Retail_PerMile', 'VMT_PerVeh')

        discount_values(settings, settings.fleet_cap)

        # calc the annual summary, present values and annualized values (excluding cost/veh and cost/mile results)
        AnnualSummary.annual_summary(settings, settings.fleet_cap, settings.annual_summary_cap)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, settings.fleet_cap)
        settings.annual_summary_cap = calc_deltas(settings, settings.annual_summary_cap)

        settings.wtd_def_cpm_dict = calc_deltas_weighted(settings, settings.wtd_def_cpm_dict)
        settings.wtd_repair_cpm_dict = calc_deltas_weighted(settings, settings.wtd_repair_cpm_dict)
        settings.wtd_cap_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_cap_fuel_cpm_dict)

    if settings.calc_ghg_costs:

        # calculate package costs based on cumulative sales (learning is applied to cumulative sales)
        calc_avg_package_cost_per_step(settings, settings.sourcetype_sales)
        calc_package_costs_per_veh(settings, settings.fleet_ghg, settings.sourcetype_sales, 'Tech')
        calc_package_costs(settings, settings.fleet_ghg, 'Tech', 'VPOP')

        calc_fuel_costs_ghg(settings, settings.fleet_ghg)
        calc_fuel_costs_per_veh(settings, settings.fleet_ghg, 'VPOP', 'VMT')

        # sum attributes in the attributes_to_sum dictionary
        for summed_attribute, sum_attributes in settings.fleet_ghg.attributes_to_sum.items():
            calc_sum_of_costs(settings, settings.fleet_ghg, summed_attribute, *sum_attributes)

        # calc GHG pollution effects, if applicable
        if settings.calc_ghg_pollution:
            pass

        create_weighted_cost_dict(settings, settings.wtd_ghg_fuel_cpm_dict, 'FuelCost_Retail_PerMile', 'VMT_PerVeh')

        discount_values(settings, settings.fleet_ghg)

        # calc the annual summary, present values and annualized values (excluding cost/veh and cost/mile results)
        AnnualSummary.annual_summary(settings, settings.fleet_ghg, settings.annual_summary_ghg)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, settings.fleet_ghg)
        settings.annual_summary_ghg = calc_deltas(settings, settings.annual_summary_ghg)

        settings.wtd_ghg_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_ghg_fuel_cpm_dict)


        t = 0

    #
    # if settings.calc_ghg:
    #     # create project fleet DataFrame which will include adjustments to the MOVES input file that are unique to the project.
    #     ghg_fleet_df = create_fleet_df(settings, settings.moves_ghg, settings.options_ghg_dict,
    #                     settings.moves_adjustments_ghg_dict, 'VPOP')
    #
    #     # create totals, averages and sales by sourcetype dictionaries
    #     sourcetype_sales_dict, ghg_totals_dict, ghg_averages_dict = dict(), dict(), dict()
    #     ghg_totals_dict = FleetTotals(ghg_totals_dict).create_fleet_totals_dict(settings, ghg_fleet_df)
    #     ghg_averages_dict = FleetAverages(ghg_averages_dict).create_fleet_averages_dict(settings, ghg_fleet_df)
    #     sourcetype_sales_dict = FleetTotals(sourcetype_sales_dict).create_sourcetype_sales_dict(ghg_fleet_df)
    #
    #     # calculate tech costs per sourcetype based on cumulative sourcetype sales (learning is applied to cumulative sales)
    #     sourcetype_yoy_costs_per_step = calc_yoy_costs_per_step(settings, sourcetype_sales_dict, 'VPOP_withTech', 'GHG')
    #
    #     # calculate average (per vehicle) then total tech costs
    #     ghg_averages_dict = calc_per_veh_direct_costs(sourcetype_yoy_costs_per_step, settings.cost_steps_sourcetype, ghg_averages_dict, 'GHG')
    #     ghg_totals_dict = calc_direct_costs(ghg_totals_dict, ghg_averages_dict, 'VPOP', 'GHG')
    #
    #     # calculate total then average fuel costs
    #     ghg_totals_dict = calc_fuel_costs(settings, ghg_totals_dict, 'Gallons', 'GHG')
    #     ghg_averages_dict = calc_average_fuel_costs(ghg_totals_dict, ghg_averages_dict, 'VPOP', 'VMT')
    #
    #     # sum operating costs and operating-tech costs into a single key, value
    #     # the totals_dict here uses pre-tax fuel price since it serves as the basis for social costs
    #     # the averages_dict uses retail fuel prices since it serves as the basis for average operating costs which are relevant to owners
    #     ghg_totals_dict = calc_sum_of_costs(ghg_totals_dict, 'OperatingCost', 'FuelCost_Pretax')
    #     ghg_totals_dict = calc_sum_of_costs(ghg_totals_dict, 'TechAndOperatingCost', 'TechCost', 'OperatingCost')
    #     ghg_averages_dict = calc_sum_of_costs(ghg_averages_dict, 'OperatingCost_Owner_AvgPerVeh', 'FuelCost_Retail_AvgPerVeh')
    #
    #     # calc emission effects, if applicable
    #     if settings.calc_ghg_pollution_effects:
    #         pass
    #         # ghg_totals_dict = calc_ghg_emission_costs(settings, ghg_totals_dict)
    #
    #     # calculate some weighted (wtd) cost per mile (cpm) operating costs
    #     # wtd_ghg_fuel_cpm_dict = create_weighted_cost_dict(settings, ghg_averages_dict, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh')
    #
    #     # discount monetized values
    #     ghg_totals_dict = discount_values(settings, ghg_totals_dict, 'GHG', 'totals')
    #     ghg_averages_dict = discount_values(settings, ghg_averages_dict, 'GHG', 'averages')
    #
    #     # calc annual sums, present and annualized values
    #     ghg_pv_annualized_dict = pv_annualized(settings, ghg_totals_dict, 'GHG')
    #
    #     # calculate deltas relative to the passed no action alternative ID
    #     ghg_totals_dict = calc_deltas(settings, ghg_totals_dict)
    #     ghg_averages_dict = calc_deltas(settings, ghg_averages_dict)
    #     ghg_pv_annualized_dict = calc_deltas(settings, ghg_pv_annualized_dict)
    #
    #     # wtd_ghg_fuel_cpm_dict = calc_deltas_weighted(settings, wtd_ghg_fuel_cpm_dict, 'FuelCost_Retail_AvgPerMile')
    #
    elapsed_time_calcs = time.time() - start_time_calcs

    # determine run output paths
    if run_id == 'test':
        path_of_run_results_folder = set_paths.path_test
        path_of_run_results_folder.mkdir(exist_ok=True)
        path_of_run_folder = path_of_run_results_folder
    else:
        path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder \
            = set_paths.create_output_paths(settings.start_time_readable, run_id)

    start_time_postproc = time()
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

    cap_df = pd.DataFrame(settings.fleet_cap).tranpose()
    cap_df.to_csv(path_of_run_results_folder / 'results_cap.csv', index=False)
    rc_sales_df = pd.DataFrame(settings.regclass_sales).transpose()
    rc_sales_df.to_csv(path_of_run_results_folder / 'rc_sales.csv', index=False)

    ghg_df = pd.DataFrame(settings.fleet_ghg).transpose()
    ghg_df.to_csv(path_of_run_results_folder / 'results_ghg.csv', index=False)
    st_sales_df = pd.DataFrame(settings.sourcetype_sales).transpose()
    st_sales_df.to_csv(path_of_run_results_folder / 'st_sales.csv', index=False)

    # summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder',
    #                                           'Calc CAP costs', 'Calc CAP pollution',
    #                                           'Calc GHG costs', 'Calc GHG pollution',
    #                                           'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time post-processing',
    #                                           'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
    #                                  'Results': [bca_tool_code.__version__, path_of_run_folder,
    #                                              settings.calc_cap_costs, settings.calc_cap_pollution,
    #                                              settings.calc_ghg_costs, settings.calc_ghg_pollution,
    #                                              settings.start_time_readable, settings.elapsed_time_inputs,
    #                                              elapsed_time_calcs, elapsed_time_postproc,
    #                                              elapsed_time_outputs, end_time_readable, elapsed_time],
    #                                  'Units': ['', '', '', '', '', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    # summary_log = pd.concat([summary_log, get_file_datetime(settings.input_files_pathlist)], axis=0, sort=False, ignore_index=True)
    # summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)

    print(f'\nOutput files have been saved to {path_of_run_folder}\n')


if __name__ == '__main__':
    main()
