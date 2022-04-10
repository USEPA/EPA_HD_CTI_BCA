

def calc_criteria_emission_costs(settings):
    """
    
    Parameters:
        settings: The SetInputs class.

    Returns:
        Updates the fleet dictionary with emission costs ($/ton * inventory tons).

    """
    cap_dr1 = settings.general_inputs.get_attribute_value('criteria_discount_rate_1')
    cap_dr2 = settings.general_inputs.get_attribute_value('criteria_discount_rate_2')

    for key in settings.fleet_cap._dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        calendar_year = model_year + age_id
        
        factors = ['pm25_tailpipe', 'nox_tailpipe']
        pm_tailpipe_dr1, pm_tailpipe_dr2, nox_tailpipe_dr1, nox_tailpipe_dr2 \
            = settings.dollar_per_ton_cap.get_factors(settings, calendar_year, *factors)

        pm_tons = settings.fleet_cap.get_attribute_value(key, 'PM25_UStons')
        nox_tons = settings.fleet_cap.get_attribute_value(key, 'NOx_UStons')

        update_dict = {f'PM25Cost_tailpipe_{str(cap_dr1)}': pm_tailpipe_dr1 * pm_tons,
                       f'PM25Cost_tailpipe_{str(cap_dr2)}': pm_tailpipe_dr2 * pm_tons,
                       f'NOxCost_tailpipe_{str(cap_dr1)}': nox_tailpipe_dr1 * nox_tons,
                       f'NOxCost_tailpipe_{str(cap_dr2)}': nox_tailpipe_dr2 * nox_tons,
                       f'CriteriaCost_tailpipe_{str(cap_dr1)}': pm_tailpipe_dr1 * pm_tons + nox_tailpipe_dr1 * nox_tons,
                       f'CriteriaCost_tailpipe_{str(cap_dr2)}': pm_tailpipe_dr2 * pm_tons + nox_tailpipe_dr2 * nox_tons}

        settings.fleet_cap.update_dict(key, update_dict)
