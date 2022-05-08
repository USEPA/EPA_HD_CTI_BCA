def calc_criteria_emission_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        An update_dict for use in updating the cost results dictionary.

    """
    cap_dr1 = settings.general_inputs.get_attribute_value('criteria_discount_rate_1')
    cap_dr2 = settings.general_inputs.get_attribute_value('criteria_discount_rate_2')

    vehicle, alt, model_year, age_id, disc_rate = key
    calendar_year = model_year + age_id

    factors = ('pm25_tailpipe', 'nox_tailpipe')
    pm25_tailpipe_dr1, pm25_tailpipe_dr2, nox_tailpipe_dr1, nox_tailpipe_dr2 \
        = settings.dollar_per_ton_cap.get_factors(settings, calendar_year, *factors)

    pm25_tons = vehicle.pm25_ustons
    nox_tons = vehicle.nox_ustons

    update_dict = {f'PM25Cost_tailpipe_{str(cap_dr1)}': pm25_tailpipe_dr1 * pm25_tons,
                   f'PM25Cost_tailpipe_{str(cap_dr2)}': pm25_tailpipe_dr2 * pm25_tons,
                   f'NOxCost_tailpipe_{str(cap_dr1)}': nox_tailpipe_dr1 * nox_tons,
                   f'NOxCost_tailpipe_{str(cap_dr2)}': nox_tailpipe_dr2 * nox_tons,
                   f'CriteriaCost_tailpipe_{str(cap_dr1)}': pm25_tailpipe_dr1 * pm25_tons + nox_tailpipe_dr1 * nox_tons,
                   f'CriteriaCost_tailpipe_{str(cap_dr2)}': pm25_tailpipe_dr2 * pm25_tons + nox_tailpipe_dr2 * nox_tons}

    return update_dict
