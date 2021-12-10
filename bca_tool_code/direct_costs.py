from bca_tool_code.fleet_dicts_cap import FleetTotalsDict, FleetAveragesDict
from bca_tool_code.regclass_sales_dict import RegclassSalesDict


def tech_package_cost(costs_df, unit, alt, cost_step):
    """

    Parameters:
        costs_df: A DataFrame of individual tech costs by regclass and fueltype based on the DirectCosts by regclass input file.  \n
        unit: A tuple representing a regclass_fueltype engine or a sourcetype_regclass_fueltype vehicle.\n
        alt: The Alternative or optionID.\n
        cost_step: If standards are implemented in stages (i.e., for MY2027 and then again for MY2030), then these would represent two cost steps. The cost_step
        here is a string representing a model year of implementation (i.e., '2027', not 2027).

    Returns:
        A single float representing the package direct cost (a summation of individual tech direct costs) for the passed vehicle at the given cost_step.

    """
    try:
        rc, ft = unit
        techs_on_veh = costs_df.loc[(costs_df['optionID'] == alt)
                                    & (costs_df['regClassID'] == rc)
                                    & (costs_df['fuelTypeID'] == ft),
                                    ['TechPackageDescription', cost_step]]
    except:
        st, rc, ft = unit
        techs_on_veh = costs_df.loc[(costs_df['optionID'] == alt)
                                    & (costs_df['sourceTypeID'] == st)
                                    & (costs_df['regClassID'] == rc)
                                    & (costs_df['fuelTypeID'] == ft),
                                    ['TechPackageDescription', cost_step]]
    pkg_cost = techs_on_veh[cost_step].sum(axis=0)
    return pkg_cost


def calc_cumulative_sales_by_step(unit, alt, model_year, cost_step, sales_dict, sales_arg):
    """

    Parameters:
        unit: A tuple representing a regclass_fueltype engine or a sourcetype_regclass_fueltype vehicle.\n
        alt: The Alternative or option ID.\n
        model_year: The model year of the passed vehicle.\n
        cost_step: If standards are implemented in stages (i.e., for MY2027 and then again for MY2030), then these would represent two cost steps. The cost_step
        here is a string representing a model year of implementation (i.e., '2027', not 2027).\n
        sales_dict: A dictionary containing sales (VPOP at age=0) of units by model year.\n
        sales_arg: A String specifying the sales attribute to use (e.g., "VPOP" or "VPOP_AddingTech")

    Returns:
        A single float of cumulative sales for the given unit meeting the standards set in the given cost_step.

    Note:
        New standards for MY2027 would have cumulative sales beginning in MY2027 and continuing each model year thereafter. New standards set in MY2030 would have
        cumulative sales beginning in MY2030 and continuing each model year thereafter. These sales "streams" are never combined.

    """
    rc_sales = RegclassSalesDict(sales_dict)
    cumulative_sales = 0
    for year in range(int(cost_step), model_year + 1):
        cumulative_sales += rc_sales.get_attribute_value((unit, alt, year), sales_arg)
        # cumulative_sales += sales_dict[(unit, alt, year)][sales_arg]
    return cumulative_sales


def tech_pkg_cost_withlearning(settings, unit, alt, cumulative_sales, cost_step, sales_dict, sales_arg):
    """

    Parameters:
        settings: The SetInputs class.\n
        unit: A tuple representing a regclass_fueltype engine or a sourcetype_regclass_fueltype vehicle.\n
        alt: The alternative or option ID.\n
        cumulative_sales: The cumulative sales of the given unit since the start of the cost step.\n
        cost_step: If standards are implemented in stages (i.e., for MY2027 and then again for MY2030), then these would represent two cost steps. The cost_step
        here is a string representing a model year of implementation (i.e., '2027', not 2027).\n
        sales_dict: A dictionary containing sales (VPOP at age=0) of units by model year.\n
        sales_arg: A String specifying the sales attribute to use (e.g., "VPOP" or "VPOP_AddingTech")

    Returns:
        Two values - the package cost with learning applied for the passsed unit in the given model year and associated with the given cost_step;
        and, the cumulative sales of that vehicle used in calculating learning effects.

    """
    rc_sales = RegclassSalesDict(sales_dict)
    sales_year1 = rc_sales.get_attribute_value((unit, alt, int(cost_step)), sales_arg)
    # sales_year1 = sales_dict[(unit, alt, int(cost_step))][sales_arg]
    if sales_year1 == 0:
        pkg_cost_learned = 0
    else:
        try:
            rc, ft = unit
            seedvolume_factor = settings.seedvol_factor_regclass_dict[(unit, alt)]['SeedVolumeFactor']
            pkg_cost = tech_package_cost(settings.regclass_costs, unit, alt, cost_step)
        except:
            st, rc, ft = unit
            seedvolume_factor = settings.seedvol_factor_sourcetype_dict[(unit, alt)]['SeedVolumeFactor']
            pkg_cost = tech_package_cost(settings.sourcetype_costs, unit, alt, cost_step)
        pkg_cost_learned = pkg_cost \
                           * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                               / (sales_year1 + (sales_year1 * seedvolume_factor))) ** settings.learning_rate)
    return pkg_cost_learned


