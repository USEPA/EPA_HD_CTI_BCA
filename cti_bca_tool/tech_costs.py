
per_veh_tech_cost_dict = dict()


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
        vehicle, model_year, age_id, disc_rate = key
        if age_id == 0:
            dc_per_veh = averages_dict[key]['DirectCost_AvgPerVeh']
            ic_per_veh = averages_dict[key]['IndirectCost_AvgPerVeh']
            averages_dict[key].update({'TechCost_AvgPerVeh': dc_per_veh + ic_per_veh})
    return averages_dict


def calc_tech_costs(totals_dict, averages_dict):
    """

    Parameters::
        totals_dict: A dictionary containing vehicle population (VPOP).\n
        averages_dict: A dictionary containing average tech costs per vehicle.

    Returns:
        The totals_dict dictionary updated with annual technology costs for all vehicles.

    """
    print('\nCalculating total technology costs.\n')
    for key in totals_dict.keys():
        vehicle, model_year, age_id, disc_rate = key
        if age_id == 0:
            cost_per_veh = averages_dict[key]['TechCost_AvgPerVeh']
            sales = totals_dict[key]['VPOP']
            totals_dict[key].update({'TechCost': cost_per_veh * sales})
    return totals_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.general_functions import save_dict_to_csv
    from cti_bca_tool.project_fleet import create_fleet_df, regclass_vehicles
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_totals_dict, create_averages_dict
    from cti_bca_tool.direct_costs import calc_per_regclass_direct_costs, calc_direct_costs, calc_per_veh_direct_costs
    from cti_bca_tool.indirect_costs import calc_per_veh_indirect_costs, calc_indirect_costs

    project_fleet_df = create_fleet_df(settings)
    vehicles_rc = regclass_vehicles(project_fleet_df)

    project_regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)
    totals_dict = create_totals_dict(project_fleet_df)
    averages_dict = create_averages_dict(project_fleet_df)

    per_veh_dc_by_year_dict = calc_per_regclass_direct_costs(settings, vehicles_rc, project_regclass_sales_dict)[1]

    totals_dict = calc_direct_costs(per_veh_dc_by_year_dict, totals_dict)
    averages_dict = calc_per_veh_direct_costs(totals_dict, averages_dict)

    averages_dict = calc_per_veh_indirect_costs(settings, averages_dict)
    averages_dict = calc_per_veh_tech_costs(averages_dict)

    totals_dict = calc_indirect_costs(settings, totals_dict, averages_dict)
    totals_dict = calc_tech_costs(totals_dict, averages_dict)

    # save dicts to csv
    save_dict_to_csv(averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
