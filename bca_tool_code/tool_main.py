"""
cti_bca_tool.tool_main.py

This is the main module of the tool.

"""
import pandas as pd
import shutil
from datetime import datetime
import time
import bca_tool_code
from bca_tool_code.tool_setup import SetInputs, SetPaths
from bca_tool_code.project_fleet import create_fleet_df # create_cap_fleet_df, create_ghg_fleet_df
from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages
from bca_tool_code.direct_costs import calc_yoy_costs_per_step, calc_per_veh_direct_costs, calc_direct_costs
from bca_tool_code.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs
from bca_tool_code.tech_costs import calc_per_veh_tech_costs, calc_tech_costs
from bca_tool_code.def_costs import calc_def_costs, calc_average_def_costs
from bca_tool_code.fuel_costs import calc_fuel_costs, calc_average_fuel_costs
from bca_tool_code.repair_costs import calc_emission_repair_costs_per_mile, calc_per_veh_emission_repair_costs, calc_emission_repair_costs
from bca_tool_code.emission_costs import calc_criteria_emission_costs
from bca_tool_code.sum_by_vehicle import calc_sum_of_costs
from bca_tool_code.discounting import discount_values
from bca_tool_code.pv_annualized_dicts import pv_annualized
from bca_tool_code.weighted_results import create_weighted_cost_dict
from bca_tool_code.calc_deltas import calc_deltas, calc_deltas_weighted
from bca_tool_code.vehicle import Vehicle
from bca_tool_code.figures import CreateFigures
# from bca_tool_code.tool_postproc import create_output_paths
from bca_tool_code.general_functions import save_dict_to_csv, inputs_filenames, get_file_datetime


