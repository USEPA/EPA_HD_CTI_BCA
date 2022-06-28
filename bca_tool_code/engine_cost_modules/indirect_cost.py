

def calc_project_markup_value(settings, vehicle, markup_factor_name):
    """

    This function calculates the project markup value for the passed markup_factor (Warranty, RnD, Other, Profit).

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.
        markup_factor_name: str; represents the name of the project markup factor value to return (warranty, r and d,
        other, etc.).

    Returns:
        A single markup factor value to be used in the project having been adjusted in accordance with the proposed
        warranty and useful life changes and the Absolute/Relative scaling entries.

    Note:
        The project markup factor differs from the input markup factors by scaling where that scaling is done based on
        the "Absolute" or "Relative" entries in the input file and by the scaling metric (Miles or Age) entries of the
        warranty/useful life input files. Whether Miles or Age is used is set via the BCA_General_Inputs file.

    """
    rc, ft = vehicle.engine_id
    option_id, modelyear_id = vehicle.option_id, vehicle.modelyear_id

    markups_key = ft, option_id, markup_factor_name
    scaling_metric = settings.general_inputs.get_attribute_value('indirect_cost_scaling_metric')  # scaling metric will be 'Miles' or 'Age'
    input_markup_value, scaler, scaled_by, num_years = settings.markups.get_attribute_values(markups_key)

    numerator, denominator = 1, 1

    # remember that warranty and useful life provisions are by regclass, not sourcetype
    scaling_dict_key = ((rc, ft), option_id, modelyear_id, scaling_metric)
    scaling_dict = dict()
    if scaled_by == 'Warranty':
        scaling_dict = settings.warranty
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, 'period_value')
    elif scaled_by == 'Usefullife':
        scaling_dict = settings.useful_life
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, 'period_value')
    else:
        pass

    if scaler == 'Absolute':
        scaling_dict_key = ((rc, ft), option_id, 2024, scaling_metric)
        denominator = scaling_dict.get_attribute_value(scaling_dict_key, 'period_value')
    elif scaler == 'Relative':
        scaling_dict_key = ((rc, ft), option_id, modelyear_id - int(num_years), scaling_metric)
        denominator = scaling_dict.get_attribute_value(scaling_dict_key, 'period_value')
    else:
        pass

    project_markup_value = input_markup_value * (numerator / denominator)

    return project_markup_value


def calc_indirect_cost(settings, vehicle, pkg_cost):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.
        pkg_cost: numeric; the direct manufacturing cost for the given vehicle.

    Returns:
        A dictionary of indirect cost contributors and their values.

    """
    markup_factors = settings.markups.markup_factor_names

    ic_sum_per_veh = 0
    ic_sum = 0
    return_dict = dict()
    for markup_factor in markup_factors:
        markup_value = calc_project_markup_value(settings, vehicle, markup_factor)
        cost_per_veh = markup_value * pkg_cost
        ic_sum_per_veh += cost_per_veh
        return_dict.update({
            'optionID': vehicle.option_id,
            'engineID': vehicle.engine_id,
            'regClassID': vehicle.regclass_id,
            'fuelTypeID': vehicle.fueltype_id,
            'modelYearID': vehicle.modelyear_id,
            'optionName': vehicle.option_name,
            'regClassName': vehicle.regclass_name,
            'fuelTypeName': vehicle.fueltype_name,
            f'{markup_factor}_cost_per_veh': cost_per_veh,
            f'{markup_factor}_factor': markup_value,
        })
    return_dict.update({
        'ic_sum_per_veh': ic_sum_per_veh,
        'effective_markup': (pkg_cost + ic_sum_per_veh) / pkg_cost
    })
    settings.markups.update_contribution_factors(vehicle, return_dict)

    for markup_factor in markup_factors:
        cost = return_dict[f'{markup_factor}_cost_per_veh'] * vehicle.vpop
        ic_sum += cost
        return_dict.update({f'{markup_factor}_cost': cost})
    return_dict.update({'ic_sum': ic_sum})

    return return_dict


def calc_indirect_cost_new_warranty(settings, vehicle, pkg_cost):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.
        pkg_cost: numeric; the direct manufacturing cost for the given vehicle.

    Returns:
        A dictionary of indirect cost contributors and their values.

    """
    markup_factors = settings.markups.markup_factor_names

    ic_sum_per_veh = 0
    ic_sum = 0
    return_dict = dict()
    for markup_factor in markup_factors:
        if markup_factor == 'Warranty':
            key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id
            markup_value = 'na'
            cost_per_veh = settings.emission_repair_cost.repair_cost_details[key]['warranty_cost_per_veh']
        else:
            markup_value = calc_project_markup_value(settings, vehicle, markup_factor)
            cost_per_veh = markup_value * pkg_cost
        ic_sum_per_veh += cost_per_veh
        return_dict.update({
            'optionID': vehicle.option_id,
            'vehicleID': vehicle.vehicle_id,
            'engineID': vehicle.engine_id,
            'sourceTypeID': vehicle.sourcetype_id,
            'regClassID': vehicle.regclass_id,
            'fuelTypeID': vehicle.fueltype_id,
            'modelYearID': vehicle.modelyear_id,
            'optionName': vehicle.option_name,
            'sourceTypeName': vehicle.sourcetype_name,
            'regClassName': vehicle.regclass_name,
            'fuelTypeName': vehicle.fueltype_name,
            f'{markup_factor}Cost_PerVeh': cost_per_veh,
            f'{markup_factor}_factor': markup_value,
        })
    return_dict.update({
        'ic_sum_per_veh': ic_sum_per_veh,
        'effective_markup': (pkg_cost + ic_sum_per_veh) / pkg_cost
    })
    settings.markups.update_contribution_factors(vehicle, return_dict)

    for markup_factor in markup_factors:
        cost = return_dict[f'{markup_factor}Cost_PerVeh'] * vehicle.vpop
        ic_sum += cost
        return_dict.update({f'{markup_factor}Cost': cost})
    return_dict.update({'ic_sum': ic_sum})

    return return_dict
