import pandas as pd
import attr
from itertools import product
from cti_bca_tool.project_classes import ProjectClass
from cti_bca_tool.project_fleet import alt_rc_ft_vehicles


absolute_scaler_dict = dict()
relative_scaler_dict = dict()


def calc_scalers_absolute(input_df, vehicle, identifier, period):
    """
    :param: input_df: A DataFrame of warranty or useful life miles and ages by optionID.
    :return: DatFrame of scaling factors that scale on absolute terms.
    """
    absolute_scaler_dict_id = f'{vehicle}_{identifier}'
    if absolute_scaler_dict_id in absolute_scaler_dict:
        return absolute_scaler_dict[absolute_scaler_dict_id]
    else:
        absolute_scaler_dict[absolute_scaler_dict_id] = dict()

    alt, rc, ft = vehicle
    scaler_df = pd.DataFrame(input_df.loc[(input_df['optionID'] == alt)
                                          & (input_df['regClassID'] == rc)
                                          & (input_df['fuelTypeID'] == ft)
                                          & (input_df['period'] == period), :]).reset_index(drop=True)
    cols = [col for col in scaler_df.columns if '20' in col]
    for col in cols[1:]:
        absolute_scaler_dict[absolute_scaler_dict_id].update({col: scaler_df[col][0] / scaler_df[cols[0]][0]})
    absolute_scaler_dict[absolute_scaler_dict_id].update({[cols[0]][0]: 1.0})
    return absolute_scaler_dict[absolute_scaler_dict_id]


def calc_scalers_relative(input_df, vehicle, identifier, period):
    """
    :param: input_df: A DataFrame of warranty or useful life miles and ages by optionID.
    :return: DatFrame of scaling factors that scale relative to the prior year.
    """
    relative_scaler_dict_id = f'{vehicle}_{identifier}'
    if relative_scaler_dict_id in relative_scaler_dict:
        return relative_scaler_dict[relative_scaler_dict_id]
    else:
        relative_scaler_dict[relative_scaler_dict_id] = dict()

    alt, rc, ft = vehicle
    scaler_df = pd.DataFrame(input_df.loc[(input_df['optionID'] == alt)
                                          & (input_df['regClassID'] == rc)
                                          & (input_df['fuelTypeID'] == ft)
                                          & (input_df['period'] == period), :]).reset_index(drop=True)
    cols = [col for col in scaler_df.columns if '20' in col]
    for col_number, col in enumerate(cols):
        relative_scaler_dict[relative_scaler_dict_id].update({col: scaler_df[cols[col_number]][0] / scaler_df[cols[col_number - 3]][0]})
    return relative_scaler_dict[relative_scaler_dict_id]


def get_markup_factors(df):
    project_markups = df.copy()
    # insert and id to use as a dictionary key
    project_markups.insert(0, 'id', pd.Series(zip(project_markups['fuelTypeID'], project_markups['Markup_Factor'])))
    project_markups.set_index('id', inplace=True)
    markups_dict = project_markups.to_dict('index')
    return markups_dict


def calc_project_markups(project_fleet, markups_dict, settings):
    """
    Warranty indirect markup factors are to be scaled using absolute scalers. R&D indirect markup factors are to be scaled using relative scalers.
    Other and Profit indirect markup factors are not scaled. The scaling factors are determined using both the warranty and useful life inputs which
    provide the no action and action (proposed) changes to the miles and ages during which warranty and/or useful life provisions exist. So, if warranty
    miles or age doubles (the miles or age identifier is set via the General_Inputs workbook), then the warranty markup factor would double indefinitely. If useful life
    miles or age doubles, then the R&D markup factor would double for three years the return to normal.
    :param project_fleet:
    :param settings:
    :return:
    """
    # create list of markup factors
    markup_factors = [item for item in settings.markups['Markup_Factor'].unique()]
    vehicles = alt_rc_ft_vehicles(project_fleet)
    years = range(project_fleet['modelYearID'].min(), project_fleet['modelYearID'].max() + 1)
    project_markups_dict = dict()

    for markup_factor, vehicle in product(markup_factors, vehicles):
        project_markups_dict[f'{vehicle}_{markup_factor}'] = dict()
    for markup_factor, vehicle, year in product(markup_factors, vehicles, years):
        alt, rc, ft = vehicle
        if markup_factor == 'Warranty':
            project_markups_dict[f'{vehicle}_{markup_factor}'] = calc_scalers_absolute(settings.warranty_inputs, vehicle, 'Warranty', settings.indirect_cost_scaling_metric)
            markup_factor_value = markups_dict[(ft, f'{markup_factor}')]['Value']
            project_markups_dict[f'{vehicle}_{markup_factor}'][str(year)] = project_markups_dict[f'{vehicle}_{markup_factor}'][str(year)] * markup_factor_value
        if markup_factor == 'RnD':
            project_markups_dict[f'{vehicle}_{markup_factor}'] = calc_scalers_relative(settings.usefullife_inputs, vehicle, 'UsefulLife', settings.indirect_cost_scaling_metric)
            markup_factor_value = markups_dict[(ft, f'{markup_factor}')]['Value']
            project_markups_dict[f'{vehicle}_{markup_factor}'][str(year)] = project_markups_dict[f'{vehicle}_{markup_factor}'][str(year)] * markup_factor_value
        if markup_factor == 'Other' or markup_factor == 'Profit':
            markup_factor_value = markups_dict[(ft, f'{markup_factor}')]['Value']
            project_markups_dict[f'{vehicle}_{markup_factor}'][str(year)] = markup_factor_value
    return project_markups_dict


