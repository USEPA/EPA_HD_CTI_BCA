def calc_tech_cost(vehicle, pkg_cost_per_veh, indirect_cost_per_veh):
    """

    Parameters:
        vehicle: object; an object of the Vehicle class.
        pkg_cost: numeric; the direct manufacturing cost for the given vehicle.
        ic_sum: numeric; the indirect costs (the sum of all indirect cost contributors) for the given vehicle.

    Returns:
        The tech cost per vehicle and tech cost (direct plus indirect).

    """
    cost_per_veh = pkg_cost_per_veh + indirect_cost_per_veh
    cost = cost_per_veh * vehicle.vpop

    return cost_per_veh, cost
