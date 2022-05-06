

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
    scaling_dict_key = ((rc, ft), option_id, scaling_metric)
    scaling_dict = dict()
    if scaled_by == 'Warranty':
        scaling_dict = settings.warranty
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, f'{modelyear_id}')
    elif scaled_by == 'Usefullife':
        scaling_dict = settings.useful_life
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, f'{modelyear_id}')
    else:
        pass

    if scaler == 'Absolute':
        denominator = scaling_dict.get_attribute_value(scaling_dict_key, '2024')
    elif scaler == 'Relative':
        denominator = scaling_dict.get_attribute_value(scaling_dict_key, str(int(modelyear_id) - int(num_years)))
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
        return_dict.update({f'{markup_factor}_cost_per_veh': cost_per_veh})
    return_dict.update({'ic_sum_per_veh': ic_sum_per_veh})

    for markup_factor in markup_factors:
        markup_value = calc_project_markup_value(settings, vehicle, markup_factor)
        cost = markup_value * pkg_cost * vehicle.vpop
        ic_sum += cost
        return_dict.update({f'{markup_factor}_cost': cost})
    return_dict.update({'ic_sum': ic_sum})

    return return_dict
