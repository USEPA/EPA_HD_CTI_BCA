import pandas as pd


def calc_def_doserate(settings, vehicle):
    """

    Parameters:
        settings: The SetInputs class \n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n

    Returns:
        The DEF dose rate for the passed vehicle (engine) based on the DEF dose rate input file.

    """
    st, rc, ft = vehicle
    engine = rc, ft
    nox_std = settings.def_doserates.get_attribute_value(engine, 'standard_NOx')
    nox_engine_out = settings.def_doserates.get_attribute_value(engine, 'engineout_NOx')
    slope, intercept = settings.def_doserates.get_curve_coefficients(engine)
    base_doserate = ((nox_std - nox_engine_out) - intercept) / slope

    return base_doserate


def calc_nox_reduction(settings, data_object, key):
    """

    Parameters:
        settings: The SetInputs class. \n
        data_object: Object; the fleet data object.\n
        key: Tuple; represents the vehicle, alt, model year, age and discount rate.

    Returns:
        The NOx reduction for the passed model year vehicle in the given calendar year.

    Notes:
        The nox_reduction calculation should be done such that it is positive if action has lower nox than no action.

    """
    vehicle, alt, model_year, age_id, disc_rate = key
    no_action_key = vehicle, settings.no_action_alt, model_year, age_id, disc_rate
    nox_no_action = data_object.get_attribute_value(no_action_key, 'NOx_UStons')
    nox_action = data_object.get_attribute_value(key, 'NOx_UStons')
    nox_reduction = nox_no_action - nox_action

    return nox_reduction


def calc_def_costs(settings, data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        The passed dictionary updated with costs associated with DEF consumption.

    """
    print('\nCalculating DEF costs...')

    # get keys where fueltype=2 (Diesel since they are the only vehicles that use DEF)
    ft2_keys = [k for k, v in data_object._dict.items() if v['fuelTypeID'] == 2]

    def_gallons_per_ton_nox_reduction \
        = pd.to_numeric(settings.general_inputs.get_attribute_value('def_gallons_per_ton_nox_reduction'))

    for key in ft2_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        calendar_year = model_year + age_id

        def_price = settings.def_prices.get_price(calendar_year)
        gallons_fuel = data_object.get_attribute_value(key, 'Gallons')
        base_doserate = calc_def_doserate(settings, vehicle)
        nox_reduction = calc_nox_reduction(settings, data_object, key)

        gallons_def = gallons_fuel * base_doserate + nox_reduction * def_gallons_per_ton_nox_reduction
        cost = def_price * gallons_def

        update_dict = {'DEF_Gallons': gallons_def,
                       'DEFCost': cost,
                       }
        data_object.update_dict(key, update_dict)


def calc_def_costs_per_veh(data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        Updates the fleet dictionary with costs/mile and costs/vehicle associated with DEF consumption.

    """
    print('\nCalculating DEF average costs...')

    # get keys where fueltype=2 (Diesel since they are the only vehicles that use DEF)
    ft2_keys = [k for k, v in data_object._dict.items() if v['fuelTypeID'] == 2]

    for key in ft2_keys:
        def_cost = data_object.get_attribute_value(key, 'DEFCost')
        vmt = data_object.get_attribute_value(key, 'VMT')
        vpop = data_object.get_attribute_value(key, 'VPOP')
        cost_per_mile = def_cost / vmt
        cost_per_veh = def_cost / vpop

        update_dict = {'DEFCost_PerMile': cost_per_mile,
                       'DEFCost_PerVeh': cost_per_veh,
                       }
        data_object.update_dict(key, update_dict)