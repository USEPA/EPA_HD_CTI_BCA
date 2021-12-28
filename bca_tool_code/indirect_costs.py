from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages
from bca_tool_code.project_dicts import InputFileDict


def calc_project_markup_value(settings, unit, alt, markup_factor_name, model_year):
    """

    This function calculates the project markup value for the markup_factor (Warranty, RnD, Other, Profit) passed.

    Parameters:
        settings: The SetInputs classs.\n
        unit:  Tuple; represents a regclass_fueltype engine or a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; The Alternative or option ID.\n
        markup_factor_name: String; represents the name of the project markup factor value to return (warranty, r and d, other, etc.).\n
        model_year: Numeric; the model year of the passed unit.

    Returns:
        A single markup factor value to be used in the project having been adjusted in accordance with the proposed warranty and useful life
        changes and the Absolute/Relative scaling entries.

    Note:
        The project markup factor differs from the input markup factors by scaling where that scaling is done based on the "Absolute" or "Relative"
        entries in the input file and by the scaling metric (Miles or Age) entries of the warranty/useful life input files. Whether Miles or Age is used is set
        via the BCA_General_Inputs file.

    """
    try:
        rc, ft = unit
        markups_dict = InputFileDict(settings.markup_inputs_regclass_dict)
    except:
        st, rc, ft = unit
        markups_dict = InputFileDict(settings.markup_inputs_sourcetype_dict)

    markups_dict_key = (ft, markup_factor_name), alt
    scaling_metric = settings.indirect_cost_scaling_metric # scaling metric will be 'Miles' or 'Age'
    input_markup_value, scaler, scaled_by, num_years = markups_dict.get_attribute_value(markups_dict_key, 'Value'), \
                                                       markups_dict.get_attribute_value(markups_dict_key, 'Scaler'), \
                                                       markups_dict.get_attribute_value(markups_dict_key, 'Scaled_by'), \
                                                       markups_dict.get_attribute_value(markups_dict_key, 'NumberOfYears')

    numerator, denominator = 1, 1

    # remember that warranty and useful life provisions are by regclass, not sourcetype
    scaling_dict_key = ((rc, ft, scaling_metric), alt)
    if scaled_by == 'Warranty':
        scaling_dict = InputFileDict(settings.warranty_inputs_dict)
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, f'{model_year}')
    elif scaled_by == 'Usefullife':
        scaling_dict = InputFileDict(settings.usefullife_inputs_dict)
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, f'{model_year}')
    else:
        pass

    if scaler == 'Absolute':
        denominator = scaling_dict.get_attribute_value(scaling_dict_key, '2024')
    elif scaler == 'Relative':
        denominator = scaling_dict.get_attribute_value(scaling_dict_key, str(int(model_year) - int(num_years)))
    else:
        pass

    project_markup_value = input_markup_value * (numerator / denominator)

    return project_markup_value


def calc_per_veh_indirect_costs(settings, averages_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        averages_dict: Dictionary; contains tech package direct costs/vehicle.

    Returns:
        The averages_dict dictionary updated with indirect costs associated with each markup value along with the summation of those individual indirect
        costs as "IndirectCost_AvgPerVeh."

    """
    print('\nCalculating CAP per vehicle indirect costs...')
    calcs_avg = FleetAverages(averages_dict)
    markup_factors = settings.markup_factors_unique_names.copy()

    age0_keys = [k for k, v in averages_dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = (rc, ft)

        temp_dict = dict()
        ic_sum = 0
        for markup_factor in markup_factors:
            markup_value = calc_project_markup_value(settings, engine, alt, markup_factor, model_year)
            per_veh_direct_cost = calcs_avg.get_attribute_value(key, 'DirectCost_AvgPerVeh')
            cost = markup_value * per_veh_direct_cost
            temp_dict[f'{markup_factor}Cost_AvgPerVeh'] = cost
            ic_sum += cost

        temp_dict['IndirectCost_AvgPerVeh'] = ic_sum
        calcs_avg.update_dict(key, temp_dict)

    return averages_dict


def calc_indirect_costs(settings, totals_dict, averages_dict, sales_arg):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: Dictionary; contains sales data (e.g., sales_arg at age=0).\n
        averages_dict: Dictionary; contains individual indirect costs per vehicle.\n
        sales_arg: String; specifies the sales attribute to use (e.g., "VPOP" or "VPOP_withTech")

    Returns:
        The totals_dict dictionary updated with total indirect costs for each individual indirect cost property and a summation of those.

    """
    print('\nCalculating CAP total indirect costs...')

    markup_factors = settings.markup_factors_unique_names.copy()
    markup_factors.append('Indirect')

    calcs_avg = FleetAverages(averages_dict)
    calcs = FleetTotals(totals_dict)

    age0_keys = [k for k, v in totals_dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        temp_dict = dict()
        for markup_factor in markup_factors:
            cost_per_veh = calcs_avg.get_attribute_value(key, f'{markup_factor}Cost_AvgPerVeh')
            sales = calcs.get_attribute_value(key, sales_arg)
            cost = cost_per_veh * sales
            temp_dict[f'{markup_factor}Cost'] = cost

        calcs.update_dict(key, temp_dict)

    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