def calc_per_veh_indirect_costs(project_fleet, per_veh_direct_costs_dict, project_markups_dict, settings):
    """
    Warranty indirect markup factors are to be scaled using absolute scalers. R&D indirect markup factors are to be scaled using relative scalers.
    Other and Profit indirect markup factors are not scaled. The scaling factors are determined using both the warranty and useful life inputs which
    provide the no action and action (proposed) changes to the miles and ages during which warranty and/or useful life provisions exist. So, if warranty
    miles or age doubles (the miles or age identifier is set via the General_Inputs workbook), then the warranty markup factor would double indefinitely. If useful life
    miles or age doubles, then the R&D markup factor would double for three years the return to normal.
    :param project_fleet:
    :param settings:
    :return:
    """
    # create list of markup factors
    markup_factors = [item for item in settings.markups['Markup_Factor'].unique()]
    years = range(project_fleet['modelYearID'].min(), project_fleet['modelYearID'].max() + 1)
    vehicles = alt_rc_ft_vehicles(project_fleet)
    per_veh_indirect_costs_dict = dict()
    per_veh_indirect_costs_df = pd.DataFrame()
    for vehicle in vehicles:
        alt, rc, ft = vehicle
        dc_df = per_veh_direct_costs_dict[vehicle].copy()
        per_veh_indirect_costs_dict[vehicle] = pd.DataFrame(columns=['optionID', 'modelYearID', 'ageID', 'regClassID', 'fuelTypeID'])
        per_veh_indirect_costs_dict[vehicle]['modelYearID'] = pd.Series(years)
        per_veh_indirect_costs_dict[vehicle]['optionID'] = alt
        per_veh_indirect_costs_dict[vehicle]['ageID'] = 0
        per_veh_indirect_costs_dict[vehicle]['regClassID'] = rc
        per_veh_indirect_costs_dict[vehicle]['fuelTypeID'] = ft
        for markup_factor in markup_factors:
            per_veh = list()
            for year in years:
                dc_year_df = pd.DataFrame(dc_df.loc[dc_df['modelYearID'] == year, :]).reset_index(drop=True)
                direct_cost = dc_year_df['DirectCost_AvgPerVeh'][0]
                per_veh.append(project_markups_dict[f'{vehicle}_{markup_factor}'][str(year)] * direct_cost)
            col_num = len(per_veh_indirect_costs_dict[vehicle].columns)
            per_veh_indirect_costs_dict[vehicle].insert(col_num, f'{markup_factor}Cost_AvgPerVeh', per_veh)

    for vehicle in vehicles:
        per_veh_indirect_costs_df = pd.concat([per_veh_indirect_costs_df, per_veh_indirect_costs_dict[vehicle]], axis=0, ignore_index=True)
    return per_veh_indirect_costs_df, per_veh_indirect_costs_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import project_fleet
    from cti_bca_tool.direct_costs2 import calc_per_veh_direct_costs

    project_fleet = project_fleet(settings.moves)
    vehicles = alt_rc_ft_vehicles(project_fleet)

    markups_dict = get_markup_factors(settings.markups)
    project_markups_dict = calc_project_markups(project_fleet, markups_dict, settings)
    project_markups_df = pd.DataFrame(project_markups_dict)

    per_veh_direct_costs_dict = calc_per_veh_direct_costs(project_fleet, settings)[1]
    per_veh_indirect_costs_df, per_veh_indirect_costs_dict \
        = calc_per_veh_indirect_costs(project_fleet, per_veh_direct_costs_dict, project_markups_dict, settings)

    project_markups_df.to_csv(settings.path_project / 'test/project_markups.csv', index=True)
    per_veh_indirect_costs_df.to_csv(settings.path_project / 'test/per_veh_indirect_costs.csv', index=False)
