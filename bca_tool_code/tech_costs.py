

def calc_tech_costs_per_veh(data_object, attribute_name):
    """
    
    Parameters:
        data_object: Object; the fleet data object.\n
        attribute_name: String; the name of the package cost attribute, e.g., 'Direct' or 'Tech.'\n

    Returns:
        Updates to the fleet dictionary to include average tech costs per vehicle (direct plus indirect).

    Note:
        Direct and indirect costs apply only for ageID=0 (i.e., new sales).

    """
    print('\nCalculating technology costs per vehicle...')

    age0_keys = [k for k, v in data_object._dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost = data_object.get_attribute_value(key, f'{attribute_name}Cost_PerVeh')
        cost += data_object.get_attribute_value(key, 'IndirectCost_PerVeh')

        update_dict = {'TechCost_PerVeh': cost}
        data_object.update_dict(key, update_dict)


def calc_tech_costs(data_object, sales_arg):
    """

    Parameters:
        data_object: Object; the fleet data object.\n
        sales_arg: String; the sales to use when calculating sales * cost/veh.

    Returns:
        Updates to the fleet dictionary to include annual technology costs for all vehicles.

    """
    print('\nCalculating technology costs...')

    age0_keys = [k for k, v in data_object._dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost_per_veh = data_object.get_attribute_value(key, 'TechCost_PerVeh')
        sales = data_object.get_attribute_value(key, sales_arg)
        cost = cost_per_veh * sales

        update_dict = {'TechCost': cost}
        data_object.update_dict(key, update_dict)
