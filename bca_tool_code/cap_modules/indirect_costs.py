

def calc_project_markup_value(settings, engine, alt, markup_factor_name, model_year):
    """

    This function calculates the project markup value for the markup_factor (Warranty, RnD, Other, Profit) passed.

    Parameters:
        settings: The SetInputs classs.\n
        engine:  Tuple; represents a regclass_fueltype engine.\n
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
    rc, ft = engine

    markups_key = ft, alt, markup_factor_name
    scaling_metric = settings.general_inputs.get_attribute_value('indirect_cost_scaling_metric')  # scaling metric will be 'Miles' or 'Age'
    input_markup_value, scaler, scaled_by, num_years = settings.markups.get_attribute_value(markups_key, 'Value'), \
                                                       settings.markups.get_attribute_value(markups_key, 'Scaler'), \
                                                       settings.markups.get_attribute_value(markups_key, 'Scaled_by'), \
                                                       settings.markups.get_attribute_value(markups_key, 'NumberOfYears')

    numerator, denominator = 1, 1

    # remember that warranty and useful life provisions are by regclass, not sourcetype
    scaling_dict_key = ((rc, ft), alt, scaling_metric)
    if scaled_by == 'Warranty':
        scaling_dict = settings.warranty
        numerator = scaling_dict.get_attribute_value(scaling_dict_key, f'{model_year}')
    elif scaled_by == 'Usefullife':
        scaling_dict = settings.useful_life
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


def calc_indirect_costs_per_veh(settings, data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        Updates to the fleet dictionary to include indirect costs per vehicle in sum and for each contribution factor.

    """
    print('\nCalculating Indirect costs per vehicle...')
    markup_factors = settings.markups.markup_factor_names

    age0_keys = [k for k, v in data_object._dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = rc, ft

        update_dict = dict()
        ic_sum = 0
        for markup_factor in markup_factors:
            markup_value = calc_project_markup_value(settings, engine, alt, markup_factor, model_year)
            package_cost_per_veh = data_object.get_attribute_value(key, 'DirectCost_PerVeh')
            cost = markup_value * package_cost_per_veh
            update_dict[f'{markup_factor}Cost_PerVeh'] = cost
            ic_sum += cost

        update_dict['IndirectCost_PerVeh'] = ic_sum
        data_object.update_dict(key, update_dict)


def calc_indirect_costs(settings, data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        Updates to the fleet dictionary to include total indirect costs in sum and for each contribution factor.

    """
    print('\nCalculating Indirect costs...')

    markup_factors = settings.markups.markup_factor_names
    markup_factors.append('Indirect')

    age0_keys = [k for k, v in data_object._dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        update_dict = dict()
        for markup_factor in markup_factors:
            cost_per_veh = data_object.get_attribute_value(key, f'{markup_factor}Cost_PerVeh')
            sales = data_object.get_attribute_value(key, 'VPOP')
            cost = cost_per_veh * sales
            update_dict[f'{markup_factor}Cost'] = cost

        data_object.update_dict(key, update_dict)
