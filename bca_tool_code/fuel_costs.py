orvr_adjust_dict = dict()


def get_orvr_adjustment(settings, vehicle, alt):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing a sourcetype_regclass_fueltype vehicle.\n
        alt: The Alternative or option ID.

    Returns:
        A single value representing the milliliter per gram adjustment to be applied to total hydrocarbon emission reductions to
        estimate the gallons of fuel saved.

    """
    st, rc, ft = vehicle
    engine = (rc, ft)
    orvr_adjust_dict_id = (engine, alt)
    if orvr_adjust_dict_id in orvr_adjust_dict.keys():
        adjustment = orvr_adjust_dict[orvr_adjust_dict_id]
    else:
        adjustment = settings.orvr_inputs_dict[orvr_adjust_dict_id]['ml/g']
        orvr_adjust_dict[orvr_adjust_dict_id] = adjustment
    return adjustment


def calc_thc_reduction(settings, vehicle, alt, year, model_year, totals_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing a sourcetype_regclass_fueltype vehicle.\n
        alt: The Alternative or option ID.\n
        year: The calendar year.\n
        model_year: The model year of the passed vehicle.\n
        totals_dict: A dictionary of fleet total hydrocarbon (THC) tons by vehicle.

    Returns:
        A single THC reduction for the given model year vehicle in the given year.

    """
    age = year - model_year
    thc_reduction = totals_dict[(vehicle, settings.no_action_alt, model_year, age, 0)]['THC_UStons'] \
                    - totals_dict[(vehicle, alt, model_year, age, 0)]['THC_UStons']
    return thc_reduction


def calc_captured_gallons(settings, vehicle, alt, year, model_year, totals_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        vehicle: A tuple representing a sourcetype_regclass_fueltype vehicle.\n
        alt: The Alternative or option ID.\n
        year: The calendar year.\n
        model_year: The model year of the passed vehicle.\n
        totals_dict: A dictionary of fleet Gallons consumed by all vehicles.

    Returns:
        The gallons captured by ORVR that would have otherwise evaporated during refueling.

    """
    age = year - model_year
    # totals_dict_key = (vehicle, alt, model_year, age, 0)
    adjustment = get_orvr_adjustment(settings, vehicle, alt)
    thc_reduction = calc_thc_reduction(settings, vehicle, alt, year, model_year, totals_dict)
    # old_gallons = totals_dict[totals_dict_key]['Gallons']
    # adjusted_gallons = old_gallons - thc_reduction * adjustment * settings.grams_per_short_ton * settings.gallons_per_ml
    captured_gallons = thc_reduction * adjustment * settings.grams_per_short_ton * settings.gallons_per_ml
    return captured_gallons


def calc_cap_fuel_costs(settings, totals_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: A dictionary of fleet Gallons consumed by all vehicles.

    Returns:
        The passed dictionary updated to reflect fuel consumption (Gallons) adjusted to account for the fuel saved in association with ORVR.
        The dictionary is also updated to include the fuel costs associated with the gallons consumed (Gallons * $/gallon fuel).

    Note:
        Note that gallons of fuel captured are not included in the MOVES runs that serve as the input fleet data for the tool although the inventory impacts
        are included in the MOVES runs.

    """
    print('\nCalculating CAP-related fuel costs.\n')
    captured_gallons = 0
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        year = model_year + age_id
        fuel_price_retail = settings.fuel_prices_dict[(year, ft)]['retail_fuel_price']
        fuel_price_pretax = settings.fuel_prices_dict[(year, ft)]['pretax_fuel_price']
        if ft == 1:
            captured_gallons = calc_captured_gallons(settings, vehicle, alt, year, model_year, totals_dict)
        totals_dict[key]['GallonsCaptured_byORVR'] = captured_gallons
        gallons_paid_for = totals_dict[key]['Gallons'] - captured_gallons
        totals_dict[key].update({'FuelCost_Retail': fuel_price_retail * gallons_paid_for})
        totals_dict[key].update({'FuelCost_Pretax': fuel_price_pretax * gallons_paid_for})
    return totals_dict


def calc_ghg_fuel_costs(settings, totals_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: A dictionary of fleet Gallons consumed by all vehicles.

    Returns:
        The passed dictionary updated to reflect fuel consumption (Gallons) adjusted to account for the fuel saved in association with ORVR.
        The dictionary is also updated to include the fuel costs associated with the gallons consumed (Gallons * $/gallon fuel).

    """
    print('\nCalculating GHG_related fuel costs.\n')
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        year = model_year + age_id
        fuel_price_retail = settings.fuel_prices_dict[(year, ft)]['retail_fuel_price']
        fuel_price_pretax = settings.fuel_prices_dict[(year, ft)]['pretax_fuel_price']
        gallons = totals_dict[key]['Gallons']
        totals_dict[key].update({'FuelCost_Retail': fuel_price_retail * gallons})
        totals_dict[key].update({'FuelCost_Pretax': fuel_price_pretax * gallons})
    return totals_dict


def calc_average_fuel_costs(totals_dict, averages_dict):
    """

    Parameters:
        totals_dict: A dictionary of fleet fuel costs for all vehicles.\n
        averages_dict: A dictionary into which fuel costs/vehicle and costs/mile will be updated.

    Returns:
        The passed averages_dict updated to include fuel costs/vehicle and costs/mile.

    """
    for key in averages_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        print(f'Calculating fuel average cost per mile and per vehicle for {vehicle}, option ID {alt}, MY {model_year}, age {age_id}')
        fuel_cost = totals_dict[key]['FuelCost_Retail']
        vmt = totals_dict[key]['VMT']
        vpop = totals_dict[key]['VPOP']
        averages_dict[key].update({'FuelCost_Retail_AvgPerMile': fuel_cost / vmt})
        averages_dict[key].update({'FuelCost_Retail_AvgPerVeh': fuel_cost / vpop})
    return averages_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
