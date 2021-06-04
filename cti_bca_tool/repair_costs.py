# import pandas as pd


cumulative_vmt_dict = dict()
typical_vmt_dict = dict()
estimated_ages_dict = dict()
repair_cpm_dict = dict()


def calc_per_veh_cumulative_vmt(averages_dict):
    """This function calculates cumulative average VMT/vehicle year-over-year for use in estimating a typical VMT per year and for estimating emission
    repair costs.

    Parameters:
        averages_dict: A dictionary containing annual average VMT/vehicle.

    Returns:
        The averages_dict dictionary updated with cumulative annual average VMT/vehicle.

    Note:
        VMT does not differ across options.

    """
    # this loop calculates the cumulative vmt for each key with the averages_dict and saves it in the cumulative_vmt_dict
    for key in averages_dict.keys():
        vehicle, model_year, age_id, disc_rate = key
        alt, st, rc, ft = vehicle
        if ((0, st, rc, ft), model_year, age_id-1, 0) in cumulative_vmt_dict.keys():
            cumulative_vmt = cumulative_vmt_dict[((0, st, rc, ft), model_year, age_id-1, 0)] + averages_dict[key]['VMT_AvgPerVeh']
        else:
            cumulative_vmt = averages_dict[key]['VMT_AvgPerVeh']
        cumulative_vmt_dict[key] = cumulative_vmt
    # this loop updates the averages_dict with the contents of the cumulative_vmt_dict
    for key in averages_dict.keys():
        cumulative_vmt = cumulative_vmt_dict[key]
        averages_dict[key].update({'VMT_AvgPerVeh_Cumulative': cumulative_vmt})
    return averages_dict


def calc_typical_vmt_per_year(settings, vehicle, model_year, averages_dict):
    """This function calculates a typical annual VMT/vehicle over a set number of years as set via the General Inputs workbook. This typical annual VMT/vehicle
    can then be used to estimate the ages at which warranty and useful life will be reached.

    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.\n
        model_year: The model year of the passed vehicle.\n
        averages_dict: A dictionary containing cumulative annual average VMT/vehicle.

    Returns:
        A single typical annual VMT/veh value for the passed vehicle of the given model year.

    """
    typical_vmt_dict_id = (vehicle, model_year)
    if typical_vmt_dict_id in typical_vmt_dict:
        vmt = typical_vmt_dict[typical_vmt_dict_id]
    else:
        vmt_thru_age_id = settings.repair_inputs_dict['typical_vmt_thru_ageID']['Value']
        if model_year + vmt_thru_age_id <= settings.year_max:
            vmt = averages_dict[(vehicle, model_year, vmt_thru_age_id, 0)]['VMT_AvgPerVeh_Cumulative'] / (vmt_thru_age_id + 1)
        else:
            vmt = typical_vmt_dict[(vehicle, model_year-1)]
        typical_vmt_dict[typical_vmt_dict_id] = vmt
    return vmt


