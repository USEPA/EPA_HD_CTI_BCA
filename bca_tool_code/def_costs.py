from bca_tool_code.fleet_dicts_cap import FleetTotalsCAP, FleetAveragesCAP


def calc_def_doserate(settings, vehicle):
    """

    Parameters:
        settings: The SetInputs class. \n
        vehicle: A tuple representing a sourcetype_regclass_fueltype vehicle.\n

    Returns:
        The DEF dose rate for the passed vehicle based on the DEF dose rate input file.

    """
    st, rc, ft = vehicle
    nox_std = settings.def_doserate_inputs_dict[(rc, ft)]['standard_NOx']
    nox_engine_out = settings.def_doserate_inputs_dict[(rc, ft)]['engineout_NOx']
    doserate_intercept = settings.def_doserate_inputs_dict[(rc, ft)]['intercept_DEFdoserate']
    doserate_slope = settings.def_doserate_inputs_dict[(rc, ft)]['slope_DEFdoserate']
    base_doserate = ((nox_std - nox_engine_out) - doserate_intercept) / doserate_slope
    return base_doserate


def calc_nox_reduction(settings, vehicle, alt, year, model_year, totals_dict):
    """

    Parameters:
        settings: The SetInputs class. \n
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle. \n
        year: The calendar year (yearID). \n
        model_year: The model year of the passed vehicle. \n
        totals_dict: A dictionary of fleet NOx tons by vehicle.

    Returns:
        The NOx reduction for the passed model year vehicle in the given calendar year.

    """
    calcs = FleetTotalsCAP(totals_dict)
    age_id = year - model_year
    nox_no_action = calcs.get_attribute_value((vehicle, settings.no_action_alt, model_year, age_id, 0), 'NOx_UStons')
    nox_action = calcs.get_attribute_value((vehicle, alt, model_year, age_id, 0), 'NOx_UStons')
    nox_reduction = nox_no_action - nox_action
    return nox_reduction


def calc_def_gallons(settings, vehicle, alt, year, model_year, totals_dict):
    """

    Parameters:
        settings: The SetInputs class. \n
        vehicle: A tuple representing a sourcetype_regclass_fueltype vehicle. \n
        alt: The Alternative or option ID. \n
        year: The calendar year (yearID). \n
        model_year: The model year of the passed vehicle. \n
        totals_dict: A dictionary of fleet Gallons (fuel consumption) by vehicle.

    Returns:
        The gallons of DEF consumption for the passed model year vehicle in the given calendar year.

    """
    calcs = FleetTotalsCAP(totals_dict)
    age_id = year - model_year
    gallons_fuel = calcs.get_attribute_value((vehicle, alt, model_year, age_id, 0), 'Gallons')
    base_doserate = calc_def_doserate(settings, vehicle)
    nox_reduction = calc_nox_reduction(settings, vehicle, alt, year, model_year, totals_dict)
    gallons_def = gallons_fuel * base_doserate + nox_reduction * settings.def_gallons_per_ton_nox_reduction
    return gallons_def


def calc_def_costs(settings, totals_dict):
    """

    Parameters:
        settings: The SetInputs class. \n
        totals_dict: A dictionary of fleet DEF consumption by vehicle.

    Returns:
        The passed dictionary updated with costs associated with DEF consumption.

    """
    print('\nCalculating DEF total costs...')
    calcs = FleetTotalsCAP(totals_dict)
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        if ft == 2:
            year = model_year + age_id
            def_price = settings.def_prices_dict[year]['DEF_USDperGal']
            gallons_def = calc_def_gallons(settings, vehicle, alt, year, model_year, totals_dict)
            cost = def_price * gallons_def
            calcs.update_dict(key, 'DEF_Gallons', gallons_def)
            calcs.update_dict(key, 'DEFCost', cost)
    return totals_dict


def calc_average_def_costs(totals_dict, averages_dict):
    """

    Parameters:
        totals_dict: A dictionary of fleet DEF costs by vehicle. \n
        averages_dict: A dictionary into which DEF costs/vehicle will be updated.

    Returns:
        The passed dictionary updated with costs/mile and costs/vehicle associated with DEF consumption.

    """
    print('\nCalculating DEF average costs...')

    calcs_avg = FleetAveragesCAP(averages_dict)
    calcs = FleetTotalsCAP(totals_dict)
    for key in averages_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        if ft == 2:
            def_cost = calcs.get_attribute_value(key, 'DEFCost')
            vmt = calcs.get_attribute_value(key, 'VMT')
            vpop = calcs.get_attribute_value(key, 'VPOP')
            cost_per_mile = def_cost / vmt
            cost_per_veh = def_cost / vpop
            calcs_avg.update_dict(key, 'DEFCost_AvgPerMile', cost_per_mile)
            calcs_avg.update_dict(key, 'DEFCost_AvgPerVeh', cost_per_veh)
    return averages_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
