from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages


def calc_per_veh_tech_costs(averages_dict):
    """
    
    Parameters::
        averages_dict: Dictionary; contains average direct and indirect costs per vehicle.

    Returns:
        The averages_dict dictionary updated with average tech costs per vehicle (direct plus indirect).

    Note:
        Direct and indirect costs apply only for ageID=0 (i.e., new sales).

    """
    print('\nCalculating per vehicle technology costs...')
    calcs_avg = FleetAverages(averages_dict)

    age0_keys = [k for k, v in averages_dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost = calcs_avg.get_attribute_value(key, 'DirectCost_AvgPerVeh')
        cost += calcs_avg.get_attribute_value(key, 'IndirectCost_AvgPerVeh')

        temp_dict = {'TechCost_AvgPerVeh': cost}
        calcs_avg.update_dict(key, temp_dict)

    return averages_dict


def calc_tech_costs(totals_dict, averages_dict, sales_arg):
    """

    Parameters::
        totals_dict: Dictionary; contains vehicle population (VPOP) data.\n
        averages_dict: Dictionary; contains average tech costs per vehicle.
        sales_arg: String; specifies the sales attribute to use (e.g., "VPOP" or "VPOP_withTech")

    Returns:
        The totals_dict dictionary updated with annual technology costs for all vehicles.

    """
    print('\nCalculating total technology costs...')

    calcs_avg = FleetAverages(averages_dict)
    calcs = FleetTotals(totals_dict)

    age0_keys = [k for k, v in totals_dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost_per_veh = calcs_avg.get_attribute_value(key, 'TechCost_AvgPerVeh')
        sales = calcs.get_attribute_value(key, sales_arg)
        cost = cost_per_veh * sales

        temp_dict = {'TechCost': cost}
        calcs.update_dict(key, temp_dict)

    return totals_dict
