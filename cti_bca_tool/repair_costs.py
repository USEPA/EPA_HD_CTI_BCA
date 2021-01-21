import pandas as pd


cumulative_vmt_dict = dict()
typical_vmt_dict = dict()
estimated_ages_dict = dict()
repair_cpm_dict = dict()


def calc_per_veh_cumulative_vmt(fleet_averages_dict):
    """
    VMT does not change between alternatives (optionIDs)
    :param fleet_averages_dict:
    :return:
    """
    for key in fleet_averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if ((0, st, rc, ft), model_year, age_id-1, 0) in cumulative_vmt_dict:
            cumulative_vmt = cumulative_vmt_dict[((0, st, rc, ft), model_year, age_id-1, 0)] + fleet_averages_dict[key]['VMT_AvgPerVeh']
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
        vmt_thru_age_id = settings.repair_inputs_dict['typical_vmt_thru_ageID']['Value']
        if model_year + vmt_thru_age_id <= settings.year_max:
            vmt = fleet_averages_dict[((vehicle), model_year, vmt_thru_age_id, 0)]['VMT_AvgPerVeh_Cumulative'] / (vmt_thru_age_id + 1)
        else:
            vmt = typical_vmt_dict[((vehicle), model_year-1)]
        typical_vmt_dict[key] = vmt
    return vmt


def calc_estimated_age(settings, vehicle, model_year, identifier, fleet_averages_dict):
    alt, st, rc, ft = vehicle
    key = ((vehicle), model_year, identifier)
    if key in estimated_ages_dict.keys():
        required_age, calculated_age, estimated_age,  = estimated_ages_dict[key]['required_age'],\
                                                        estimated_ages_dict[key]['calculated_age'], \
                                                        estimated_ages_dict[key]['estimated_age']
    else:
        typcial_vmt = calc_typical_vmt_per_year(settings, vehicle, model_year, fleet_averages_dict)
        required_age = settings.required_miles_and_ages_dict[((alt, rc, ft), identifier, 'Age')][str(model_year)]
        calculated_age = round(settings.required_miles_and_ages_dict[((alt, rc, ft), identifier, 'Miles')][str(model_year)] / typcial_vmt)
        estimated_age = min(required_age, calculated_age)
        estimated_ages_dict[((vehicle), model_year, identifier)] = ({'required_age': required_age,
                                                                     'calculated_age': calculated_age,
                                                                     'estimated_age': estimated_age,
                                                                     })
    return estimated_age


def calc_emission_repair_costs_per_mile(settings, fleet_averages_dict):
    for key in fleet_averages_dict.keys():
        print(f'Calculating repair costs per mile for {key}')
        vehicle, model_year, age_id = key[0], key[1], key[2]
        reference_direct_cost = fleet_averages_dict[((0, 61, 47, 2), model_year, 0, 0)]['DirectCost_AvgPerVeh'] # sourcetype here is arbitrary provided it is of diesel regclass 47
        direct_cost_scaler = fleet_averages_dict[((vehicle), model_year, 0, 0)]['DirectCost_AvgPerVeh'] / reference_direct_cost
        warranty_estimated_age = calc_estimated_age(settings, vehicle, model_year, 'Warranty', fleet_averages_dict)
        usefullife_estimated_age = calc_estimated_age(settings, vehicle, model_year, 'Usefullife', fleet_averages_dict)
        in_warranty_cpm = settings.repair_inputs_dict['in-warranty_R&M_CPM']['Value'] \
                          * settings.repair_inputs_dict['emission_repair_share']['Value'] \
                          * direct_cost_scaler
        at_usefullife_cpm = settings.repair_inputs_dict['at-usefullife_R&M_CPM']['Value'] \
                          * settings.repair_inputs_dict['emission_repair_share']['Value'] \
                          * direct_cost_scaler

        if usefullife_estimated_age > warranty_estimated_age:
            slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) / (usefullife_estimated_age - warranty_estimated_age)
        else:
            slope_within_usefullife = 0

        max_cpm = settings.repair_inputs_dict['max_R&M_CPM']['Value'] \
                  * settings.repair_inputs_dict['emission_repair_share']['Value'] \
                  * direct_cost_scaler

        # now calulate the cost per mile
        if (age_id + 1) < warranty_estimated_age:
            cpm = in_warranty_cpm
        elif warranty_estimated_age <= (age_id + 1) < usefullife_estimated_age:
            cpm = slope_within_usefullife * ((age_id + 1) - warranty_estimated_age) + in_warranty_cpm
        elif (age_id + 1) == usefullife_estimated_age:
            cpm = at_usefullife_cpm
        else:
            cpm = max_cpm
        fleet_averages_dict[key].update({'EmissionRepairCost_AvgPerMile': cpm})
        repair_cpm_dict[key] = {'reference_direct_cost': reference_direct_cost, \
                                'direct_cost_scaler': direct_cost_scaler, \
                                'warranty_estimated_age': warranty_estimated_age, \
                                'usefullife_estimated_age': usefullife_estimated_age, \
                                'in_warranty_cpm': in_warranty_cpm, \
                                'at_usefullife_cpm': at_usefullife_cpm, \
                                'slope_within_usefullife': slope_within_usefullife, \
                                'max_cpm': max_cpm, \
                                'cpm': cpm
                                }
    return fleet_averages_dict


