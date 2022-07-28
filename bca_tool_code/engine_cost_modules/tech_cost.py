def calc_tech_cost(settings, vehicle):
    """

    Parameters:
        vehicle: object; an object of the Vehicle class.

    Returns:
        The tech cost per vehicle and tech cost (direct plus indirect).

    """
    key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id, 0

    attribute_names = ['DirectCost_PerVeh', 'IndirectCost_PerVeh', 'ReplacementCost_PerVeh']

    direct_cost, indirect_cost, replacement_cost = settings.cap_costs.get_attribute_values(key, *attribute_names)

    cost_per_veh = direct_cost + indirect_cost + replacement_cost
    cost = cost_per_veh * vehicle.vpop

    return cost_per_veh, cost
