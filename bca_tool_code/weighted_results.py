from bca_tool_code.vehicle import Vehicle


def create_weighted_cost_dict(settings, fleet_averages_dict, arg_to_weight, arg_to_weight_by):
    """This function weights arguments by the passed weight_by argument.

    Parameters::
        settings: The SetInputs class.\n
        fleet_averages_dict: A dictionary of fleet average data (e.g., miles/year, cost/year, cost/mile).\n
        arg_to_weight: The argument to be weighted by the arg_to_weight_by argument.\n
        arg_to_weight_by: The argument to weight by.

    Returns:
        A dictionary of arguments weighted by the weight_by argument.

    Note:
        The weighting is limited by the number of years (ages) to be included which is set in the general inputs file. The weighting is also
        limited to model years for which sufficient data exits to include all of those ages. For example, if the maximum calendar year included
        in the input data is 2045, and the maximum numbers of ages of data to include for each model year is 9 (which would be 10 years of age
        since year 1 is age 0) then the maximum model year included will be 2035.

    """
    print(f'\nCalculating weighted {arg_to_weight}...')
    wtd_result_dict = dict()
    weighted_results_dict = dict()
    for key in fleet_averages_dict.keys():
        vehicle, alt, model_year, age_id = key[0], key[1], key[2], key[3]
        st, rc, ft = vehicle
        if arg_to_weight == 'DEFCost_AvgPerMile' and ft != 2:
            pass
        else:
            if model_year <= (settings.year_max - settings.max_age_included - 1):
                # print(f'Calculating weighted {arg_to_weight} for {vehicle}, optionID {alt}, MY {model_year}')
                wtd_result_dict_id = (vehicle, alt, model_year)
                numerator, denominator = 0, 0
                if wtd_result_dict_id in wtd_result_dict:
                    numerator, denominator = wtd_result_dict[wtd_result_dict_id]['numerator'], wtd_result_dict[wtd_result_dict_id]['denominator']
                else:
                    pass
                if age_id <= settings.max_age_included:
                    numerator += fleet_averages_dict[key][arg_to_weight] * fleet_averages_dict[key][arg_to_weight_by]
                    denominator += fleet_averages_dict[key]['VMT_AvgPerVeh']
                    wtd_result_dict[wtd_result_dict_id] = {'numerator': numerator, 'denominator': denominator}
    for key in wtd_result_dict.keys():
        numerator, denominator = wtd_result_dict[key]['numerator'], wtd_result_dict[key]['denominator']
        vehicle, alt = key[0], key[1]
        st, rc, ft = vehicle
        source_type = Vehicle(st).sourcetype_name()
        weighted_results_dict[key] = {'optionID': alt, 'sourceTypeName': source_type, 'cents_per_mile': 100 * numerator / denominator}
    return weighted_results_dict
