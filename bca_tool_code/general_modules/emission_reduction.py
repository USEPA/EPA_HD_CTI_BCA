
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
                         and v.modelyear_id == vehicle.modelyear_id
                         and v.age_id == vehicle.age_id][0]
        nox_action = vehicle.nox_ustons
        nox_reduction = nox_no_action - nox_action

    return nox_reduction


def calc_thc_reduction(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object. \n
        vehicle: object; an object of the Vehicle class.

    Returns:
        The THC reduction for the given vehicle object.

    Notes:
        The thc_reduction calculation should be done such that it is positive if action has lower thc than no action.

    """
    if vehicle.option_id == settings.no_action_alt:
        thc_reduction = 0
    else:
        thc_no_action = [v.thc_ustons for v in settings.fleet_cap.vehicles_no_action
                         if v.vehicle_id == vehicle.vehicle_id
                         and v.option_id == settings.no_action_alt
                         and v.modelyear_id == vehicle.modelyear_id
                         and v.age_id == vehicle.age_id][0]
        thc_action = vehicle.thc_ustons
        thc_reduction = thc_no_action - thc_action

    return thc_reduction
