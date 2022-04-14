

def calc_typical_vmt_per_year(settings, data_object, key):
    """
    This function calculates a typical annual VMT/vehicle over a set number of years as set via the General Inputs workbook. This typical annual VMT/vehicle
    can then be used to estimate the ages at which warranty and useful life will be reached. When insufficient years are available -- e.g., if the typical_vmt_thru_ageID
    is set to >5 years and the given vehicle is a MY2041 vintage vehicle and the fleet input file contains data only thru CY2045, then insufficient data exist to
    calculate the typical VMT for that vehicle -- the typical VMT for that vehicle will be set equal to the last prior MY vintage for which sufficient data were present.

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.\n
        key: Tuple; represents a sourcetype, regclass,fueltype, model year vehicle.

    Returns:
        A single typical annual VMT/veh value for the passed vehicle of the given model year.

    """
    vehicle, alt, model_year, age_id, disc_rate = key
    vmt_thru_age_id = int(settings.repair_and_maintenance.get_attribute_value('typical_vmt_thru_ageID'))
    year_max = data_object.year_max

    if model_year + vmt_thru_age_id <= year_max:
        year = model_year
    else:
        year = year_max - vmt_thru_age_id # can't get cumulative VMT when model_year + vmt_thru_age_id exceeds year_max

    cumulative_vmt_key = (vehicle, alt, year, vmt_thru_age_id, 0)
    cumulative_vmt = data_object.get_attribute_value(cumulative_vmt_key, 'VMT_PerVeh_Cumulative')
    typical_vmt = cumulative_vmt / (vmt_thru_age_id + 1)

    return typical_vmt


def calc_estimated_age(settings, key, typical_vmt):
    """

    Parameters:
        settings: The SetInputs class.\n
        key: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
        typical_vmt: Numeric; the typical annual VMT/vehicle over a set number of years as set via the General Inputs
        workbook (see calc_typical_vmt_per_year function).

    Returns:
        The passed dictionary updated to include the ages at which warranty and useful life will be reached for the
        passed vehicle/model year.

    """
    vehicle, alt, model_year, age_id, disc_rate = key
    st, rc, ft = vehicle
    engine = rc, ft

    miles_and_ages_dict = {'Warranty': settings.warranty,
                           'UsefulLife': settings.useful_life,
                           }

    for identifier in ['Warranty', 'UsefulLife']:
        miles_and_ages = miles_and_ages_dict[identifier]
        estimated_ages_dict_key = vehicle, alt, model_year, identifier

        required_age = miles_and_ages.get_attribute_value((engine, alt, 'Age'), str(model_year))
        required_miles = miles_and_ages.get_attribute_value((engine, alt, 'Miles'), str(model_year))
        calculated_age = round(required_miles / typical_vmt)
        estimated_age = min(required_age, calculated_age)
        settings.estimated_ages_dict[estimated_ages_dict_key] = ({'vehicle': vehicle,
                                                                  'optionID': alt,
                                                                  'modelYearID': model_year,
                                                                  'identifier': identifier,
                                                                  'typical_vmt': typical_vmt,
                                                                  'required_age': required_age,
                                                                  'calculated_age': calculated_age,
                                                                  'estimated_age': estimated_age,
                                                                  })


