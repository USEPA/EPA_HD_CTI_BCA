import pandas as pd
from itertools import product


# create some dictionaries for storing data
scaled_markups_dict = dict()
project_markups_dict = dict()


def calc_project_markup_value(settings, vehicle, markup_factor, model_year):
    """This function calculates the project markup value for the markup_factor (Warranty, RnD, Other, Profit) passed.

    Parameters:
        settings: The SetInputs classs.\n
        vehicle: A tuple representing an alt_regclass_fueltype vehicle.\n
        markup_factor: A string representing the name of the project markup factor value to return.\n
        model_year: The model year of the passed vehicle.

    Returns:
        A single markup factor value to be used in the project having been adjusted in accordance with the proposed warranty and useful life
        changes and the Absolute/Relative scaling entries.

    Note:
        The project markup factor differs from the input markup factors by scaling where that scaling is done based on the "Absolute" or "Relative"
        entries in the input file and by the Miles or Age entries of the warranty/useful life input files. Whether Miles or Age is used is set
        via the BCA_General_Inputs file.

    """
    alt, rc, ft = vehicle
    scaled_markups_dict_id = (vehicle, markup_factor, model_year)
    scaling_metric = settings.indirect_cost_scaling_metric
    if scaled_markups_dict_id in scaled_markups_dict:
        project_markup_value = scaled_markups_dict[scaled_markups_dict_id]
    else:
        input_markup_value, scaler, scaled_by, num_years = settings.markup_inputs_dict[(ft, markup_factor)]['Value'], \
                                                           settings.markup_inputs_dict[(ft, markup_factor)]['Scaler'], \
                                                           settings.markup_inputs_dict[(ft, markup_factor)]['Scaled_by'], \
                                                           settings.markup_inputs_dict[(ft, markup_factor)]['NumberOfYears']
        if scaler == 'Absolute':
            project_markup_value = \
                (settings.required_miles_and_ages_dict[(vehicle, scaled_by, scaling_metric)][f'{model_year}']
                 / settings.required_miles_and_ages_dict[(vehicle, scaled_by, scaling_metric)]['2024']) \
                * input_markup_value
        if scaler == 'Relative':
            project_markup_value = \
                (settings.required_miles_and_ages_dict[(vehicle, scaled_by, scaling_metric)][f'{model_year}']
                 / settings.required_miles_and_ages_dict[(vehicle, scaled_by, scaling_metric)][str(int(model_year) - int(num_years))]) \
                * input_markup_value
        if scaler == 'None':
            project_markup_value = input_markup_value
        scaled_markups_dict[scaled_markups_dict_id] = project_markup_value
    return project_markup_value


def per_veh_project_markups(settings, vehicles):
    """This function is used for testing to allow for output of the project markup values.

    Parameters:
        settings: The SetInputs class.\n
        vehicles: A list of tuples representing alt_regclass_fueltype vehicles.

    Returns:
        A dictionary of project markup values.

    """
    for vehicle, model_year in product(vehicles, settings.years):
        for markup_factor in settings.markup_factors:
            markup_value = calc_project_markup_value(settings, vehicle, markup_factor, model_year)
            if markup_factor == settings.markup_factors[0]:
                project_markups_dict[(vehicle, model_year)] = {markup_factor: markup_value}
            else:
                project_markups_dict[(vehicle, model_year)].update({markup_factor: markup_value})
    return project_markups_dict


def calc_per_veh_indirect_costs(settings, averages_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        averages_dict: A dictionary containing tech package direct costs/vehicle.

    Returns:
        The averages_dict dictionary updated with indirect costs associated with each markup value along with the summation of those individual indirect
        costs as "IndirectCost_AvgPerVeh."

    """
    print('\nCalculating per vehicle indirect costs\n')

    for key in averages_dict.keys():
        vehicle, model_year, age_id, disc_rate = key
        alt, st, rc, ft = vehicle
        if age_id == 0:
            print(f'Calculating per vehicle direct costs for {vehicle}, MY {model_year}.')
            ic_sum = 0
            for markup_factor in settings.markup_factors:
                markup_value = calc_project_markup_value(settings, (alt, rc, ft), markup_factor, model_year)
                per_veh_direct_cost = averages_dict[key]['DirectCost_AvgPerVeh']
                averages_dict[key].update({f'{markup_factor}Cost_AvgPerVeh': markup_value * per_veh_direct_cost})
                ic_sum += markup_value * per_veh_direct_cost
            averages_dict[key].update({'IndirectCost_AvgPerVeh': ic_sum})
    return averages_dict


def calc_indirect_costs(settings, totals_dict, averages_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: A dictionary containing sales (VPOP at age=0) and into which tech package indirect costs will be updated.\n
        averages_dict: A dictionary containing individual indirect costs per vehicle.

    Returns:
        The totals_dict dictionary updated with total indirect costs for each individual indirect cost property and a summation of those.

    """
    print('\nCalculating total indirect costs.\n')
    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    markup_factors.append('Indirect')
    for key in totals_dict.keys():
        vehicle, model_year, age_id, disc_rate = key
        if age_id == 0:
            for markup_factor in markup_factors:
                cost_per_veh = averages_dict[key][f'{markup_factor}Cost_AvgPerVeh']
                sales = totals_dict[key]['VPOP']
                totals_dict[key].update({f'{markup_factor}Cost': cost_per_veh * sales})
    return totals_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    per_veh_markups_by_year_dict = per_veh_project_markups(settings, vehicles_rc)

    per_veh_markups_by_year_df = pd.DataFrame(per_veh_markups_by_year_dict)

    # create project fleet data structures, both a DataFrame and a dictionary of regclass based sales
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

    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)

    # save dicts to csv
    save_dict_to_csv(per_veh_markups_by_year_df, settings.path_test / 'per_veh_markups_by_year', 'vehicle', 'modelYearID')
    # save_dict_to_csv(fleet_averages_dict, settings.path_test / 'fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    # save_dict_to_csv(fleet_totals_dict, settings.path_test / 'fleet_totals', 'vehicle', 'modelYearID', 'ageID')
