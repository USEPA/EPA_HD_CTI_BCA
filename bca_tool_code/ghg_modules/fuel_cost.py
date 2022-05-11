
def calc_fuel_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        Average retail fuel cost per vehicle, retail fuel cost, pretax fuel cost and retail cost per mile associated
        with the passed vehicle.

    """
    prices = ['retail_fuel_price', 'pretax_fuel_price']
    price_retail, price_pretax = settings.fuel_prices.get_price(vehicle.year_id, vehicle.fueltype_id, *prices)

    gallons_paid_for = vehicle.gallons

    cost_retail = price_retail * gallons_paid_for
    cost_pretax = price_pretax * gallons_paid_for

    try:
        cost_per_mile = cost_retail / vehicle.vmt
        cost_per_veh = cost_retail / vehicle.vpop
    except ZeroDivisionError:
        cost_per_mile = 0
        cost_per_veh = 0

    return cost_per_veh, cost_retail, cost_pretax, cost_per_mile
