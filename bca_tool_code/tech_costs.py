

def calc_tech_costs_per_veh(settings):
    """
    
    Parameters:
        settings: The SetInputs class.

    Returns:
        The averages_dict dictionary updated with average tech costs per vehicle (direct plus indirect).

    Note:
        Direct and indirect costs apply only for ageID=0 (i.e., new sales).

    """
    print('\nCalculating technology costs per vehicle...')

    age0_keys = [k for k, v in settings.fleet_cap._data.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost = settings.fleet_cap.get_attribute_value(key, 'DirectCost_PerVeh')
        cost += settings.fleet_cap.get_attribute_value(key, 'IndirectCost_PerVeh')

        update_dict = {'TechCost_PerVeh': cost}
        settings.fleet_cap.update_dict(key, update_dict)


def calc_tech_costs(settings, sales_arg):
    """

    Parameters:
        settings: The SetInputs class.\n
        sales_arg: String; the sales to use when calculating sales * cost/veh.

    Returns:
        The totals_dict dictionary updated with annual technology costs for all vehicles.

    """
    print('\nCalculating technology costs...')

    age0_keys = [k for k, v in settings.fleet_cap._data.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost_per_veh = settings.fleet_cap.get_attribute_value(key, 'TechCost_PerVeh')
        sales = settings.fleet_cap.get_attribute_value(key, sales_arg)
        cost = cost_per_veh * sales

        update_dict = {'TechCost': cost}
        settings.fleet_cap.update_dict(key, update_dict)
