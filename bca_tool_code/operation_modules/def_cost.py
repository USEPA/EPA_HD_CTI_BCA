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


def calc_def_cost(settings, vehicle, nox_reduction=None):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.\n
        nox_reduction: numeric; the nox_reduction, if applicable, for the vehicle relative to its no_action state.

    Returns:
        The DEF cost per vehicle, the corresponding DEF cost, the DEF cost per mile and the gallons of DEF consumed.

    """
    def_gallons_per_ton_nox_reduction \
        = pd.to_numeric(settings.general_inputs.get_attribute_value('def_gallons_per_ton_nox_reduction'))

    def_price = settings.def_prices.get_price(vehicle.year_id)
    gallons_fuel = vehicle.gallons
    base_doserate = calc_def_doserate(settings, vehicle)
    # nox_reduction = calc_nox_reduction(settings, vehicle)

    gallons_def = gallons_fuel * base_doserate + nox_reduction * def_gallons_per_ton_nox_reduction
    cost = def_price * gallons_def
    try:
        cost_per_veh = cost / vehicle.vpop
        cost_per_mile = cost / vehicle.vmt
    except ZeroDivisionError:
        cost_per_veh = 0
        cost_per_mile = 0

    return cost_per_veh, cost, cost_per_mile, gallons_def
