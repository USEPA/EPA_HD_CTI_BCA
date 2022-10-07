def calc_tech_cost(settings, vehicle):
    """

    Parameters:
        settings: object; an object of the SetInputs class.
        vehicle: object; an object of the Vehicle class.

    Returns:
        The tech cost per vehicle and tech cost (direct plus indirect).

    """
    key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id, 0
    replacement_cost = 0

    if settings.replacement_costs:
        attribute_names = [
            'DirectCost_PerVeh',
            'IndirectCost_PerVeh',
            'ReplacementCost_PerVeh'
        ]
        direct_cost, indirect_cost, replacement_cost = settings.cost_calcs.get_attribute_values(key, *attribute_names)

    else:
        attribute_names = [
            'DirectCost_PerVeh',
            'IndirectCost_PerVeh'
        ]
        direct_cost, indirect_cost = settings.cost_calcs.get_attribute_values(key, *attribute_names)

    cost_per_veh = direct_cost + indirect_cost + replacement_cost
    cost = cost_per_veh * vehicle.vpop

    return cost_per_veh, cost
