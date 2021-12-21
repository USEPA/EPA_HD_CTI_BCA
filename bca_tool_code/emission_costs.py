from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.project_dicts import InputFileDict


def get_criteria_cost_factors(settings, calendar_year):
    """

    Parameters:
        settings: The SetInputs class.\n
        calendar_year: Numeric; the calendar year for which emission cost factors are needed.

    Returns:
        Six values - the PM25, NOx and SO2 emission cost factors (dollars/ton) for each of two different mortality estimates and each of two
        different discount rates.

    Note:
        Note that the BCA_General_Inputs file contains a toggle to stipulate whether to estimate emission (pollution) costs or not. This function is called
        only if that toggle is set to 'Y' (yes). The default setting is 'N' (no).

    """
    cost_factors = InputFileDict(settings.criteria_cost_factors_dict)

    cap_dr1 = settings.criteria_discount_rate_1
    cap_dr2 = settings.criteria_discount_rate_2

    pm_tailpipe_cap_dr1, pm_tailpipe_cap_dr2 = cost_factors.get_attribute_value(calendar_year, f'pm25_tailpipe_{str(cap_dr1)}_USD_per_uston'), \
                                               cost_factors.get_attribute_value(calendar_year, f'pm25_tailpipe_{str(cap_dr2)}_USD_per_uston')
    nox_tailpipe_cap_dr1, nox_tailpipe_cap_dr2 = cost_factors.get_attribute_value(calendar_year, f'nox_tailpipe_{str(cap_dr1)}_USD_per_uston'), \
                                                 cost_factors.get_attribute_value(calendar_year, f'nox_tailpipe_{str(cap_dr2)}_USD_per_uston')
    so2_tailpipe_cap_dr1, so2_tailpipe_cap_dr2 = cost_factors.get_attribute_value(calendar_year, f'so2_tailpipe_{str(cap_dr1)}_USD_per_uston'), \
                                               cost_factors.get_attribute_value(calendar_year, f'so2_tailpipe_{str(cap_dr2)}_USD_per_uston')

    return pm_tailpipe_cap_dr1, pm_tailpipe_cap_dr2, \
           nox_tailpipe_cap_dr1, nox_tailpipe_cap_dr2, \
           so2_tailpipe_cap_dr1, so2_tailpipe_cap_dr2


def calc_criteria_emission_costs(settings, totals_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        totals_dict: Dictionary; into which emission costs will be updated.

    Returns:
        The totals_dict dictionary updated with emission costs ($/ton * inventory tons).

    """
    calcs = FleetTotals(totals_dict)

    cap_dr1 = settings.criteria_discount_rate_1
    cap_dr2 = settings.criteria_discount_rate_2

    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id = key[0], key[1], key[2], key[3]
        calendar_year = model_year + age_id
        pm_tailpipe_cap_dr1, pm_tailpipe_cap_dr2, nox_tailpipe_cap_dr1, nox_tailpipe_cap_dr2, so2_tailpipe_cap_dr1, so2_tailpipe_cap_dr2 \
            = get_criteria_cost_factors(settings, calendar_year)

        pm_tons = calcs.get_attribute_value(key, 'PM25_UStons')
        nox_tons = calcs.get_attribute_value(key, 'NOx_UStons')
        # so2_tons = calcs.get_attribute_value(key, 'SO2_UStons')

        calcs.update_dict(key, f'PM25Cost_tailpipe_{str(cap_dr1)}', pm_tailpipe_cap_dr1 * pm_tons)
        calcs.update_dict(key, f'PM25Cost_tailpipe_{str(cap_dr2)}', pm_tailpipe_cap_dr2 * pm_tons)
        calcs.update_dict(key, f'NOxCost_tailpipe_{str(cap_dr1)}', nox_tailpipe_cap_dr1 * nox_tons)
        calcs.update_dict(key, f'NOxCost_tailpipe_{str(cap_dr2)}', nox_tailpipe_cap_dr2 * nox_tons)
        calcs.update_dict(key, f'CriteriaCost_tailpipe_{str(cap_dr1)}', pm_tailpipe_cap_dr1 * pm_tons + nox_tailpipe_cap_dr1 * nox_tons)
        calcs.update_dict(key, f'CriteriaCost_tailpipe_{str(cap_dr2)}', pm_tailpipe_cap_dr2 * pm_tons + nox_tailpipe_cap_dr2 * nox_tons)

    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
