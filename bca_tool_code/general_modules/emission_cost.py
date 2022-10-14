def calc_criteria_emission_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        An update_dict for use in updating the cost results dictionary.

    Note:
        This function is not being used so may not work properly.

    """
    cap_dr1 = settings.general_inputs.get_attribute_value('criteria_discount_rate_1')
    cap_dr2 = settings.general_inputs.get_attribute_value('criteria_discount_rate_2')

    factors = ('pm25_tailpipe', 'nox_tailpipe')
    pm25_tailpipe_dr1, pm25_tailpipe_dr2, nox_tailpipe_dr1, nox_tailpipe_dr2 \
        = settings.dollar_per_ton_cap.get_factors(settings, vehicle.year_id, *factors)

    pm25_tons = vehicle.pm25_ustons
    nox_tons = vehicle.nox_ustons

    update_dict = {f'PM25Cost_tailpipe_{str(cap_dr1)}': pm25_tailpipe_dr1 * pm25_tons,
                   f'PM25Cost_tailpipe_{str(cap_dr2)}': pm25_tailpipe_dr2 * pm25_tons,
                   f'NOxCost_tailpipe_{str(cap_dr1)}': nox_tailpipe_dr1 * nox_tons,
                   f'NOxCost_tailpipe_{str(cap_dr2)}': nox_tailpipe_dr2 * nox_tons,
                   f'CriteriaCost_tailpipe_{str(cap_dr1)}': pm25_tailpipe_dr1 * pm25_tons + nox_tailpipe_dr1 * nox_tons,
                   f'CriteriaCost_tailpipe_{str(cap_dr2)}': pm25_tailpipe_dr2 * pm25_tons + nox_tailpipe_dr2 * nox_tons}

    return update_dict


def calc_ghg_emission_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        An update_dict for use in updating the cost results dictionary.

    Note:
        This function is not being used so may not work properly.

    """
    ghgs = ['CO2', 'N2O', 'CH4']
    rates = ['0.05', '0.03', '0.025', '0.03_95']

    cost_factors = settings.cost_factors_scc.get_factors(vehicle.year_id)

    ustons = dict()
    ustons['CO2'], ustons['N2O'], ustons['CH4'] = vehicle.co2_ustons, vehicle.n2o_ustons, vehicle.ch4_ustons

    conversion_factor = int(settings.general_inputs.get_attribute_value('grams_per_short_ton')) / 1000000

    tons = dict()
    for ghg in ghgs:
        tons[ghg] = ustons[ghg] * conversion_factor

    update_dict = dict()
    for rate in rates:
        rate_sum = 0
        for ghg in ghgs:
            factor_name = f'{ghg}_global_{rate}_USD_per_metricton'
            cost = tons[ghg] * cost_factors[factor_name]
            update_dict.update({f'{ghg}Cost_tailpipe_{rate}': cost})
            rate_sum += cost
        update_dict.update({f'GHGCost_tailpipe_{rate}': rate_sum})

    return update_dict