def main():
    """

    Returns:
        The results of the current run of the tool.

    """
    start_time_calcs = time.time()
    set_paths = SetPaths()
    run_id = set_paths.run_id()
    settings = SetInputs()

    print("\nDoing the work...\n")

    if settings.calc_cap:
        # create project fleet DataFrame which will include adjustments to the MOVES input file that are unique to the project.
        cap_fleet_df = create_fleet_df(settings, settings.moves_cap, settings.options_cap_dict,
                                       settings.moves_adjustments_cap_dict, 'VPOP', 'VMT', 'Gallons')
        # cap_fleet_df = create_cap_fleet_df(settings, settings.moves_cap, 'VPOP', 'VMT', 'Gallons')

        # create a sales (by regclass) and fleet dictionaries
        cap_totals_dict, cap_averages_dict, regclass_sales_dict = dict(), dict(), dict()
        cap_totals_dict = FleetTotals(cap_totals_dict).create_fleet_totals_dict(settings, cap_fleet_df)
        cap_averages_dict = FleetAverages(cap_averages_dict).create_fleet_averages_dict(settings, cap_fleet_df)
        # cap_totals_dict = FleetTotalsCAP(cap_totals_dict).create_fleet_totals_dict(settings, cap_fleet_df)
        # cap_averages_dict = FleetAveragesCAP(cap_averages_dict).create_fleet_averages_dict(settings, cap_fleet_df)
        regclass_sales_dict = FleetTotals(regclass_sales_dict).create_regclass_sales_dict(cap_fleet_df)

        # calculate direct costs per reg class based on cumulative regclass sales (learning is applied to cumulative sales)
        # regclass_yoy_costs_per_step = calc_yoy_costs_per_step(settings, cap_totals_dict, 'VPOP_withTech', 'CAP')
        regclass_yoy_costs_per_step = calc_yoy_costs_per_step(settings, regclass_sales_dict, 'VPOP_withTech', 'CAP')

        # calculate total direct costs and then per vehicle costs (per sourcetype)
        cap_averages_dict = calc_per_veh_direct_costs(regclass_yoy_costs_per_step, settings.cost_steps_regclass, cap_averages_dict, 'CAP')
        cap_totals_dict = calc_direct_costs(cap_totals_dict, cap_averages_dict, 'VPOP_withTech', 'CAP')

        # calculate indirect costs per vehicle and then total indirect costs (note that GHG program costs include indirect costs)
        cap_averages_dict = calc_per_veh_indirect_costs(settings, cap_averages_dict)
        cap_totals_dict = calc_indirect_costs(settings, cap_totals_dict, cap_averages_dict, 'VPOP_withTech')

        # calculate tech costs per vehicle and total tech costs
        cap_averages_dict = calc_per_veh_tech_costs(cap_averages_dict)
        cap_totals_dict = calc_tech_costs(cap_totals_dict, cap_averages_dict, 'VPOP_withTech')

        # calculate DEF costs
        cap_totals_dict = calc_def_costs(settings, cap_totals_dict, 'Gallons_withTech')
        cap_averages_dict = calc_average_def_costs(cap_totals_dict, cap_averages_dict, 'VPOP_withTech')

        # calculate fuel costs, including adjustments for fuel consumption associated with ORVR
        cap_totals_dict = calc_fuel_costs(settings, cap_totals_dict, 'Gallons_withTech', 'CAP')
        cap_averages_dict = calc_average_fuel_costs(cap_totals_dict, cap_averages_dict, 'VPOP_withTech', 'VMT_withTech')

        # calculate emission repair costs
        cap_averages_dict, repair_cpm_dict, estimated_ages_dict = calc_emission_repair_costs_per_mile(settings, cap_averages_dict)
        cap_averages_dict = calc_per_veh_emission_repair_costs(cap_averages_dict)
        cap_totals_dict = calc_emission_repair_costs(cap_totals_dict, cap_averages_dict, 'VPOP_withTech')

        # sum operating costs and operating-tech costs into a single key, value
        # the totals_dict here uses pre-tax fuel price since it serves as the basis for social costs
        # the averages_dict uses retail fuel prices since it serves as the basis for average operating costs which are relevant to owners
        cap_totals_dict = calc_sum_of_costs(cap_totals_dict, 'OperatingCost', 'DEFCost', 'FuelCost_Pretax', 'EmissionRepairCost')
        cap_totals_dict = calc_sum_of_costs(cap_totals_dict, 'TechAndOperatingCost', 'TechCost', 'OperatingCost')
        cap_averages_dict = calc_sum_of_costs(cap_averages_dict,
                                              'OperatingCost_Owner_AvgPerMile',
                                              'DEFCost_AvgPerMile', 'FuelCost_Retail_AvgPerMile', 'EmissionRepairCost_AvgPerMile')
        cap_averages_dict = calc_sum_of_costs(cap_averages_dict,
                                              'OperatingCost_Owner_AvgPerVeh',
                                              'DEFCost_AvgPerVeh', 'FuelCost_Retail_AvgPerVeh', 'EmissionRepairCost_AvgPerVeh')

        if settings.calc_cap_pollution_effects:
            cap_totals_dict = calc_criteria_emission_costs(settings, cap_totals_dict)

        # calculate some weighted (wtd) cost per mile (cpm) operating costs
        wtd_def_cpm_dict = create_weighted_cost_dict(settings, cap_averages_dict, 'DEFCost_AvgPerMile', 'VMT_AvgPerVeh')
        wtd_repair_cpm_dict = create_weighted_cost_dict(settings, cap_averages_dict, 'EmissionRepairCost_AvgPerMile', 'VMT_AvgPerVeh')
        wtd_cap_fuel_cpm_dict = create_weighted_cost_dict(settings, cap_averages_dict, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh')

        # discount monetized values; if calculating emission costs, the discount rates entered in the BCA_General_Inputs workbook should be consistent with the
        # criteria cost factors in that input workbook
        cap_totals_dict = discount_values(settings, cap_totals_dict, 'CAP', 'totals')
        cap_averages_dict = discount_values(settings, cap_averages_dict, 'CAP', 'averages')

        cap_pv_annualized_dict = pv_annualized(settings, cap_totals_dict, 'CAP')

        # calculate deltas relative to the passed no action alternative ID
        cap_totals_dict = calc_deltas(settings, cap_totals_dict)
        cap_averages_dict = calc_deltas(settings, cap_averages_dict)
        cap_pv_annualized_dict = calc_deltas(settings, cap_pv_annualized_dict)

        wtd_def_cpm_dict = calc_deltas_weighted(settings, wtd_def_cpm_dict)
        wtd_repair_cpm_dict = calc_deltas_weighted(settings, wtd_repair_cpm_dict)
        wtd_cap_fuel_cpm_dict = calc_deltas_weighted(settings, wtd_cap_fuel_cpm_dict)

    if settings.calc_ghg:
        # create project fleet DataFrame which will include adjustments to the MOVES input file that are unique to the project.
        ghg_fleet_df = create_fleet_df(settings, settings.moves_ghg, settings.options_ghg_dict,
                        settings.moves_adjustments_ghg_dict, 'VPOP')
        # ghg_fleet_df = create_fleet_df(settings, settings.moves_ghg)
        
        # create a sales (by sourcetype) and fleet dictionaries
        sourcetype_sales_dict, ghg_totals_dict, ghg_averages_dict = dict(), dict(), dict()
        ghg_totals_dict = FleetTotals(ghg_totals_dict).create_fleet_totals_dict(settings, ghg_fleet_df)
        ghg_averages_dict = FleetAverages(ghg_averages_dict).create_fleet_averages_dict(settings, ghg_fleet_df)
        sourcetype_sales_dict = FleetTotals(sourcetype_sales_dict).create_sourcetype_sales_dict(ghg_fleet_df)
        # sourcetype_sales_dict = SourcetypeSales(sourcetype_sales_dict).create_sourcetype_sales_dict(ghg_fleet_df)
        # ghg_totals_dict = FleetTotalsGHG(ghg_totals_dict).create_fleet_totals_dict(settings, ghg_fleet_df)
        # ghg_averages_dict = FleetAveragesGHG(ghg_averages_dict).create_fleet_averages_dict(settings, ghg_fleet_df)

        # calculate direct costs per sourcetype based on cumulative sourcetype sales (learning is applied to cumulative sales)
        sourcetype_yoy_costs_per_step = calc_yoy_costs_per_step(settings, sourcetype_sales_dict, 'VPOP_withTech', 'GHG')
        # sourcetype_yoy_costs_per_step = calc_yoy_costs_per_step(settings, sourcetype_sales_dict, 'VPOP_AddingTech')

        # calculate total direct costs and then per vehicle costs (per sourcetype)
        ghg_averages_dict = calc_per_veh_direct_costs(sourcetype_yoy_costs_per_step, settings.cost_steps_sourcetype, ghg_averages_dict, 'GHG')
        ghg_totals_dict = calc_direct_costs(ghg_totals_dict, ghg_averages_dict, 'VPOP', 'GHG')

        # calculate fuel costs
        ghg_totals_dict = calc_fuel_costs(settings, ghg_totals_dict, 'Gallons', 'GHG')
        ghg_averages_dict = calc_average_fuel_costs(ghg_totals_dict, ghg_averages_dict, 'VPOP', 'VMT')

        # sum operating costs and operating-tech costs into a single key, value
        # the totals_dict here uses pre-tax fuel price since it serves as the basis for social costs
        # the averages_dict uses retail fuel prices since it serves as the basis for average operating costs which are relevant to owners
        ghg_totals_dict = calc_sum_of_costs(ghg_totals_dict, 'OperatingCost', 'FuelCost_Pretax')
        ghg_totals_dict = calc_sum_of_costs(ghg_totals_dict, 'TechAndOperatingCost', 'TechCost', 'OperatingCost')
        ghg_averages_dict = calc_sum_of_costs(ghg_averages_dict, 'OperatingCost_Owner_AvgPerVeh', 'FuelCost_Retail_AvgPerVeh')

        if settings.calc_ghg_pollution_effects:
            pass
            # ghg_totals_dict = calc_ghg_emission_costs(settings, ghg_totals_dict)

        # calculate some weighted (wtd) cost per mile (cpm) operating costs
        # wtd_ghg_fuel_cpm_dict = create_weighted_cost_dict(settings, ghg_averages_dict, 'FuelCost_Retail_AvgPerMile', 'VMT_AvgPerVeh')

        # discount monetized values
        ghg_totals_dict = discount_values(settings, ghg_totals_dict, 'GHG', 'totals')
        ghg_averages_dict = discount_values(settings, ghg_averages_dict, 'GHG', 'averages')

        ghg_pv_annualized_dict = pv_annualized(settings, ghg_totals_dict, 'GHG')

        # calculate deltas relative to the passed no action alternative ID
        ghg_totals_dict = calc_deltas(settings, ghg_totals_dict)
        ghg_averages_dict = calc_deltas(settings, ghg_averages_dict)
        ghg_pv_annualized_dict = calc_deltas(settings, ghg_pv_annualized_dict)

        # wtd_ghg_fuel_cpm_dict = calc_deltas_weighted(settings, wtd_ghg_fuel_cpm_dict, 'FuelCost_Retail_AvgPerMile')

    elapsed_time_calcs = time.time() - start_time_calcs

    # determine run output paths
    if run_id == 'test':
        path_of_run_results_folder = set_paths.path_test
        path_of_run_results_folder.mkdir(exist_ok=True)
        path_of_run_folder = path_of_run_results_folder
    else:
        path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder \
            = set_paths.create_output_paths(settings.start_time_readable, run_id)

    start_time_postproc = time.time()

    # pass dicts thru the vehicle_name function to add some identifiers and then
    # do the post-processing to generate an annual summary and some figures
    if settings.calc_cap:
        # add identifier attributes
        cap_totals_dict = Vehicle().vehicle_name(settings, settings.options_cap_dict, cap_totals_dict)
        cap_averages_dict = Vehicle().vehicle_name(settings, settings.options_cap_dict, cap_averages_dict)
        cap_pv_annualized_dict = Vehicle().option_name(settings, settings.options_cap_dict, cap_pv_annualized_dict)

        # rearrange columns for better presentation
        cap_totals_df = pd.DataFrame(cap_totals_dict).transpose()
        cols = [col for col in cap_totals_df.columns if col not in settings.row_header_for_fleet_files]
        cap_totals_df = pd.DataFrame(cap_totals_df, columns=settings.row_header_for_fleet_files + cols)

        cap_averages_df = pd.DataFrame(cap_averages_dict).transpose()
        cols = [col for col in cap_averages_df.columns if col not in settings.row_header_for_fleet_files]
        cap_averages_df = pd.DataFrame(cap_averages_df, columns=settings.row_header_for_fleet_files + cols)

        cap_pv_annualized_df = pd.DataFrame(cap_pv_annualized_dict).transpose()
        cols = [col for col in cap_pv_annualized_df.columns if col not in settings.row_header_for_annual_summary_files]
        cap_pv_annualized_df = pd.DataFrame(cap_pv_annualized_df, columns=settings.row_header_for_annual_summary_files + cols)
        
    if settings.calc_ghg:
        # add identifier attributes
        ghg_totals_dict = Vehicle().vehicle_name(settings, settings.options_ghg_dict, ghg_totals_dict)
        ghg_averages_dict = Vehicle().vehicle_name(settings, settings.options_ghg_dict, ghg_averages_dict)
        ghg_pv_annualized_dict = Vehicle().option_name(settings, settings.options_ghg_dict, ghg_pv_annualized_dict)

        # rearrange columns for better presentation
        ghg_totals_df = pd.DataFrame(ghg_totals_dict).transpose()
        cols = [col for col in ghg_totals_df.columns if col not in settings.row_header_for_fleet_files]
        ghg_totals_df = pd.DataFrame(ghg_totals_df, columns=settings.row_header_for_fleet_files + cols)

        ghg_averages_df = pd.DataFrame(ghg_averages_dict).transpose()
        cols = [col for col in ghg_averages_df.columns if col not in settings.row_header_for_fleet_files]
        ghg_averages_df = pd.DataFrame(ghg_averages_df, columns=settings.row_header_for_fleet_files + cols)

        ghg_pv_annualized_df = pd.DataFrame(ghg_pv_annualized_dict).transpose()
        cols = [col for col in ghg_pv_annualized_df.columns if col not in settings.row_header_for_annual_summary_files]
        ghg_pv_annualized_df = pd.DataFrame(ghg_pv_annualized_df, columns=settings.row_header_for_annual_summary_files + cols)

    elapsed_time_postproc = time.time() - start_time_postproc

    start_time_outputs = time.time()

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
        for file in set_paths.files_in_code_folder():
            try:
                shutil.copy2(file, path_of_code_folder / file.name)
            except:
                print('\nUnable to copy Python code to run results folder when using the executable.\n')
        settings.fuel_prices.to_csv(path_of_modified_inputs_folder / f'fuel_prices_{settings.aeo_case}.csv', index=False)
        settings.regclass_costs.to_csv(path_of_modified_inputs_folder / 'regclass_costs.csv', index=False)
        settings.sourcetype_costs.to_csv(path_of_modified_inputs_folder / 'sourcetype_costs.csv', index=False)
        settings.repair_and_maintenance.to_csv(path_of_modified_inputs_folder / 'repair_and_maintenance.csv')
        settings.def_prices.to_csv(path_of_modified_inputs_folder / 'def_prices.csv', index=False)
        gdp_deflators = pd.DataFrame(settings.gdp_deflators)  # from dict to df
        gdp_deflators.to_csv(path_of_modified_inputs_folder / 'gdp_deflators.csv', index=True)

    # save dictionaries to csv and also add some identifying info using the vehicle_name function
    print("\nSaving the output files...\n")

    if settings.calc_cap:
        cap_totals_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_fleet_totals_{settings.start_time_readable}.csv', index=False)
        cap_averages_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_fleet_averages_{settings.start_time_readable}.csv', index=False)
        cap_pv_annualized_df.to_csv(path_of_run_results_folder / f'CAP_bca_tool_annual_summary_{settings.start_time_readable}.csv', index=False)

        save_dict_to_csv(Vehicle().vehicle_name(settings, settings.options_cap_dict, estimated_ages_dict),
                         path_of_run_results_folder / f'CAP_bca_tool_estimated_ages_{settings.start_time_readable}',
                         list(),
                         'vehicle', 'optionID', 'modelYearID', 'identifier')
        save_dict_to_csv(Vehicle().vehicle_name(settings, settings.options_cap_dict, repair_cpm_dict),
                         path_of_run_results_folder / f'CAP_bca_tool_repair_cpm_details_{settings.start_time_readable}',
                         list(),
                         'vehicle', 'optionID', 'modelYearID', 'ageID', 'DiscountRate')

        save_dict_to_csv(wtd_def_cpm_dict,
                         path_of_run_results_folder / f'CAP_bca_tool_vmt_weighted_def_cpm_{settings.start_time_readable}',
                         list(),
                         'vehicle', 'optionID', 'modelYearID')
        save_dict_to_csv(wtd_repair_cpm_dict,
                         path_of_run_results_folder / f'CAP_bca_tool_vmt_weighted_emission_repair_cpm_{settings.start_time_readable}',
                         list(),
                         'vehicle', 'optionID', 'modelYearID')
        save_dict_to_csv(wtd_cap_fuel_cpm_dict,
                         path_of_run_results_folder / f'CAP_bca_tool_vmt_weighted_fuel_cpm_{settings.start_time_readable}',
                         list(),
                         'vehicle', 'optionID', 'modelYearID')

        # create figures
        arg_list = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
        CreateFigures(cap_pv_annualized_df, 'US Dollars', path_of_run_results_folder, 'CAP').create_figures(arg_list)

    if settings.calc_ghg:
        ghg_totals_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_fleet_totals_{settings.start_time_readable}.csv', index=False)
        ghg_averages_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_fleet_averages_{settings.start_time_readable}.csv', index=False)
        ghg_pv_annualized_df.to_csv(path_of_run_results_folder / f'GHG_bca_tool_annual_summary_{settings.start_time_readable}.csv', index=False)

        # create figures
        arg_list = ['TechCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
        CreateFigures(ghg_pv_annualized_df, 'US Dollars', path_of_run_results_folder, 'GHG').create_figures(arg_list)

    elapsed_time_outputs = time.time() - start_time_outputs
    end_time = time.time()
    end_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    elapsed_time = end_time - settings.start_time

    summary_log = pd.DataFrame(data={'Item': ['Version', 'Run folder',
                                              'Calc CAP costs', 'Calc CAP pollution',
                                              'Calc GHG costs', 'Calc GHG pollution',
                                              'Start of run', 'Elapsed time read inputs', 'Elapsed time calculations', 'Elapsed time post-processing',
                                              'Elapsed time save outputs', 'End of run', 'Elapsed runtime'],
                                     'Results': [bca_tool_code.__version__, path_of_run_folder,
                                                 settings.calc_cap_value, settings.calc_cap_pollution_effects_value,
                                                 settings.calc_ghg_value, settings.calc_ghg_pollution_effects_value,
                                                 settings.start_time_readable, settings.elapsed_time_read, elapsed_time_calcs, elapsed_time_postproc,
                                                 elapsed_time_outputs, end_time_readable, elapsed_time],
                                     'Units': ['', '', '', '', '', '', 'YYYYmmdd-HHMMSS', 'seconds', 'seconds', 'seconds', 'seconds', 'YYYYmmdd-HHMMSS', 'seconds']})
    summary_log = pd.concat([summary_log, get_file_datetime(settings.input_files_pathlist)], axis=0, sort=False, ignore_index=True)

    # add summary log to document_tables_file for tracking this file which is the most likely to be shared
    # if settings.generate_post_processing_files:
    #     if settings.calc_cap:
    #         summary_log.to_excel(document_cap_tables_file, sheet_name='summary_log', index=False)
    #         document_cap_tables_file.save()
    #     if settings.calc_ghg:
    #         summary_log.to_excel(document_ghg_tables_file, sheet_name='summary_log', index=False)
    #         document_ghg_tables_file.save()
    summary_log.to_csv(path_of_run_results_folder.joinpath('summary_log.csv'), index=False)
    print(f'\nOutput files have been saved to {path_of_run_folder}\n')


if __name__ == '__main__':
    main()
