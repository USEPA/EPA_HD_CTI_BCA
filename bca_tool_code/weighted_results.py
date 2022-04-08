import pandas as pd

from bca_tool_code.vehicle import Vehicle


def create_weighted_cost_dict(settings, input_dict, arg_to_weight, arg_to_weight_by):
    """
    This function weights 'arg_to_weight' attributes by the 'arg_to_weight_by' attribute.

    Parameters::
        settings: The SetInputs class.\n
        input_dict: Dictionary into which to place results.
        arg_to_weight: String; the attribute to be weighted by the arg_to_weight_by argument.\n
        arg_to_weight_by: String; the argument to weight by.

    Returns:
        A dictionary of arguments weighted by the weight_by argument.

    Note:
        The weighting is limited by the number of years (ages) to be included which is set in the general inputs file.
        The weighting is also limited to model years for which sufficient data exits to include all of those ages. For
        example, if the maximum calendar year included in the input data is 2045, and the maximum numbers of ages of
        data to include for each model year is 9 (which would be 10 years of age since year 1 is age 0) then the maximum
        model year included will be 2035.

    """
    print(f'\nCalculating weighted {arg_to_weight}...')

    wtd_result_dict = dict()

    max_age_included = pd.to_numeric(settings.general_inputs.get_attribute_value('weighted_operating_cost_thru_ageID'))

    for key in settings.fleet_cap._data.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        if arg_to_weight == 'DEFCost_PerMile' and ft != 2:
            pass
        else:
            if model_year <= (settings.fleet_cap.year_max - max_age_included - 1):
                wtd_result_dict_id = (vehicle, alt, model_year)
                numerator, denominator = 0, 0
                if wtd_result_dict_id in wtd_result_dict:
                    numerator = wtd_result_dict[wtd_result_dict_id]['numerator']
                    denominator = wtd_result_dict[wtd_result_dict_id]['denominator']
                else:
                    pass
                if age_id <= max_age_included:
                    arg_weight = settings.fleet_cap.get_attribute_value(key, arg_to_weight)
                    arg_weight_by = settings.fleet_cap.get_attribute_value(key, arg_to_weight_by)
                    numerator += arg_weight * arg_weight_by
                    denominator += settings.fleet_cap.get_attribute_value(key, arg_to_weight_by)
                    wtd_result_dict[wtd_result_dict_id] = {'numerator': numerator, 'denominator': denominator}
    for key in wtd_result_dict.keys():
        numerator = wtd_result_dict[key]['numerator']
        denominator = wtd_result_dict[key]['denominator']
        vehicle, alt = key[0], key[1]
        st, rc, ft = vehicle
        source_type = Vehicle(st).sourcetype_name()
        input_dict[key] = {'optionID': alt,
                           'sourceTypeName': source_type,
                           'cents_per_mile': 100 * numerator / denominator}
