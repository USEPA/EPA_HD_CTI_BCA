import pandas as pd
from itertools import product


def get_emission_cost_factors(settings, year):
    pm_low_3, pm_high_3, pm_low_7, pm_high_7 = settings.criteria_cost_factors_dict[year]['pm25_low-mortality_0.03_USD_per_uston'], \
                                               settings.criteria_cost_factors_dict[year]['pm25_high-mortality_0.03_USD_per_uston'], \
                                               settings.criteria_cost_factors_dict[year]['pm25_low-mortality_0.07_USD_per_uston'], \
                                               settings.criteria_cost_factors_dict[year]['pm25_high-mortality_0.07_USD_per_uston']
    nox_low_3, nox_high_3, nox_low_7, nox_high_7 = settings.criteria_cost_factors_dict[year]['nox_low-mortality_0.03_USD_per_uston'], \
                                                   settings.criteria_cost_factors_dict[year]['nox_high-mortality_0.03_USD_per_uston'], \
                                                   settings.criteria_cost_factors_dict[year]['nox_low-mortality_0.07_USD_per_uston'], \
                                                   settings.criteria_cost_factors_dict[year]['nox_high-mortality_0.07_USD_per_uston']
    return pm_low_3, pm_high_3, pm_low_7, pm_high_7, nox_low_3, nox_high_3, nox_low_7, nox_high_7


def calc_criteria_emission_costs(settings, fleet_totals_dict):
    for key in fleet_totals_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        print(f'Calculating criteria emission costs for {vehicle}, MY {model_year}, age {age_id}')
        year = model_year + age_id
        pm_low_3, pm_high_3, pm_low_7, pm_high_7, nox_low_3, nox_high_3, nox_low_7, nox_high_7 = get_emission_cost_factors(settings, year)
        pm_tons = fleet_totals_dict[key]['PM25_UStons']
        nox_tons = fleet_totals_dict[key]['NOx_UStons']
        update_dict = {'PM25Cost_low_0.03': pm_low_3 * pm_tons,
                       'PM25Cost_high_0.03': pm_high_3 * pm_tons,
                       'PMCost_low_0.07': pm_low_7 * pm_tons,
                       'PMCost_high_0.07': pm_high_7 * pm_tons,
                       'NOxCost_low_0.03': nox_low_3 * nox_tons,
                       'NOxCost_high_0.03': nox_high_3 * nox_tons,
                       'NOxCost_low_0.07': nox_low_7 * nox_tons,
                       'NOxCost_high_0.07': nox_high_7 * nox_tons,
                       'CriteriaCost_low_0.03': pm_low_3 * pm_tons + nox_low_3 * nox_tons,
                       'CriteriaCost_high_0.03': pm_high_3 * pm_tons + nox_high_3 * nox_tons,
                       'CriteriaCost_low_0.07': pm_low_7 * pm_tons + nox_low_7 * nox_tons,
                       'CriteriaCost_high_0.07': pm_high_7 * pm_tons + nox_high_7 * nox_tons,
                       }
        fleet_totals_dict[key].update(update_dict)
    return fleet_totals_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)

    fleet_totals_dict = calc_criteria_emission_costs(settings, fleet_totals_dict)
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/emission_costs', 'vehicle', 'modelYearID', 'ageID')
