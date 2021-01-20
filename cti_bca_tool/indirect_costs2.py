import pandas as pd
from itertools import product


# create some dictionaries for storing data
scaled_markups_dict = dict()
project_markups_dict = dict()


def calc_project_markup_value(settings, vehicle, markup_factor, model_year):
    alt, rc, ft = vehicle
    scaled_markups_dict_id = ((vehicle), markup_factor, model_year)
    scaling_metric = settings.indirect_cost_scaling_metric
    if scaled_markups_dict_id in scaled_markups_dict:
        project_markup_value = scaled_markups_dict[scaled_markups_dict_id]
    else:
        input_markup_value, scaler, scaled_by = settings.markup_inputs_dict[(ft, markup_factor)]['Value'], \
                                                settings.markup_inputs_dict[(ft, markup_factor)]['Scaler'], \
                                                settings.markup_inputs_dict[(ft, markup_factor)]['Scaled_by']
        if scaler == 'Absolute':
            project_markup_value = \
                (settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)][f'{model_year}']
                 / settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)]['2024']) \
                * input_markup_value
        if scaler == 'Relative':
            project_markup_value = \
                (settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)][f'{model_year}']
                 / settings.required_miles_and_ages_dict[((vehicle), scaled_by, scaling_metric)][str(int(model_year) - 3)]) \
                * input_markup_value
        if scaler == 'None':
            project_markup_value = input_markup_value
        scaled_markups_dict[scaled_markups_dict_id] = project_markup_value
    return project_markup_value


def per_veh_project_markups(settings, vehicles):
    """
    This method is for use in testing to get an output CSV that shows the markups used within the project.
    :param settings:
    :param markup_factors:
    :param vehicles:
    :param scaling_dict:
    :param markups_dict:
    :return:
    """
    for vehicle, model_year in product(vehicles, settings.years):
        for markup_factor in settings.markup_factors:
            markup_value = calc_project_markup_value(settings, vehicle, markup_factor, model_year)
            if markup_factor == settings.markup_factors[0]:
                project_markups_dict[((vehicle), model_year)] = {markup_factor: markup_value}
            else:
                project_markups_dict[((vehicle), model_year)].update({markup_factor: markup_value})
    return project_markups_dict


def calc_per_veh_indirect_costs(settings, fleet_averages_dict):
    print('\nCalculating per vehicle indirect costs\n')

    for key in fleet_averages_dict.keys():
        alt, st, rc, ft = key[0]
        model_year, age = key[1], key[2]
        if age == 0:
            ic_sum = 0
            for markup_factor in settings.markup_factors:
                markup_value = calc_project_markup_value(settings, (alt, rc, ft), markup_factor, model_year)
                per_veh_direct_cost = fleet_averages_dict[key]['DirectCost_AvgPerVeh']
                fleet_averages_dict[key].update({f'{markup_factor}Cost_AvgPerVeh': markup_value * per_veh_direct_cost})
                ic_sum += markup_value * per_veh_direct_cost
            fleet_averages_dict[key].update({'IndirectCost_AvgPerVeh': ic_sum})
    return fleet_averages_dict


def calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict):
    print('\nCalculating total indirect costs.\n')
    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    markup_factors.append('Indirect')
    for key in fleet_totals_dict.keys():
        age = key[2]
        if age == 0:
            for markup_factor in markup_factors:
                cost_per_veh = fleet_averages_dict[key][f'{markup_factor}Cost_AvgPerVeh']
                sales = fleet_totals_dict[key]['VPOP']
                fleet_totals_dict[key].update({f'{markup_factor}Cost': cost_per_veh * sales})
    return fleet_totals_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
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
    save_dict_to_csv(per_veh_markups_by_year_df, settings.path_project / 'test/per_veh_markups_by_year', 'vehicle', 'modelYearID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
