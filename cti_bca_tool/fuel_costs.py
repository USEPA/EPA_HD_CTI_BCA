orvr_adjust_dict = dict()


def get_orvr_adjustment(settings, vehicle):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.

    Returns:
        A single value representing the milliliter per gram adjustment to be applied to total hydrocarbon emission reductions to
        estimate the gallons of fuel saved.

    """
    alt, st, rc, ft = vehicle
    orvr_adjust_dict_id = (alt, rc, ft)
    if orvr_adjust_dict_id in orvr_adjust_dict.keys():
        adjustment = orvr_adjust_dict[orvr_adjust_dict_id]
    else:
        adjustment = settings.orvr_inputs_dict[orvr_adjust_dict_id]['ml/g']
        orvr_adjust_dict[orvr_adjust_dict_id] = adjustment
    return adjustment


def calc_thc_reduction(settings, vehicle, year, model_year, totals_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.\n
        year: The calendar year.\n
        model_year: The model year of the passed vehicle.\n
        totals_dict: A dictionary of fleet total hydrocarbon (THC) tons by vehicle.

    Returns:
        A single THC reduction for the given model year vehicle in the given year.

    """
    alt, st, rc, ft = vehicle
    age = year - model_year
    thc_reduction = totals_dict[((settings.no_action_alt, st, rc, ft), model_year, age, 0)]['THC_UStons'] \
                    - totals_dict[(vehicle, model_year, age, 0)]['THC_UStons']
    return thc_reduction


def calc_adjusted_gallons(settings, vehicle, year, model_year, totals_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.\n
        year: The calendar year.\n
        model_year: The model year of the passed vehicle.\n
        totals_dict: A dictionary of fleet Gallons consumed by all vehicles.

    Returns:
        The passed dictionary updated to reflect fuel consumption (Gallons) adjusted to account for the fuel saved in associated with  ORVR.

    """
    age = year - model_year
    totals_dict_key = (vehicle, model_year, age, 0)
    adjustment = get_orvr_adjustment(settings, vehicle)
    thc_reduction = calc_thc_reduction(settings, vehicle, year, model_year, totals_dict)
    old_gallons = totals_dict[totals_dict_key]['Gallons']
    adjusted_gallons = old_gallons - thc_reduction * adjustment * settings.grams_per_short_ton * settings.gallons_per_ml
    return adjusted_gallons


def calc_fuel_costs(settings, totals_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: A dictionary of fleet Gallons consumed by all vehicles.

    Returns:
        The passed dictionary updated to reflect fuel consumption (Gallons) adjusted to account for the fuel saved in association with ORVR.
        The dictionary is also updated to include the fuel costs associated with the gallons consumed (Gallons * $/gallon fuel).

    Note:
        Note that these fuel impacts are not included in the MOVES runs that serve as the input fleet data for the tool.

    """
    print('\nCalculating fuel total costs.\n')
    for key in totals_dict.keys():
        vehicle, model_year, age_id, disc_rate = key
        alt, st, rc, ft = vehicle
        year = model_year + age_id
        fuel_price_retail = settings.fuel_prices_dict[(year, ft)]['retail_fuel_price']
        fuel_price_pretax = settings.fuel_prices_dict[(year, ft)]['pretax_fuel_price']
        if ft == 1:
            gallons = calc_adjusted_gallons(settings, vehicle, year, model_year, totals_dict)
            totals_dict[key].update({'Gallons': gallons})
        else:
            gallons = totals_dict[key]['Gallons']
        totals_dict[key].update({'FuelCost_Retail': fuel_price_retail * gallons})
        totals_dict[key].update({'FuelCost_Pretax': fuel_price_pretax * gallons})
    return totals_dict


def calc_average_fuel_costs(totals_dict, averages_dict):
    """

    Parameters:
        totals_dict: A dictionary of fleet "ORVR adjusted" Gallons consumed by all vehicles.\n
        averages_dict: A dictionary into which fuel costs/vehicle and costs/mile will be updated.

    Returns:
        The passed averages_dict updated to include fuel costs/vehicle and costs/mile.

    """
    for key in averages_dict.keys():
        vehicle, model_year, age_id, disc_rate = key
        print(f'Calculating fuel average cost per mile and per vehicle for {vehicle}, MY {model_year}, age {age_id}')
        fuel_cost = totals_dict[key]['FuelCost_Retail']
        vmt = totals_dict[key]['VMT']
        vpop = totals_dict[key]['VPOP']
        averages_dict[key].update({'FuelCost_Retail_AvgPerMile': fuel_cost / vmt})
        averages_dict[key].update({'FuelCost_Retail_AvgPerVeh': fuel_cost / vpop})
    return averages_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    vehicles_st = sourcetype_vehicles(project_fleet_df)

    fleet_totals_dict = calc_fuel_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_fuel_costs(fleet_totals_dict, fleet_averages_dict)

    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
