import pandas as pd


def calc_def_doserate(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object. \n
        vehicle: tuple; (sourcetype_id, regclass_id, fueltype_id).\n

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
        settings: object; the SetInputs class object. \n
        data_object: object; the fleet data object.\n
        key: tuple; ((sourcetype_id, regclass_id, fueltype_id), alt, model year, age, discount rate).

    Returns:
        The NOx reduction for the passed model year vehicle at the given age.

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
        settings: object; the SetInputs class object.\n
        data_object: object; the fleet data object.

    Returns:
        Updates the data_object dictionary with costs associated with DEF consumption.

    """
    print('\nCalculating DEF costs...')
    def_gallons_per_ton_nox_reduction \
        = pd.to_numeric(settings.general_inputs.get_attribute_value('def_gallons_per_ton_nox_reduction'))

    # Note: use keys where fueltype_id=2 (i.e., diesel, since they are the only vehicles that use DEF)
    for key in data_object.ft2_keys:
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
        data_object: object; the fleet data object.

    Returns:
        Updates the data_object dictionary with costs/mile and costs/vehicle associated with DEF consumption.

    """
    print('\nCalculating DEF average costs...')

    for key in data_object.ft2_keys:
        def_cost = data_object.get_attribute_value(key, 'DEFCost')
        vmt = data_object.get_attribute_value(key, 'VMT')
        vpop = data_object.get_attribute_value(key, 'VPOP')
        cost_per_mile = def_cost / vmt
        cost_per_veh = def_cost / vpop

        update_dict = {'DEFCost_PerMile': cost_per_mile,
                       'DEFCost_PerVeh': cost_per_veh,
                       }
        data_object.update_dict(key, update_dict)