def calc_yoy_costs_per_step(settings, sales_dict, sales_arg):
    """

    Parameters:
        settings: The SetInputs class.\n
        sales_dict: A dictionary containing sales (VPOP at age=0) of units by model year.\n
        sales_arg: A String specifying the sales attribute to use (e.g., "VPOP" or "VPOP_AddingTech")

    Returns:
        A dictionary containing the package cost and cumulative sales used to calculate that package cost (learning effects depend on cumulative
        sales) for the passed unit in the given model year and complying with the standards set in the given cost step.

    """
    yoy_costs_per_step_dict = dict()
    for key in sales_dict.keys():
        unit, alt, model_year = key
        try:
            rc, ft = unit
            steps = settings.cost_steps_regclass
        except:
            st, rc, ft = unit
            steps = settings.cost_steps_sourcetype
        for cost_step in steps:
            if model_year >= int(cost_step):
                cumulative_sales = calc_cumulative_sales_by_step(unit, alt, model_year, cost_step, sales_dict, sales_arg)
                pkg_cost = tech_pkg_cost_withlearning(settings, unit, alt, cumulative_sales, cost_step, sales_dict, sales_arg)
                yoy_costs_per_step_dict[(unit, alt, model_year, cost_step)] = {'CumulativeSales': cumulative_sales, 'Cost_AvgPerVeh': pkg_cost}
    return yoy_costs_per_step_dict


def calc_per_veh_direct_costs(yoy_costs_per_step_dict, cost_steps, averages_dict, program):
    """

    Parameters:
        yoy_costs_per_step_dict: A dictionary containing the package cost and cumulative sales used to calculate that package cost (learning effects depend on cumulative
        sales) for the passed unit in the given model year and complying with the standards set in the given cost step.
        cost_steps: A list of cost steps associated with the direct costs being calculated.
        averages_dict: A dictionary into which tech package direct costs/vehicle will be updated.
        program: The program identifier string (i.e., 'CAP' or 'GHG').

    Returns:
        The averages_dict dictionary updated with tech package costs/vehicle.

    """
    print(f'\nCalculating {program} costs per vehicle...')
    calcs_avg = FleetAveragesDict(averages_dict)
    # calcs_dict = averages_dict.copy()
    # for key in calcs_dict.keys():
    for key in averages_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = (rc, ft)
        if program == 'CAP': unit = engine
        else: unit = vehicle
        if age_id == 0:
            # print(f'Calculating per unit direct costs for {vehicle}, MY {model_year}.')
            if alt == 0:
                model_year_cost = yoy_costs_per_step_dict[(unit, alt, model_year, cost_steps[0])]['Cost_AvgPerVeh']
            else:
                model_year_cost = yoy_costs_per_step_dict[(unit, 0, model_year, cost_steps[0])]['Cost_AvgPerVeh']
                for step in cost_steps:
                    if model_year >= int(step):
                        model_year_cost += yoy_costs_per_step_dict[(unit, alt, model_year, step)]['Cost_AvgPerVeh']
            if program == 'GHG':
                # GHG program costs are to be averaged over all VPOP for the given unit
                vpop_adding_tech = calcs_avg.get_attribute_value(key, 'VPOP_AddingTech')
                vpop = calcs_avg.get_attribute_value(key, 'VPOP')
                model_year_cost = model_year_cost * vpop_adding_tech / vpop
                # model_year_cost = model_year_cost * averages_dict[key]['VPOP_AddingTech'] / averages_dict[key]['VPOP']
                calcs_avg.update_dict(key, 'TechCost_AvgPerVeh', model_year_cost)
            else: calcs_avg.update_dict(key, 'DirectCost_AvgPerVeh', model_year_cost)
                # model_year_cost = model_year_cost * calcs_dict[key]['VPOP_AddingTech'] / calcs_dict[key]['VPOP']
                # calcs_dict[key].update({'TechCost_AvgPerVeh': model_year_cost})
            # else: calcs_dict[key].update({'DirectCost_AvgPerVeh': model_year_cost})
    return averages_dict


def calc_direct_costs(totals_dict, averages_dict, program, sales_arg):
    """

    Parameters:
        totals_dict: A dictionary into which tech package direct costs will be updated.\n
        averages_dict: A dictionary containing tech package direct costs/vehicle.\n
        program: The program identifier string (i.e., 'CAP' or 'GHG').\n
        sales_arg: A String specifying the sales attribute to use (e.g., "VPOP" or "VPOP_AddingTech")

    Returns:
        The totals_dict dictionary updated with tech package direct costs (package cost * sales).

    """
    if program == 'CAP': arg = 'Direct'
    else: arg = 'Tech'
    print(f'\nCalculating {program} {arg} total costs...')
    calcs_avg = FleetAveragesDict(averages_dict)
    calcs = FleetTotalsDict(totals_dict)
    for key in totals_dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        if age_id == 0:
            cost_per_veh = calcs_avg.get_attribute_value(key, f'{arg}Cost_AvgPerVeh')
            sales = calcs.get_attribute_value(key, sales_arg)
            cost = cost_per_veh * sales
            # cost_per_veh = averages_dict[key][f'{arg}Cost_AvgPerVeh']
            # sales = totals_dict[key][sales_arg]
            calcs.update_dict(key, f'{arg}Cost', cost)
            # totals_dict[key].update({f'{arg}Cost': cost_per_veh * sales})
    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
