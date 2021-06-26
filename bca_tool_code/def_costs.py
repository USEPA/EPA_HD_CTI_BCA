

base_doserate_dict = dict()


def calc_def_doserate(settings, vehicle, alt):
    """

    Parameters:
        settings: The SetInputs class. \n
        vehicle: A tuple representing a sourcetype_regclass_fueltype vehicle.\n
        alt: The Alternative or option ID.

    Returns:
        The DEF dose rate for the passed vehicle based on the DEF dose rate input file.

    """
    st, rc, ft = vehicle
    base_doserate_dict_id = (rc, ft)
    if base_doserate_dict_id in base_doserate_dict.keys():
        base_doserate = base_doserate_dict[base_doserate_dict_id]
    else:
        nox_std = settings.def_doserate_inputs_dict[(rc, ft)]['standard_NOx']
        nox_engine_out = settings.def_doserate_inputs_dict[(rc, ft)]['engineout_NOx']
        doserate_intercept = settings.def_doserate_inputs_dict[(rc, ft)]['intercept_DEFdoserate']
        doserate_slope = settings.def_doserate_inputs_dict[(rc, ft)]['slope_DEFdoserate']
        base_doserate = ((nox_std - nox_engine_out) - doserate_intercept) / doserate_slope
        base_doserate_dict[base_doserate_dict_id] = base_doserate
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
    age_id = year - model_year
    nox_reduction = totals_dict[(vehicle, settings.no_action_alt, model_year, age_id, 0)]['NOx_UStons'] \
                    - totals_dict[(vehicle, alt, model_year, age_id, 0)]['NOx_UStons']
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
    age_id = year - model_year
    gallons_fuel = totals_dict[(vehicle, alt, model_year, age_id, 0)]['Gallons']
    base_doserate = calc_def_doserate(settings, vehicle, alt)
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
    print('\nCalculating total DEF costs.')
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        if ft == 2:
            year = model_year + age_id
            def_price = settings.def_prices_dict[year]['DEF_USDperGal']
            gallons_def = calc_def_gallons(settings, vehicle, alt, year, model_year, totals_dict)
            totals_dict[key].update({'DEF_Gallons': gallons_def, 'DEFCost': def_price * gallons_def})
    return totals_dict


def calc_average_def_costs(totals_dict, averages_dict):
    """

    Parameters:
        totals_dict: A dictionary of fleet DEF costs by vehicle. \n
        averages_dict: A dictionary into which DEF costs/vehicle will be updated.

    Returns:
        The passed dictionary updated with costs/mile and costs/vehicle associated with DEF consumption.

    """
    for key in averages_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        if ft == 2:
            print(f'Calculating DEF average cost per mile for {vehicle}, option ID {alt}, MY {model_year}, age {age_id}.')
            def_cost = totals_dict[key]['DEFCost']
            vmt = totals_dict[key]['VMT']
            vpop = totals_dict[key]['VPOP']
            averages_dict[key].update({'DEFCost_AvgPerMile': def_cost / vmt})
            averages_dict[key].update({'DEFCost_AvgPerVeh': def_cost / vpop})
    return averages_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
