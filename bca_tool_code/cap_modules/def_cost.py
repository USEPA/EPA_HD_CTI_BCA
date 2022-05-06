import pandas as pd


def calc_def_doserate(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object. \n
        vehicle: object; an object of the Vehicle class.

    Returns:
        The DEF dose rate for the passed vehicle (engine) based on the DEF dose rate input file.

    """
    nox_std = settings.def_doserates.get_attribute_value(vehicle.engine_id, 'standard_NOx')
    nox_engine_out = settings.def_doserates.get_attribute_value(vehicle.engine_id, 'engineout_NOx')
    slope, intercept = settings.def_doserates.get_curve_coefficients(vehicle.engine_id)
    base_doserate = ((nox_std - nox_engine_out) - intercept) / slope

    return base_doserate


def calc_nox_reduction(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object. \n
        vehicle: object; an object of the Vehicle class.

    Returns:
        The NOx reduction for the passed vehicle.

    Notes:
        The nox_reduction calculation should be done such that it is positive if action has lower nox than no action.

    """
    if vehicle.option_id == settings.no_action_alt:
        nox_reduction = 0
    else:
        nox_no_action = [v.nox_ustons for v in settings.fleet_cap.vehicles_no_action
                         if v.vehicle_id == vehicle.vehicle_id
                         and v.option_id == settings.no_action_alt
                         and v.modelyear_id == vehicle.modelyear_id][0]
        nox_action = vehicle.nox_ustons
        nox_reduction = nox_no_action - nox_action

    return nox_reduction


def calc_def_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        The DEF cost per vehicle and DEF cost for the given vehicle object.

    """
    def_gallons_per_ton_nox_reduction \
        = pd.to_numeric(settings.general_inputs.get_attribute_value('def_gallons_per_ton_nox_reduction'))

    def_price = settings.def_prices.get_price(vehicle.year_id)
    gallons_fuel = vehicle.gallons
    base_doserate = calc_def_doserate(settings, vehicle)
    nox_reduction = calc_nox_reduction(settings, vehicle)

    gallons_def = gallons_fuel * base_doserate + nox_reduction * def_gallons_per_ton_nox_reduction
    cost = def_price * gallons_def
    try:
        cost_per_veh = cost / vehicle.vpop
        cost_per_mile = cost / vehicle.vmt
    except ZeroDivisionError:
        cost_per_veh = 0
        cost_per_mile = 0

    return cost_per_veh, cost, cost_per_mile
