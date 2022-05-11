import pandas as pd


def calc_fuel_cost(settings, vehicle, thc_reduction=None):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.\n
        thc_reduction: numeric: the thc_reduction, if applicable, for the vehicle relative to its no_action state.

    Returns:
        Average retail fuel cost per vehicle, retail fuel cost, pretax fuel cost and retail cost per mile, and the
        gallons of gasoline captured by ORVR, associated with the passed vehicle.

    Note:
        Note that gallons of fuel captured are not included in the MOVES runs that serve as the input fleet data for the
        tool although the inventory impacts are included in the MOVES runs.

    """
    gallons_per_ml = pd.to_numeric(settings.general_inputs.get_attribute_value('gallons_per_ml'))
    grams_per_short_ton = pd.to_numeric(settings.general_inputs.get_attribute_value('grams_per_short_ton'))

    captured_gallons = 0
    prices = ['retail_fuel_price', 'pretax_fuel_price']
    price_retail, price_pretax = settings.fuel_prices.get_price(vehicle.year_id, vehicle.fueltype_id, *prices)

    # calculate gallons that would have evaporated without new ORVR, if applicable
    if thc_reduction and vehicle.fueltype_id == 1:
        orvr_adjustment = settings.orvr_fuelchanges_cap.get_ml_per_gram(vehicle.engine_id, vehicle.option_id)
        captured_gallons = thc_reduction * orvr_adjustment * grams_per_short_ton * gallons_per_ml

    gallons = vehicle.gallons
    gallons_paid_for = gallons - captured_gallons

    cost_retail = price_retail * gallons_paid_for
    cost_pretax = price_pretax * gallons_paid_for

    try:
        cost_per_mile = cost_retail / vehicle.vmt
        cost_per_veh = cost_retail / vehicle.vpop
    except ZeroDivisionError:
        cost_per_mile = 0
        cost_per_veh = 0

    return cost_per_veh, cost_retail, cost_pretax, cost_per_mile, captured_gallons
