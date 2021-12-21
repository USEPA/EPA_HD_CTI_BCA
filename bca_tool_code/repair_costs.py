from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages
from bca_tool_code.project_dicts import InputFileDict


def calc_typical_vmt_per_year(settings, vehicle, alt, model_year, averages_dict):
    """
    This function calculates a typical annual VMT/vehicle over a set number of years as set via the General Inputs workbook. This typical annual VMT/vehicle
    can then be used to estimate the ages at which warranty and useful life will be reached. When insufficient years are available -- e.g., if the typical_vmt_thru_ageID
    is set to >5 years and the given vehicle is a MY2041 vintage vehicle and the fleet input file contains data only thru CY2045, then insufficient data exist to
    calculate the typical VMT for that vehicle -- the typical VMT for that vehicle will be set equal to the last prior MY vintage for which sufficient data were present.

    Parameters:
        settings: The SetInputs class.\n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; the Alternative or option ID.\n
        model_year: Numeric; the model year of the passed vehicle.\n
        averages_dict: Dictionary; contains cumulative annual average VMT/vehicle.

    Returns:
        A single typical annual VMT/veh value for the passed vehicle of the given model year.

    """
    calcs_avg = FleetAverages(averages_dict)

    vmt_thru_age_id = settings.repair_inputs_dict['typical_vmt_thru_ageID']['Value']
    if model_year + vmt_thru_age_id <= settings.year_max:
        year = model_year
    else:
        year = settings.year_max - vmt_thru_age_id # can't get cumulative VMT when model_year + vmt_thru_age_id exceeds data

    cumulative_vmt = calcs_avg.get_attribute_value((vehicle, alt, year, vmt_thru_age_id, 0), 'VMT_AvgPerVeh_Cumulative')
    typical_vmt = cumulative_vmt / (vmt_thru_age_id + 1)

    return typical_vmt


def calc_estimated_age(settings, vehicle, alt, model_year, identifier, typical_vmt, estimated_ages_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; the Alternative or option ID.\n
        model_year: Numeric; the model year of the passed vehicle.\n
        identifier: String; the identifier of the age being estimated (i.e., 'Warranty' or 'Usefullife'). \n
        typical_vmt: Numeric; the typical annual VMT/vehicle over a set number of years as set via the General Inputs workbook (see calc_typical_vmt_per_year function).\n
        estimated_ages_dict: Dictionary in which to collect estimated ages to be included in the outputs for the given run.

    Returns:
        An integer representing the age at which the identifier will be reached for the passed vehicle/model year.\n
        A dictionary that tracks those ages for all vehicles.

    """
    miles_and_ages_dict = InputFileDict(settings.warranty_inputs_dict)
    if identifier == 'Usefullife': miles_and_ages_dict = InputFileDict(settings.usefullife_inputs_dict)

    st, rc, ft = vehicle
    required_age = miles_and_ages_dict.get_attribute_value(((rc, ft, 'Age'), alt), str(model_year))
    required_miles = miles_and_ages_dict.get_attribute_value(((rc, ft, 'Miles'), alt), str(model_year))
    calculated_age = round(required_miles / typical_vmt)
    estimated_age = min(required_age, calculated_age)
    estimated_ages_dict[(vehicle, alt, model_year, identifier)] = ({'vehicle': vehicle,
                                                                    'optionID': alt,
                                                                    'modelYearID': model_year,
                                                                    'identifier': identifier,
                                                                    'typical_vmt': typical_vmt,
                                                                    'required_age': required_age,
                                                                    'calculated_age': calculated_age,
                                                                    'estimated_age': estimated_age,
                                                                    })
    return estimated_age, estimated_ages_dict


def calc_emission_repair_costs_per_mile(settings, averages_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        averages_dict: Dictionary; contains tech package direct costs/vehicle and cumulative annual average VMT/vehicle.

    Returns:
        The averages_dict dictionary updated to include emission repair costs/mile for each dictionary key.\n
        A repair cost/mile dictionary containing details used in the calculation of repair cost/mile and which is then written to an output file for the given run.\n
        An 'estimated ages' dictionary containing details behind the calculations and which is then written to an output file for the given run.

    """
    print('\nCalculating emission repair costs per mile...')
    calcs_avg = FleetAverages(averages_dict)

    repair_cpm_dict = dict()
    estimated_ages_dict = dict()
    for key in averages_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key

        reference_direct_cost = calcs_avg.get_attribute_value(((61, 47, 2), 0, model_year, 0, 0), 'DirectCost_AvgPerVeh') # sourcetype here is arbitrary provided it is of diesel regclass 47
        direct_cost = calcs_avg.get_attribute_value((vehicle, alt, model_year, 0, 0), 'DirectCost_AvgPerVeh')
        direct_cost_scaler = direct_cost / reference_direct_cost

        typical_vmt = calc_typical_vmt_per_year(settings, vehicle, alt, model_year, averages_dict)
        warranty_estimated_age, estimated_ages_dict = calc_estimated_age(settings, vehicle, alt, model_year, 'Warranty', typical_vmt, estimated_ages_dict)
        usefullife_estimated_age, estimated_ages_dict = calc_estimated_age(settings, vehicle, alt, model_year, 'Usefullife', typical_vmt, estimated_ages_dict)

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
        calcs_avg.update_dict(key, 'EmissionRepairCost_AvgPerMile', cpm)
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
    return averages_dict, repair_cpm_dict, estimated_ages_dict


def calc_per_veh_emission_repair_costs(averages_dict):
    """

    Parameters:
        averages_dict: Dictionary; contains annual emission repair costs/mile.

    Returns:
        The passed dictionary updated with annual emission repair costs/vehicle for each dictionary key.

    """
    print('\nCalculating emission repair costs per vehicle...')
    calcs_avg = FleetAverages(averages_dict)

    for key in averages_dict.keys():
        repair_cpm = calcs_avg.get_attribute_value(key, 'EmissionRepairCost_AvgPerMile')
        vmt_per_veh = calcs_avg.get_attribute_value(key, 'VMT_AvgPerVeh')
        cost_per_veh = repair_cpm * vmt_per_veh
        calcs_avg.update_dict(key, 'EmissionRepairCost_AvgPerVeh', cost_per_veh)

    return averages_dict


def calc_emission_repair_costs(totals_dict, averages_dict, vpop_arg):
    """

    Parameters:
        totals_dict: Dictionary; contains annual vehicle populations (VPOP).\n
        averages_dict: Dictionary; contains annual average emission repair costs/mile.\n
        vpop_arg: String; specifies the population attribute to use (e.g., "VPOP" or "VPOP_withTech")

    Returns:
        The totals_dict dictionary updated with annual emission repair costs for all vehicles.

    """
    print(f'\nCalculating total emission repair costs...')

    calcs_avg = FleetAverages(averages_dict)
    calcs = FleetTotals(totals_dict)

    for key in totals_dict.keys():
        cost_per_veh = calcs_avg.get_attribute_value(key, 'EmissionRepairCost_AvgPerVeh')
        vpop = calcs.get_attribute_value(key, vpop_arg)
        cost = cost_per_veh * vpop
        calcs.update_dict(key, 'EmissionRepairCost', cost)

    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
