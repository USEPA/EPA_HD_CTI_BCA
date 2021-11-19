

def calc_per_veh_tech_costs(averages_dict):
    """
    
    Parameters::
        averages_dict: A dictionary containing average direct and indirect costs per vehicle.

    Returns:
        The averages_dict dictionary updated with average tech costs per vehicle (direct plus indirect).

    Note:
        Direct and indirect costs apply only for ageID=0 (i.e., new sales).

    """
    print('\nCalculating per vehicle technology costs.\n')
    for key in averages_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        if age_id == 0:
            dc_per_veh = averages_dict[key]['DirectCost_AvgPerVeh']
            ic_per_veh = averages_dict[key]['IndirectCost_AvgPerVeh']
            averages_dict[key].update({'TechCost_AvgPerVeh': dc_per_veh + ic_per_veh})
    return averages_dict


def calc_tech_costs(totals_dict, averages_dict, sales_arg):
    """

    Parameters::
        totals_dict: A dictionary containing vehicle population (VPOP).\n
        averages_dict: A dictionary containing average tech costs per vehicle.
        sales_arg: A String specifying the sales attribute to use (e.g., "VPOP" or "VPOP_AddingTech")

    Returns:
        The totals_dict dictionary updated with annual technology costs for all vehicles.

    """
    print('\nCalculating total technology costs.\n')
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        if age_id == 0:
            cost_per_veh = averages_dict[key]['TechCost_AvgPerVeh']
            sales = totals_dict[key][sales_arg]
            totals_dict[key].update({'TechCost': cost_per_veh * sales})
    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
