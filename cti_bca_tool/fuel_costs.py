orvr_adjust_dict = dict()


def get_orvr_adjustment(settings, vehicle):
    alt, st, rc, ft = vehicle
    key = (alt, rc, ft)
    if key in orvr_adjust_dict:
        adjustment = orvr_adjust_dict[key]
    else:
        adjustment = settings.orvr_inputs_dict[key]['ml/g']
        orvr_adjust_dict[key] = adjustment
    return adjustment


def calc_thc_reduction(vehicle, year, model_year, fleet_totals_dict):
    """

    :param settings: The SetInputs class.
    :param vehicle: An alt_st_rc_ft vehicle
    :param year: The calendar year (yearID).
    :param model_year: The model year.
    :param fleet_dict: The fleet dictionary.
    :return: The THC reduction in terms of the no action case less the action case (larger no action emissions result in positive reductions).
    """
    alt, st, rc, ft = vehicle
    age = year - model_year
    thc_reduction = fleet_totals_dict[((0, st, rc, ft), model_year, age)]['THC_UStons'] - fleet_totals_dict[((vehicle), model_year, age)]['THC_UStons']
    return thc_reduction


def calc_adjusted_gallons(settings, vehicle, year, model_year, fleet_totals_dict):
    age = year - model_year
    key = ((vehicle), model_year, age)
    adjustment = get_orvr_adjustment(settings, vehicle)
    thc_reduction = calc_thc_reduction(vehicle, year, model_year, fleet_totals_dict)
    old_gallons = fleet_totals_dict[key]['Gallons']
    adjusted_gallons = old_gallons - thc_reduction * adjustment * settings.grams_per_short_ton * settings.gallons_per_ml
    return adjusted_gallons


def calc_fuel_costs(settings, fleet_totals_dict):
    print('\nCalculating fuel total costs.\n')
    for key in fleet_totals_dict.keys():
        alt, st, rc, ft = key[0]
        vehicle, model_year, age = key[0], key[1], key[2]
        year = model_year + age
        fuel_price_retail = settings.fuel_prices_dict[(year, ft)]['retail_fuel_price']
        fuel_price_pretax = settings.fuel_prices_dict[(year, ft)]['pretax_fuel_price']
        if ft == 1:
            gallons = calc_adjusted_gallons(settings, vehicle, year, model_year, fleet_totals_dict)
            fleet_totals_dict[key].update({'Gallons': gallons})
        else:
            gallons = fleet_totals_dict[key]['Gallons']
        fleet_totals_dict[key].update({'FuelCost_Retail': fuel_price_retail * gallons})
        fleet_totals_dict[key].update({'FuelCost_Pretax': fuel_price_pretax * gallons})
    return fleet_totals_dict


def calc_average_fuel_costs(fleet_totals_dict, fleet_averages_dict):
    print('\nCalculating fuel average cost per mile and per vehicle.')
    for key in fleet_averages_dict.keys():
        fuel_cost = fleet_totals_dict[key]['FuelCost_Retail']
        vmt = fleet_totals_dict[key]['VMT']
        vpop = fleet_totals_dict[key]['VPOP']
        fleet_averages_dict[key].update({'FuelCost_Retail_AvgPerMile': fuel_cost / vmt})
        fleet_averages_dict[key].update({'FuelCost_Retail_AvgPerVeh': fuel_cost / vpop})
    return fleet_averages_dict


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    vehicles_st = sourcetype_vehicles(project_fleet_df)

    fleet_totals_dict = calc_fuel_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_fuel_costs(fleet_totals_dict, fleet_averages_dict)

    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