def calc_per_veh_emission_repair_costs(fleet_averages_dict):
    for key in fleet_averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        print(f'Calculating repair costs per vehicle for {vehicle}, MY {model_year}, age {age_id}')
        repair_cpm = fleet_averages_dict[key]['EmissionRepairCost_AvgPerMile']
        vmt_per_veh = fleet_averages_dict[key]['VMT_AvgPerVeh']
        fleet_averages_dict[key].update({'EmissionRepairCost_AvgPerVeh': repair_cpm * vmt_per_veh})
    return fleet_averages_dict


def calc_emission_repair_costs(fleet_totals_dict, fleet_averages_dict):
    print(f'\nCalculating total repair costs.\n')
    for key in fleet_totals_dict.keys():
        cost_per_veh = fleet_averages_dict[key]['EmissionRepairCost_AvgPerVeh']
        vpop = fleet_totals_dict[key]['VPOP']
        fleet_totals_dict[key].update({'EmissionRepairCost': cost_per_veh * vpop})
    return fleet_totals_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.direct_costs2 import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs2 import calc_per_veh_indirect_costs, calc_indirect_costs
    from cti_bca_tool.tech_costs import calc_per_veh_tech_costs, calc_tech_costs

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    regclass_yoy_costs_per_step = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)
    fleet_averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step, fleet_averages_dict)
    fleet_totals_dict = calc_direct_costs(fleet_totals_dict, fleet_averages_dict)

    # per_veh_dc_by_year_dict = calc_per_regclass_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]

    # fleet_totals_dict = calc_direct_costs(per_veh_dc_by_year_dict, fleet_totals_dict)
    # fleet_averages_dict = calc_per_veh_direct_costs(fleet_totals_dict, fleet_averages_dict)

    fleet_averages_dict = calc_per_veh_indirect_costs(settings, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_tech_costs(fleet_averages_dict)

    fleet_totals_dict = calc_indirect_costs(settings, fleet_totals_dict, fleet_averages_dict)
    fleet_totals_dict = calc_tech_costs(fleet_totals_dict, fleet_averages_dict)

    # fleet_averages_dict = calc_emission_repair_costs_per_mile(settings, per_veh_dc_by_year_dict, fleet_averages_dict)
    fleet_averages_dict = calc_emission_repair_costs_per_mile(settings, fleet_averages_dict)
    fleet_averages_dict = calc_per_veh_emission_repair_costs(fleet_averages_dict)
    fleet_totals_dict = calc_emission_repair_costs(fleet_totals_dict, fleet_averages_dict)

    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(estimated_ages_dict, settings.path_project / 'test/estimated_ages', 'vehicle', 'modelYearID', 'identifier')
    save_dict_to_csv(repair_cpm_dict, settings.path_project / 'test/repair_cpm_details', 'vehicle', 'modelYearID', 'ageID')
