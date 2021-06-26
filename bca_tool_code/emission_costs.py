import pandas as pd
from itertools import product


def get_emission_cost_factors(settings, year):
    """

    Parameters:
        settings: The SetInputs class.\n
        year: The calendar year for which emission cost factors are needed.

    Returns:
        Eight values - the PM25 and NOx emission cost factors (dollars/ton) for each of two different mortality estimates and each of two
        different discount rates.

    Note:
        Note that the BCA_General_Inputs file contains a toggle to stipulate whether to estimate emission (pollution) costs or not. This function is called
        only if that toggle is set to 'Y' (yes). The default setting is 'N' (no).

    """
    cap_dr1 = settings.criteria_discount_rate_1
    cap_dr2 = settings.criteria_discount_rate_2
    pm_tailpipe_cap_dr1, pm_tailpipe_cap_dr2 = settings.criteria_cost_factors_dict[year][f'pm25_tailpipe_{str(cap_dr1)}_USD_per_uston'], \
                                               settings.criteria_cost_factors_dict[year][f'pm25_tailpipe_{str(cap_dr2)}_USD_per_uston']
    nox_tailpipe_cap_dr1, nox_tailpipe_cap_dr2 = settings.criteria_cost_factors_dict[year][f'nox_tailpipe_{str(cap_dr1)}_USD_per_uston'], \
                                                 settings.criteria_cost_factors_dict[year][f'nox_tailpipe_{str(cap_dr2)}_USD_per_uston']
    return pm_tailpipe_cap_dr1, pm_tailpipe_cap_dr2, nox_tailpipe_cap_dr1, nox_tailpipe_cap_dr2


def calc_criteria_emission_costs(settings, totals_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        totals_dict: A dictionary into which emission costs will be updated.

    Returns:
        The totals_dict dictionary updated with emission costs ($/ton * inventory tons).

    """
    cap_dr1 = settings.criteria_discount_rate_1
    cap_dr2 = settings.criteria_discount_rate_2
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id = key[0], key[1], key[2], key[3]
        print(f'Calculating criteria emission costs for {vehicle}, optionID {alt}, MY {model_year}, age {age_id}')
        year = model_year + age_id
        pm_tailpipe_cap_dr1, pm_tailpipe_cap_dr2, nox_tailpipe_cap_dr1, nox_tailpipe_cap_dr2 = get_emission_cost_factors(settings, year)
        pm_tons = totals_dict[key]['PM25_UStons']
        nox_tons = totals_dict[key]['NOx_UStons']
        update_dict = {f'PM25Cost_tailpipe_{str(cap_dr1)}': pm_tailpipe_cap_dr1 * pm_tons,
                       f'PM25Cost_tailpipe_{str(cap_dr2)}': pm_tailpipe_cap_dr2 * pm_tons,
                       f'NOxCost_tailpipe_{str(cap_dr1)}': nox_tailpipe_cap_dr1 * nox_tons,
                       f'NOxCost_tailpipe_{str(cap_dr2)}': nox_tailpipe_cap_dr2 * nox_tons,
                       f'CriteriaCost_{str(cap_dr1)}': pm_tailpipe_cap_dr1 * pm_tons + nox_tailpipe_cap_dr1 * nox_tons,
                       f'CriteriaCost_{str(cap_dr2)}': pm_tailpipe_cap_dr2 * pm_tons + nox_tailpipe_cap_dr2 * nox_tons,
                       }
        totals_dict[key].update(update_dict)
    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
