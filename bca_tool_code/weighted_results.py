import pandas as pd


def create_weighted_cost_dict(settings, data_object, year_max, destination_dict, arg_to_weight=None, arg_to_weight_by=None):
    """

    This function weights 'arg_to_weight' attributes by the 'arg_to_weight_by' attribute.

    Parameters::
        settings: object; the SetInputs class object.\n
        data_object: object; the fleet data object.\n
        year_id_max: int; the max calendar year of the input data.\n
        destination_dict: Dictionary into which to place results.\n
        arg_to_weight: str; the attribute to be weighted by the arg_to_weight_by argument.\n
        arg_to_weight_by: str; the argument to weight by.

    Returns:
        Updates the destination_dict dictionary of arguments weighted by the weight_by argument.

    Note:
        The weighting is limited by the number of year_ids (ages) to be included which is set in the general inputs file.
        The weighting is also limited to model year_ids for which sufficient data exits to include all of those ages. For
        example, if the maximum calendar year included in the input data is 2045, and the maximum numbers of ages of
        data to include for each model year is 9 (which would be 10 year_ids of age since year 1 is age 0) then the maximum
        model year included will be 2035.

    """
    print(f'\nCalculating weighted {arg_to_weight}...')

    wtd_result_dict = dict()

    max_age_included = pd.to_numeric(settings.general_inputs.get_attribute_value('weighted_operating_cost_thru_ageID'))

    keys_dr0 = [k for k,v in data_object.results.items() if v['DiscountRate'] == 0]

    for key in keys_dr0:
        vehicle_id, option_id, modelyear_id, age_id, discount_rate = key
        sourcetype_id, regclass_id, fueltype_id = vehicle_id
        if arg_to_weight == 'DEFCost_PerMile' and fueltype_id != 2:
            pass
        else:
            if modelyear_id <= (year_max - max_age_included - 1):
                wtd_result_dict_key = (vehicle_id, option_id, modelyear_id)
                numerator, denominator = 0, 0
                if wtd_result_dict_key in wtd_result_dict:
                    numerator = wtd_result_dict[wtd_result_dict_key]['numerator']
                    denominator = wtd_result_dict[wtd_result_dict_key]['denominator']
                else:
                    pass
                if age_id <= max_age_included:
                    arg_weight = data_object.results[key][arg_to_weight]
                    arg_weight_by = data_object.results[key][arg_to_weight_by]
                    numerator += arg_weight * arg_weight_by
                    denominator += data_object.results[key][arg_to_weight_by]
                    wtd_result_dict[wtd_result_dict_key] = {
                        'optionID': option_id,
                        'sourceTypeID': sourcetype_id,
                        'regClassID': regclass_id,
                        'fuelTypeID': fueltype_id,
                        'modelYearID': modelyear_id,
                        'optionName': data_object.results[key]['optionName'],
                        'sourceTypeName': data_object.results[key]['sourceTypeName'],
                        'regClassName': data_object.results[key]['regClassName'],
                        'fuelTypeName': data_object.results[key]['fuelTypeName'],
                        'numerator': numerator,
                        'denominator': denominator
                    }
    for key in wtd_result_dict:
        numerator = wtd_result_dict[key]['numerator']
        denominator = wtd_result_dict[key]['denominator']
        cpm = 100 * numerator / denominator
        destination_dict[key] = {
            'optionID': wtd_result_dict[key]['optionID'],
            'sourceTypeID': wtd_result_dict[key]['sourceTypeID'],
            'regClassID': wtd_result_dict[key]['regClassID'],
            'fuelTypeID': wtd_result_dict[key]['fuelTypeID'],
            'modelYearID': wtd_result_dict[key]['modelYearID'],
            'optionName': wtd_result_dict[key]['optionName'],
            'sourceTypeName': wtd_result_dict[key]['sourceTypeName'],
            'regClassName': wtd_result_dict[key]['regClassName'],
            'fuelTypeName': wtd_result_dict[key]['fuelTypeName'],
            'cents_per_mile': cpm,
        }
