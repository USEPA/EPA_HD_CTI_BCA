import pandas as pd
from itertools import product


# create some dictionaries for storing data
scaled_markups_dict = dict()
project_markups_dict = dict()
per_veh_indirect_costs = dict()
sales_dict = dict()


def create_markup_scaling_dict(settings, warranty_id, usefullife_id):
    df_all = pd.DataFrame()
    df1 = settings.warranty_inputs.copy()
    df2 = settings.usefullife_inputs.copy()
    df1.insert(0, 'identifier', f'{warranty_id}')
    df2.insert(0, 'identifier', f'{usefullife_id}')
    for df in [df1, df2]:
        df = pd.DataFrame(df.loc[df['period'] == settings.indirect_cost_scaling_metric]).reset_index(drop=True)
        df.insert(0, 'alt_rc_ft', pd.Series(zip(df['optionID'], df['regClassID'], df['fuelTypeID'])))
        df.insert(0, 'id', pd.Series(zip(df['alt_rc_ft'], df['identifier'])))
        df = df[['id'] + [col for col in df.columns if '20' in col]]
        df_all = pd.concat([df_all, df], axis=0, ignore_index=True)
    df_all.set_index('id', inplace=True)
    dict_return = df_all.to_dict('index')
    return dict_return


def calc_project_markup_value(settings, vehicle, markup_factor, model_year, scaling_dict):
    alt, rc, ft = vehicle
    scaled_markups_dict_id = ((vehicle), markup_factor, model_year)
    if scaled_markups_dict_id in scaled_markups_dict:
        project_markup_value = scaled_markups_dict[scaled_markups_dict_id]
    else:
        input_markup_value, scaler, scaled_by = settings.markup_inputs_dict[(ft, markup_factor)]['Value'], \
                                                settings.markup_inputs_dict[(ft, markup_factor)]['Scaler'], \
                                                settings.markup_inputs_dict[(ft, markup_factor)]['Scaled_by']
        if scaler == 'Absolute':
            project_markup_value = \
                (scaling_dict[((vehicle), scaled_by)][f'{model_year}'] / scaling_dict[((vehicle), scaled_by)]['2024']) \
                * input_markup_value
        if scaler == 'Relative':
            project_markup_value = \
                (scaling_dict[((vehicle), scaled_by)][f'{model_year}'] / scaling_dict[((vehicle), scaled_by)][str(int(model_year)-3)]) \
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
    scaling_dict = create_markup_scaling_dict(settings, 'Warranty', 'Usefullife')

    for vehicle, model_year in product(vehicles, settings.years):
        for markup_factor in settings.markup_factors:
            markup_value = calc_project_markup_value(settings, vehicle, markup_factor, model_year, scaling_dict)
            if markup_factor == settings.markup_factors[0]:
                project_markups_dict[((vehicle), model_year)] = {markup_factor: markup_value}
            else:
                project_markups_dict[((vehicle), model_year)].update({markup_factor: markup_value})
    return project_markups_dict


def calc_per_veh_indirect_costs(settings, vehicles, direct_costs_dict):
    print('\nCalculating per vehicle indirect costs\n')
    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    # markups_dict = create_markup_inputs_dict(settings.markups)
    scaling_dict = create_markup_scaling_dict(settings, 'Warranty', 'Usefullife')

    for vehicle, model_year in product(vehicles, settings.years):
        ic_sum = 0
        for markup_factor in settings.markup_factors:
            markup_value = calc_project_markup_value(settings, vehicle, markup_factor, model_year, scaling_dict)
            per_veh_direct_cost = direct_costs_dict[((vehicle, model_year))]['DirectCost_AvgPerVeh']
            if markup_factor == settings.markup_factors[0]:
                per_veh_indirect_costs[((vehicle), model_year)] = {f'{markup_factor}Cost_AvgPerVeh': markup_value * per_veh_direct_cost}
            else:
                per_veh_indirect_costs[((vehicle), model_year)].update({f'{markup_factor}Cost_AvgPerVeh': markup_value * per_veh_direct_cost})
            ic_sum += markup_value * per_veh_direct_cost
        per_veh_indirect_costs[((vehicle), model_year)].update({'IndirectCost_AvgPerVeh': ic_sum})
    return per_veh_indirect_costs


def calc_indirect_costs(settings, vehicles, costs_by_year_dict, fleet_dict):
    print('\nCalculating total indirect costs.\n')
    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    markup_factors.append('Indirect')
    for vehicle, year in product(vehicles, settings.years):
        for markup_factor in markup_factors:
            alt, st, rc, ft = vehicle
            rc_vehicle = (alt, rc, ft)
            cost_per_veh = costs_by_year_dict[((rc_vehicle), year)][f'{markup_factor}Cost_AvgPerVeh']
            sales_dict_id = ((vehicle), year, 0)
            if sales_dict_id in sales_dict:
                sales = sales_dict[sales_dict_id]
            else:
                sales = fleet_dict[((vehicle), year, 0)]['VPOP']
            fleet_dict[((vehicle), year, 0)].update({f'{markup_factor}Cost': cost_per_veh * sales})
    return fleet_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict
    from cti_bca_tool.direct_costs2 import calc_per_veh_direct_costs, calc_direct_costs
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    per_veh_markups_by_year_dict = per_veh_project_markups(settings, vehicles_rc)

    per_veh_markups_by_year_df = pd.DataFrame(per_veh_markups_by_year_dict)

    project_regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    per_veh_dc_by_year_dict = calc_per_veh_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]
    per_veh_ic_by_year_dict = calc_per_veh_indirect_costs(settings, vehicles_rc, per_veh_dc_by_year_dict)
    per_veh_indirect_costs_df = pd.DataFrame(per_veh_ic_by_year_dict)

    fleet_dict = create_fleet_totals_dict(project_fleet_df)
    vehicles_st = sourcetype_vehicles(project_fleet_df)
    fleet_dict = calc_direct_costs(settings, vehicles_st, per_veh_dc_by_year_dict, fleet_dict)
    fleet_dict = calc_indirect_costs(settings, vehicles_st, per_veh_ic_by_year_dict, fleet_dict)

    # save dicts to csv
    save_dict_to_csv(per_veh_markups_by_year_df, settings.path_project / 'test/per_veh_markups_by_year', 'vehicle', 'modelYearID')
    save_dict_to_csv(per_veh_indirect_costs_df, settings.path_project / 'test/per_veh_indirect_costs_by_year', 'vehicle', 'modelYearID')
    save_dict_to_csv(fleet_dict, settings.path_project / 'test/fleet_totals', 'vehicle', 'modelYearID', 'ageID')
