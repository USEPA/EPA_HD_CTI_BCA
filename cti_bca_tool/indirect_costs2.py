import pandas as pd
import attr
from itertools import product
# from cti_bca_tool.project_classes import Moves, WarrantyAndUsefullife
from cti_bca_tool import project_fleet


scaled_markups_dict = dict()
project_markups_dict = dict()


def create_scaling_dict(warranty_df, warranty_id, usefullife_df, usefullife_id, settings):
    df_all = pd.DataFrame()
    df1 = warranty_df.copy()
    df2 = usefullife_df.copy()
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


def create_markup_inputs_dict(df):
    """

    :param df: A DataFrame of the indirect cost markup factors and values by option and fueltype.
    :return: A dictionary with 'fueltype, markup factor' keys and 'markup value' values.
    """
    project_markups = df.copy()
    # insert a unique id to use as a dictionary key
    project_markups.insert(0, 'id', pd.Series(zip(project_markups['fuelTypeID'], project_markups['Markup_Factor'])))
    project_markups.set_index('id', inplace=True)
    project_markups.drop(columns=['fuelTypeID', 'Markup_Factor'], inplace=True)
    markups_dict = project_markups.to_dict('index')
    return markups_dict


def calc_project_markup_value(vehicle, markup_factor, model_year, scaling_dict, markups_dict):
    alt, rc, ft = vehicle
    scaled_markups_dict_id = ((vehicle), markup_factor, model_year)
    if scaled_markups_dict_id in scaled_markups_dict:
        project_markup_value = scaled_markups_dict[scaled_markups_dict_id]
    else:
        input_markup_value, scaler, scaled_by = markups_dict[(ft, markup_factor)]['Value'], markups_dict[(ft, markup_factor)]['Scaler'], markups_dict[(ft, markup_factor)]['Scaled_by']
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
    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    markups_dict = create_markup_inputs_dict(settings.markups)
    scaling_dict = create_scaling_dict(settings.warranty_inputs, 'Warranty', settings.usefullife_inputs, 'Usefullife', settings)

    for vehicle, model_year in product(vehicles, settings.years):
        for markup_factor in markup_factors:
            markup_value = calc_project_markup_value(vehicle, markup_factor, model_year, scaling_dict, markups_dict)
            if markup_factor == markup_factors[0]:
                project_markups_dict[((vehicle), model_year)] = {markup_factor: markup_value}
            else:
                project_markups_dict[((vehicle), model_year)].update({markup_factor: markup_value})
    return project_markups_dict


def per_veh_indirect_costs(settings, vehicles, direct_costs_dict):
    print('\nCalculating per vehicle indirect costs\n')
    per_veh_indirect_costs = dict()

    markup_factors = [arg for arg in settings.markups['Markup_Factor'].unique()]
    markups_dict = create_markup_inputs_dict(settings.markups)
    scaling_dict = create_scaling_dict(settings.warranty_inputs, 'Warranty', settings.usefullife_inputs, 'Usefullife', settings)

    for vehicle, model_year, markup_factor in product(vehicles, settings.years, markup_factors):
        markup_value = calc_project_markup_value(vehicle, markup_factor, model_year, scaling_dict, markups_dict)
        direct_cost = direct_costs_dict[((vehicle, model_year))]['DirectCost_AvgPerVeh']
        if markup_factor == markup_factors[0]:
            per_veh_indirect_costs[((vehicle), model_year)] = {f'{markup_factor}_AvgPerVeh': markup_value * direct_cost}
        else:
            per_veh_indirect_costs[((vehicle), model_year)].update({f'{markup_factor}_AvgPerVeh': markup_value * direct_cost})
    return per_veh_indirect_costs


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    # from cti_bca_tool.project_classes import Moves, WarrantyAndUsefullife
    from cti_bca_tool import project_fleet
    from cti_bca_tool import direct_costs2

    project_fleet_df = project_fleet.project_fleet_df(settings)
    vehicles_rc = pd.Series(project_fleet_df['alt_rc_ft'].unique())

    per_veh_markups_by_year_dict = per_veh_project_markups(settings, vehicles_rc)

    per_veh_markups_by_year_df = pd.DataFrame(per_veh_markups_by_year_dict)
    # save dict to csv
    direct_costs2.per_veh_direct_costs_to_csv(per_veh_markups_by_year_df, settings.path_project / 'test/per_veh_markups_by_year')

    project_regclass_sales_dict = project_fleet.project_regclass_sales_dict(project_fleet_df)
    direct_costs_dict = direct_costs2.per_veh_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]
    per_veh_indirect_costs_dict = per_veh_indirect_costs(settings, vehicles_rc, direct_costs_dict)
    per_veh_indirect_costs_df = pd.DataFrame(per_veh_indirect_costs_dict)
    # save dict to csv
    direct_costs2.per_veh_direct_costs_to_csv(per_veh_indirect_costs_df, settings.path_project / 'test/per_veh_indirect_costs_by_year')
