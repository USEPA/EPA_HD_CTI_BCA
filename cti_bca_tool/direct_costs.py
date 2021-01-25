

# create some dictionaries for storing data
cumulative_sales_dict = dict()
pkg_cost_dict = dict()
costs_by_year_by_step_dict = dict()
costs_by_year_dict = dict()
regclass_yoy_costs_per_step_dict = dict()


def tech_package_cost(costs_df, vehicle, cost_step):
    """

    Args:
        costs_df: A DataFrame of individual tech costs by regclass and fueltype based on the DirectCosts by regclass input file..
        vehicle: A tuple representing an alt_regclass_fueltype vehicle.
        cost_step: If standards are implemented in stages (i.e., for MY2027 and then again for MY2030), then these would represent two cost steps. The cost_step
        here is a string representing a model year of implementation (i.e., '2027', not 2027).

    Returns: A single float representing the package direct cost (a summation of individual tech direct costs) for the passed vehicle at the given cost_step.

    """
    pkg_cost_dict_key = ((vehicle), cost_step)
    if pkg_cost_dict_key in pkg_cost_dict.keys():
        pkg_cost = pkg_cost_dict[pkg_cost_dict_key]
    else:
        alt, rc, ft = vehicle
        techs_on_veh = costs_df.loc[(costs_df['optionID'] == alt)
                                    & (costs_df['regClassID'] == rc)
                                    & (costs_df['fuelTypeID'] == ft),
                                    ['TechPackageDescription', cost_step]]
        pkg_cost = techs_on_veh[cost_step].sum(axis=0)
        pkg_cost_dict[pkg_cost_dict_key] = pkg_cost
    return pkg_cost


def calc_cumulative_sales_by_step(vehicle, model_year, cost_step, regclass_sales_dict):
    """

    Args:
        vehicle: A tuple representing an alt_regclass_fueltype vehicle.
        model_year: The model year of the passed vehicle.
        cost_step: If standards are implemented in stages (i.e., for MY2027 and then again for MY2030), then these would represent two cost steps. The cost_step
        here is a string representing a model year of implementation (i.e., '2027', not 2027).
        regclass_sales_dict: A dictionary containing sales (VPOP at age=0) of alt_regclass_fueltype vehicles by model year.

    Returns: A single float of cumulative sales for the given alt_regclass_fueltype vehicle meeting the standards set in the given cost_step. In other words,
    new standards for MY2027 would have cumulative sales beginning in MY2027 and continuing each model year thereafter. New standards set in MY2030 would have
    cumulative sales beginning in MY2030 and continuing each model year thereafter. These sales "streams" are never combined.

    """
    cumulative_sales_dict_id = ((vehicle), model_year, cost_step)
    if cumulative_sales_dict_id in cumulative_sales_dict.keys():
        cumulative_sales = cumulative_sales_dict[cumulative_sales_dict_id]
    else:
        cumulative_sales = 0
        for year in range(int(cost_step), model_year + 1):
            cumulative_sales += regclass_sales_dict[((vehicle), year)]['VPOP']
        cumulative_sales_dict[cumulative_sales_dict_id] = cumulative_sales
    return cumulative_sales


def tech_pkg_cost_withlearning(settings, vehicle, model_year, cost_step, regclass_sales_dict):
    """

    Args:
        settings: The SetInputs class.
        vehicle: A tuple representing an alt_regclass_fueltype vehicle.
        model_year: The model year of the passed vehicle.
        cost_step: If standards are implemented in stages (i.e., for MY2027 and then again for MY2030), then these would represent two cost steps. The cost_step
        here is a string representing a model year of implementation (i.e., '2027', not 2027).
        regclass_sales_dict: A dictionary containing sales (VPOP at age=0) of alt_regclass_fueltype vehicles by model year.

    Returns: Two values - the package cost with learning applied for the passsed vehicle in the given model year and associated with the given cost_step;
    and, the cumulative sales of that vehicle used in calculating learning effects.

    """
    sales_year1 = regclass_sales_dict[((vehicle), int(cost_step))]['VPOP']
    cumulative_sales = calc_cumulative_sales_by_step(vehicle, model_year, cost_step, regclass_sales_dict)
    seedvolume_factor = settings.seedvol_factor_dict[vehicle]['SeedVolumeFactor']
    pkg_cost = tech_package_cost(settings.regclass_costs, vehicle, cost_step)
    pkg_cost_learned = pkg_cost \
                       * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** settings.learning_rate)
    return pkg_cost_learned, cumulative_sales


def calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict):
    """

    Args:
        settings: The SetInputs class.
        regclass_sales_dict: A dictionary containing sales (VPOP at age=0) of alt_regclass_fueltype vehicles by model year.

    Returns: A dictionary containing the package cost and cumulative sales used to calculate that package cost (learning effects depend on cumulative
    sales) for the passed vehicle in the given model year and complying with the standards set in the given cost step.

    """
    for key in regclass_sales_dict.keys():
        vehicle, model_year = key[0], key[1]
        for cost_step in settings.cost_steps:
            if model_year >= int(cost_step):
                pkg_cost, cumulative_sales = tech_pkg_cost_withlearning(settings, vehicle, model_year, cost_step, regclass_sales_dict)
                regclass_yoy_costs_per_step_dict[((vehicle), model_year, cost_step)] = {'CumulativeSales': cumulative_sales, 'DirectCost_AvgPerVeh': pkg_cost}
    return regclass_yoy_costs_per_step_dict


def calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step_dict, averages_dict):
    """

    Args:
        settings: The SetInputs class.
        regclass_yoy_costs_per_step_dict: A dictionary containing the package cost and cumulative sales used to calculate that package cost (learning effects depend on cumulative
        sales) for the passed vehicle in the given model year and complying with the standards set in the given cost step.
        averages_dict: A dictionary into which tech package direct costs/vehicle will be updated.

    Returns: The passed dictionary updated with tech package direct costs/vehicle.

    """
    for key in averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if age_id == 0:
            print(f'Calculating per vehicle direct costs for {vehicle}, MY {model_year}.')
            if alt == 0:
                model_year_cost = regclass_yoy_costs_per_step_dict[((alt, rc, ft), model_year, settings.cost_steps[0])]['DirectCost_AvgPerVeh']
            else:
                model_year_cost = regclass_yoy_costs_per_step_dict[((0, rc, ft), model_year, settings.cost_steps[0])]['DirectCost_AvgPerVeh']
                for cost_step in settings.cost_steps:
                    if model_year >= int(cost_step):
                        model_year_cost += regclass_yoy_costs_per_step_dict[((alt, rc, ft), model_year, cost_step)]['DirectCost_AvgPerVeh']
            averages_dict[key].update({'DirectCost_AvgPerVeh': model_year_cost})
    return averages_dict


def calc_direct_costs(totals_dict, averages_dict):
    """

    Args:
        totals_dict: A dictionary into which tech package direct costs will be updated.
        averages_dict: A dictionary containing tech package direct costs/vehicle.

    Returns: The passed dictionary updated with tech package direct costs (package cost * sales).

    """
    print('\nCalculating total direct costs.\n')
    for key in totals_dict.keys():
        age_id = key[2]
        if age_id == 0:
            cost_per_veh = averages_dict[key]['DirectCost_AvgPerVeh']
            sales = totals_dict[key]['VPOP']
            totals_dict[key].update({'DirectCost': cost_per_veh * sales})
    return totals_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df
    from cti_bca_tool.project_dicts import create_regclass_sales_dict, create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)
    regclass_sales_dict = create_regclass_sales_dict(project_fleet_df)

    regclass_yoy_costs_per_step_dict = calc_regclass_yoy_costs_per_step(settings, regclass_sales_dict)
    fleet_averages_dict = calc_per_veh_direct_costs(settings, regclass_yoy_costs_per_step_dict, fleet_averages_dict)
    fleet_totals_dict = calc_direct_costs(fleet_totals_dict, fleet_averages_dict)

    # save dicts to csv
    save_dict_to_csv(regclass_yoy_costs_per_step_dict, settings.path_project / 'test/regclass_direct_costs_by_year_by_step', 'vehicle', 'modelYearID', 'cost_step')
    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