def calc_emission_repair_costs_per_mile(settings, data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        Updates the fleet dictionary to include emission repair costs/mile.\n
        A repair cost/mile dictionary containing details used in the calculation of repair cost/mile and which is then
        written to an output file for the given run.\n
        An estimated ages dictionary containing details behind the calculations and which is then written to an output
        file for the given run.

    """
    print('\nCalculating emission repair costs per mile...')

    in_warranty_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('in-warranty_R&M_CPM')
    at_usefullife_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('at-usefullife_R&M_CPM')
    max_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('max_R&M_CPM')
    emission_repair_share_input_value = settings.repair_and_maintenance.get_attribute_value('emission_repair_share')

    for key in data_object.keys:
        vehicle, alt, model_year, age_id, disc_rate = key

        # Note: keys with non-zero discount rates won't have any cost data yet.
        # The sourcetype in referenece_direct_cost is arbitrary provided it is of diesel regclass 47.
        reference_direct_cost \
            = data_object.get_attribute_value(((61, 47, 2), 0, model_year, 0, 0), 'DirectCost_PerVeh')
        direct_cost = data_object.get_attribute_value((vehicle, alt, model_year, 0, 0), 'DirectCost_PerVeh')
        direct_cost_scaler = direct_cost / reference_direct_cost

        typical_vmt = calc_typical_vmt_per_year(settings, data_object, key)

        # calculate estimated ages at which warranty and useful life will occur
        calc_estimated_age(settings, key, typical_vmt)
        warranty_estimated_age = settings.estimated_ages_dict[vehicle, alt, model_year, 'Warranty']['estimated_age']
        usefullife_estimated_age = settings.estimated_ages_dict[vehicle, alt, model_year, 'UsefulLife']['estimated_age']

        in_warranty_cpm = in_warranty_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        at_usefullife_cpm = at_usefullife_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        max_cpm = max_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler

        # calculate the slope of the cost per mile curve between warranty and useful life estimated ages
        if usefullife_estimated_age > warranty_estimated_age:
            slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) \
                                      / (usefullife_estimated_age - warranty_estimated_age)
        else:
            slope_within_usefullife = 0

        # now calulate the cost per mile
        if (age_id + 1) < warranty_estimated_age:
            cpm = in_warranty_cpm
        elif warranty_estimated_age <= (age_id + 1) < usefullife_estimated_age:
            cpm = slope_within_usefullife * ((age_id + 1) - warranty_estimated_age) + in_warranty_cpm
        elif (age_id + 1) == usefullife_estimated_age:
            cpm = at_usefullife_cpm
        else:
            cpm = max_cpm

        update_dict = {'EmissionRepairCost_PerMile': cpm}
        data_object.update_dict(key, update_dict)

        settings.repair_cpm_dict[key] = {'reference_direct_cost': reference_direct_cost,
                                         'direct_cost_scaler': direct_cost_scaler,
                                         'warranty_estimated_age': warranty_estimated_age,
                                         'usefullife_estimated_age': usefullife_estimated_age,
                                         'in_warranty_cpm': in_warranty_cpm,
                                         'at_usefullife_cpm': at_usefullife_cpm,
                                         'slope_within_usefullife': slope_within_usefullife,
                                         'max_cpm': max_cpm,
                                         'cpm': cpm
                                         }


def calc_emission_repair_costs_per_veh(data_object):
    """

    Parameters:
        data_object: Object; the fleet data object.

    Returns:
        Updates the fleet dictionary with annual emission repair costs/vehicle for each dictionary key.

    """
    print('\nCalculating emission repair costs per vehicle...')

    for key in data_object.keys:
        repair_cpm = data_object.get_attribute_value(key, 'EmissionRepairCost_PerMile')
        vmt_per_veh = data_object.get_attribute_value(key, 'VMT_PerVeh')
        cost_per_veh = repair_cpm * vmt_per_veh

        update_dict = {'EmissionRepairCost_PerVeh': cost_per_veh}
        data_object.update_dict(key, update_dict)


def calc_emission_repair_costs(data_object):
    """

    Parameters:
        data_object: Object; the fleet data object.

    Returns:
        The totals_dict dictionary updated with annual emission repair costs for all vehicles.

    """
    print(f'\nCalculating total emission repair costs...')

    for key in data_object.keys:
        cost_per_veh = data_object.get_attribute_value(key, 'EmissionRepairCost_PerVeh')
        vpop = data_object.get_attribute_value(key, 'VPOP')
        cost = cost_per_veh * vpop

        update_dict = {'EmissionRepairCost': cost}
        data_object.update_dict(key, update_dict)
