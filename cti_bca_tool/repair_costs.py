import pandas as pd


cumulative_vmt_dict = dict()
typical_vmt_dict = dict()
estimated_ages_dict = dict()


def calc_per_veh_cumulative_vmt(fleet_averages_dict):
    """
    VMT does not change between alternatives (optionIDs)
    :param fleet_averages_dict:
    :return:
    """
    for key in fleet_averages_dict.keys():
        vehicle, model_year, age = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if ((0, st, rc, ft), model_year, age-1) in cumulative_vmt_dict:
            cumulative_vmt = cumulative_vmt_dict[((0, st, rc, ft), model_year, age-1)] + fleet_averages_dict[key]['VMT_AvgPerVeh']
        else:
            cumulative_vmt = fleet_averages_dict[key]['VMT_AvgPerVeh']
        cumulative_vmt_dict[key] = cumulative_vmt

    for key in fleet_averages_dict.keys():
        cumulative_vmt = cumulative_vmt_dict[key]
        fleet_averages_dict[key].update({'VMT_AvgPerVeh_Cumulative': cumulative_vmt})
    return fleet_averages_dict


def calc_typical_vmt_per_year(settings, vehicle, model_year, fleet_averages_dict):
    key = ((vehicle), model_year)
    if key in typical_vmt_dict:
        vmt = typical_vmt_dict[key]
    else:
        vmt_thru_age = settings.repair_inputs_dict['typical_vmt_thru_ageID']['Value']
        if model_year + vmt_thru_age <= settings.year_max:
            vmt = fleet_averages_dict[((vehicle), model_year, vmt_thru_age)]['VMT_AvgPerVeh_Cumulative'] / (vmt_thru_age + 1)
        else:
            vmt = typical_vmt_dict[((vehicle), model_year-1)]
        typical_vmt_dict[key] = vmt
    return vmt


def calc_estimated_age(settings, vehicle, model_year, identifier, fleet_averages_dict):
    alt, st, rc, ft = vehicle
    key = ((vehicle), model_year, identifier)
    if key in estimated_ages_dict.keys():
        estimated_age = estimated_ages_dict[key]
    else:
        typcial_vmt = calc_typical_vmt_per_year(settings, vehicle, model_year, fleet_averages_dict)
        required_age = settings.required_miles_and_ages_dict[((alt, rc, ft), identifier, 'Age')][str(model_year)]
        calculated_age = round(settings.required_miles_and_ages_dict[((alt, rc, ft), identifier, 'Miles')][str(model_year)] / typcial_vmt)
        estimated_age = min(required_age, calculated_age)
        estimated_ages_dict[((vehicle), model_year, f'estimated_{identifier}_age')] = estimated_age
    return estimated_age

# TODO this needs qa/qc
def calc_per_veh_emission_repair_cost(settings, fleet_averages_dict):
    for key in fleet_averages_dict.keys():
        vehicle, model_year, age = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        reference_direct_cost = fleet_averages_dict[((0, st, rc, ft), model_year, 0)]['DirectCost_AvgPerVeh']
        direct_cost_scaler = fleet_averages_dict[((0, st, rc, ft), model_year, 0)]['DirectCost_AvgPerVeh'] / reference_direct_cost
        warranty_age = calc_estimated_age(settings, vehicle, model_year, 'Warranty', fleet_averages_dict)
        usefullife_age = calc_estimated_age(settings, vehicle, model_year, 'Usefullife', fleet_averages_dict)
        in_warranty_cpm = settings.repair_inputs_dict['in-warranty_R&M_CPM']['Value'] \
                          * settings.repair_inputs_dict['emission_repair_share']['Value'] \
                          * direct_cost_scaler
        at_usefullife_cpm = settings.repair_inputs_dict['at-usefullife_R&M_CPM']['Value'] \
                          * settings.repair_inputs_dict['emission_repair_share']['Value'] \
                          * direct_cost_scaler

        if usefullife_age > warranty_age:
            slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) / (usefullife_age - warranty_age)
        else:
            slope_within_usefullife = 0

        max_cpm = settings.repair_inputs_dict['max_R&M_CPM']['Value'] \
                  * settings.repair_inputs_dict['emission_repair_share']['Value'] \
                  * direct_cost_scaler

        # now calulate the cost per mile
        if age <= warranty_age:
            cpm = in_warranty_cpm
        elif warranty_age < age < usefullife_age:
            cpm = slope_within_usefullife * (age - warranty_age - 1) + in_warranty_cpm
        elif age <= (usefullife_age - 1):
            cpm = at_usefullife_cpm
        else:
            cpm = max_cpm
        fleet_averages_dict[key].update({'EmissionRepairCost_AvgPerMile': cpm})
    return fleet_averages_dict



if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs2 import calc_per_regclass_direct_costs, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
    from cti_bca_tool.tech_costs import calc_per_veh_tech_costs, calc_tech_costs

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    project_regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    per_veh_dc_by_year_dict = calc_per_regclass_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]

    fleet_totals_dict = calc_direct_costs(per_veh_dc_by_year_dict, fleet_totals_dict)
    fleet_averages_dict = calc_per_veh_direct_costs(fleet_totals_dict, fleet_averages_dict)

    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_tech_costs(fleet_averages_dict)

    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)
    fleet_totals_dict = calc_tech_costs(fleet_totals_dict, fleet_averages_dict)

    fleet_averages_dict = calc_per_veh_emission_repair_cost(settings, fleet_averages_dict)
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')

    df = pd.DataFrame.from_dict(estimated_ages_dict, orient='index')
    df.to_csv(settings.path_project / 'test/estimated_ages.csv', index=True)
    t = 0