def calc_estimated_age(settings, vehicle, model_year, identifier, averages_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.\n
        model_year: The model year of the passed vehicle.\n
        identifier: The identifier of the age being estimated (i.e., 'Warranty' or 'Usefullife')\n
        averages_dict: A dictionary containing cumulative annual average VMT/veh.

    Returns:
        An integer representing the age at which the identifier will be reached for the passed vehicle/model year.

    """
    alt, st, rc, ft = vehicle
    estimated_ages_dict_id = (vehicle, model_year, identifier)
    if estimated_ages_dict_id in estimated_ages_dict.keys():
        required_age, calculated_age, estimated_age,  = estimated_ages_dict[estimated_ages_dict_id]['required_age'],\
                                                        estimated_ages_dict[estimated_ages_dict_id]['calculated_age'], \
                                                        estimated_ages_dict[estimated_ages_dict_id]['estimated_age']
    else:
        typcial_vmt = calc_typical_vmt_per_year(settings, vehicle, model_year, averages_dict)
        required_age = settings.required_miles_and_ages_dict[((alt, rc, ft), identifier, 'Age')][str(model_year)]
        calculated_age = round(settings.required_miles_and_ages_dict[((alt, rc, ft), identifier, 'Miles')][str(model_year)] / typcial_vmt)
        estimated_age = min(required_age, calculated_age)
        estimated_ages_dict[(vehicle, model_year, identifier)] = ({'required_age': required_age,
                                                                   'calculated_age': calculated_age,
                                                                   'estimated_age': estimated_age,
                                                                   })
    return estimated_age


def calc_emission_repair_costs_per_mile(settings, averages_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        averages_dict: A dictionary containing tech package direct costs/vehicle and cumulative annual average VMT/vehicle.

    Returns:
        The averages_dict dictionary updated to include emission repair costs/mile for each dictionary key. This function also populates the
        repair_cpm_dict which is then written to an output file for the given run.

    """
    for key in averages_dict.keys():
        print(f'Calculating repair costs per mile for {key}')
        vehicle, model_year, age_id, disc_rate = key
        reference_direct_cost = averages_dict[((0, 61, 47, 2), model_year, 0, 0)]['DirectCost_AvgPerVeh'] # sourcetype here is arbitrary provided it is of diesel regclass 47
        direct_cost_scaler = averages_dict[(vehicle, model_year, 0, 0)]['DirectCost_AvgPerVeh'] / reference_direct_cost
        warranty_estimated_age = calc_estimated_age(settings, vehicle, model_year, 'Warranty', averages_dict)
        usefullife_estimated_age = calc_estimated_age(settings, vehicle, model_year, 'Usefullife', averages_dict)
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
        averages_dict[key].update({'EmissionRepairCost_AvgPerMile': cpm})
        repair_cpm_dict[key] = {'reference_direct_cost': reference_direct_cost,
                                'direct_cost_scaler': direct_cost_scaler,
                                'warranty_estimated_age': warranty_estimated_age,
                                'usefullife_estimated_age': usefullife_estimated_age,
                                'in_warranty_cpm': in_warranty_cpm,
                                'at_usefullife_cpm': at_usefullife_cpm,
                                'slope_within_usefullife': slope_within_usefullife,
                                'max_cpm': max_cpm,
                                'cpm': cpm
                                }
    return averages_dict


def calc_per_veh_emission_repair_costs(averages_dict):
    """

    Parameters:
        averages_dict: A dictionary containing annual emission repair costs/mile.

    Returns:
        The passed dictionary updated with annual emission repair costs/vehicle for each dictionary key.

    """
    for key in averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        print(f'Calculating repair costs per vehicle for {vehicle}, MY {model_year}, age {age_id}')
        repair_cpm = averages_dict[key]['EmissionRepairCost_AvgPerMile']
        vmt_per_veh = averages_dict[key]['VMT_AvgPerVeh']
        averages_dict[key].update({'EmissionRepairCost_AvgPerVeh': repair_cpm * vmt_per_veh})
    return averages_dict


def calc_emission_repair_costs(totals_dict, averages_dict):
    """

    Parameters:
        totals_dict: A dictionary containing annual vehicle populations (VPOP).\n
        averages_dict: A dictionary containing annual average emission repair costs/mile.

    Returns:
        The totals_dict dictionary updated with annual emission repair costs for all vehicles.

    """
    print(f'\nCalculating total repair costs.\n')
    for key in totals_dict.keys():
        cost_per_veh = averages_dict[key]['EmissionRepairCost_AvgPerVeh']
        vpop = totals_dict[key]['VPOP']
        totals_dict[key].update({'EmissionRepairCost': cost_per_veh * vpop})
    return totals_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_totals_dict, create_averages_dict
    from cti_bca_tool.direct_costs import calc_regclass_yoy_costs_per_step, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs
    from cti_bca_tool.tech_costs import calc_per_veh_tech_costs, calc_tech_costs

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    totals_dict = create_totals_dict(project_fleet_df)
    averages_dict = create_averages_dict(project_fleet_df)

    regclass_yoy_costs_per_step = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)
    averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step, averages_dict)
    totals_dict = calc_direct_costs(totals_dict, averages_dict)

    averages_dict = calc_per_veh_indirect_costs(settings, averages_dict)
    averages_dict = calc_per_veh_tech_costs(averages_dict)

    totals_dict = calc_indirect_costs(settings, totals_dict, averages_dict)
    totals_dict = calc_tech_costs(totals_dict, averages_dict)

    averages_dict = calc_emission_repair_costs_per_mile(settings, averages_dict)
    averages_dict = calc_per_veh_emission_repair_costs(averages_dict)
    totals_dict = calc_emission_repair_costs(totals_dict, averages_dict)

    save_dict_to_csv(averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(estimated_ages_dict, settings.path_project / 'test/estimated_ages', 'vehicle', 'modelYearID', 'identifier')
    save_dict_to_csv(repair_cpm_dict, settings.path_project / 'test/repair_cpm_details', 'vehicle', 'modelYearID', 'ageID')
