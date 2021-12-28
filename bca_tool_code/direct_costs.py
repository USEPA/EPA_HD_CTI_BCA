from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages
from bca_tool_code.project_dicts import InputFileDict


def tech_package_cost(settings, unit, alt, cost_step):
    """

    Parameters:
        settings: The SetInputs class. \n
        unit: Tuple; represents a regclass_fueltype engine or a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; represents the Alternative or optionID.\n
        cost_step: String; represents the model year of implementation of the tech; if standards are implemented in stages (i.e., for MY2027
        and then again for MY2031), then these would represent two cost steps, one in '2027' and the other in '2031'.

    Returns:
        A single value representing the package direct cost (a summation of individual tech direct costs) for the passed vehicle at the given cost_step.

    """
    try:
        rc, ft = unit
        cost_inputs = settings.regclass_costs
        techs_on_veh = cost_inputs.loc[(cost_inputs['optionID'] == alt)
                                       & (cost_inputs['regClassID'] == rc)
                                       & (cost_inputs['fuelTypeID'] == ft),
                                       ['TechPackageDescription', cost_step]]
    except:
        st, rc, ft = unit
        cost_inputs = settings.sourcetype_costs
        techs_on_veh = cost_inputs.loc[(cost_inputs['optionID'] == alt)
                                       & (cost_inputs['sourceTypeID'] == st)
                                       & (cost_inputs['regClassID'] == rc)
                                       & (cost_inputs['fuelTypeID'] == ft),
                                       ['TechPackageDescription', cost_step]]

    pkg_cost = techs_on_veh[cost_step].sum(axis=0)

    return pkg_cost


def tech_pkg_cost_withlearning(settings, unit, alt, cost_step, sales_arg, cumulative_sales, totals_dict):
    """

    Parameters:
        settings: The SetInputs class.\n
        unit: Tuple; represents a regclass_fueltype engine or a sourcetype_regclass_fueltype vehicle.\n
        alt: The alternative or option ID.\n
        cost_step: String; represents the model year of implementation in case standards are implemented in stages then these would represent multiple cost steps.\n
        sales_arg: String; specifies the sales attribute to use (e.g., "VPOP" or "VPOP_withTech") \n
        cumulative_sales: Numeric; represents cumulative sales of unit since cost_step. \n
        totals_dict: A dictionary containing sales (sales_arg) of units by model year.\n

    Returns:
        The package cost with learning applied for the passed unit in the given model year and associated with the given cost_step.

    """
    sales_year1 = FleetTotals(totals_dict).calc_unit_sales(unit, alt, int(cost_step), sales_arg)

    if sales_year1 == 0:
        pkg_cost_learned = 0
    else:
        try:
            rc, ft = unit
            seedvolume_factors = InputFileDict(settings.seedvol_factor_regclass_dict)
        except:
            st, rc, ft = unit
            seedvolume_factors = InputFileDict(settings.seedvol_factor_sourcetype_dict)

        seedvolume_factor = seedvolume_factors.get_attribute_value((unit, alt), 'SeedVolumeFactor')
        pkg_cost = tech_package_cost(settings, unit, alt, cost_step)

        pkg_cost_learned = pkg_cost \
                           * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                               / (sales_year1 + (sales_year1 * seedvolume_factor))) ** settings.learning_rate)
    return pkg_cost_learned


def calc_yoy_costs_per_step(settings, totals_dict, sales_arg, program):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: Dictionary; provides sales of units by model year; this will be faster if age_id > 0 is scrubbed out first.\n
        sales_arg: String; specifies the sales attribute to use (e.g., "VPOP" or "VPOP_withTech"). \n
        program: String; the program identifier (e.g., 'CAP' or 'GHG').

    Returns:
        A dictionary containing the package cost and cumulative sales used to calculate that package cost (learning effects depend on cumulative
        sales) for the passed unit in the given model year and complying with the standards set in the given cost step.

    """
    cumulative_sales_dict = dict()
    yoy_costs_per_step_dict = dict()

    for key in totals_dict.keys():
        unit, alt, model_year, age_id, discount_rate = key
        if age_id != 0:
            pass
        else:
            if program == 'CAP':
                steps = settings.cost_steps_regclass
            else:
                steps = settings.cost_steps_sourcetype
            for cost_step in steps:
                cumulative_sales = 0
                if (unit, alt, model_year, cost_step) in cumulative_sales_dict.keys():
                    cumulative_sales = cumulative_sales_dict[(unit, alt, model_year, cost_step)]
                else:
                    if model_year >= int(cost_step):
                        cumulative_sales = FleetTotals(totals_dict).calc_unit_cumulative_sales(unit, alt, int(cost_step), model_year, sales_arg)
                        pkg_cost = tech_pkg_cost_withlearning(settings, unit, alt, cost_step,
                                                              sales_arg, cumulative_sales, totals_dict)
                        yoy_costs_per_step_dict[(unit, alt, model_year, cost_step)] = {'CumulativeSales': cumulative_sales, 'Cost_AvgPerVeh': pkg_cost}
                    cumulative_sales_dict[(unit, alt, model_year, cost_step)] = cumulative_sales
    return yoy_costs_per_step_dict


def calc_per_veh_direct_costs(yoy_costs_per_step_dict, cost_steps, averages_dict, program):
    """

    Parameters:
        yoy_costs_per_step_dict: Dictionary; contains the package cost and cumulative sales used to calculate that package cost (learning effects depend on cumulative
        sales) for the passed unit in the given model year and complying with the standards set in the given cost step. \n
        cost_steps: List; provides the cost steps (as strings) associated with the direct costs being calculated.\n
        averages_dict: Dictionary; into which tech package direct costs/vehicle will be updated.\n
        program: String; the program identifier (i.e., 'CAP' or 'GHG').

    Returns:
        The averages_dict dictionary updated with tech package costs/vehicle.

    """
    print(f'\nCalculating {program} costs per vehicle...')

    calcs_avg = FleetAverages(averages_dict)

    age0_keys = [k for k, v in averages_dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = (rc, ft)

        if program == 'CAP': unit = engine
        else: unit = vehicle

        if alt == 0:
            cost = yoy_costs_per_step_dict[(unit, alt, model_year, cost_steps[0])]['Cost_AvgPerVeh']
        else:
            cost = yoy_costs_per_step_dict[(unit, 0, model_year, cost_steps[0])]['Cost_AvgPerVeh']
            for step in cost_steps:
                if model_year >= int(step):
                    cost += yoy_costs_per_step_dict[(unit, alt, model_year, step)]['Cost_AvgPerVeh']

        if program == 'GHG':
            # GHG program costs are to be averaged over all VPOP for the given unit
            vpop_with_tech = calcs_avg.get_attribute_value(key, 'VPOP_withTech')
            vpop = calcs_avg.get_attribute_value(key, 'VPOP')
            cost = cost * vpop_with_tech / vpop
            temp_dict = {'TechCost_AvgPerVeh': cost}
            calcs_avg.update_dict(key, temp_dict)
        else:
            temp_dict = {'DirectCost_AvgPerVeh': cost}
            calcs_avg.update_dict(key, temp_dict)

    return averages_dict


def calc_direct_costs(totals_dict, averages_dict, sales_arg, program):
    """

    Parameters:
        totals_dict: Dictionary; into which tech package direct costs will be updated.\n
        averages_dict: Dictionary; contains tech package direct costs/vehicle.\n
        sales_arg: String; specifies the sales attribute to use (e.g., "VPOP" or "VPOP_withTech")\n
        program: String; the program identifier (i.e., 'CAP' or 'GHG').

    Returns:
        The totals_dict dictionary updated with tech package direct costs (package cost * sales).

    """
    if program == 'CAP': arg = 'Direct'
    else: arg = 'Tech'

    print(f'\nCalculating {program} {arg} total costs...')

    calcs = FleetTotals(totals_dict)
    calcs_avg = FleetAverages(averages_dict)

    age0_keys = [k for k, v in totals_dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost_per_veh = calcs_avg.get_attribute_value(key, f'{arg}Cost_AvgPerVeh')
        sales = calcs.get_attribute_value(key, sales_arg)
        cost = cost_per_veh * sales

        temp_dict = {f'{arg}Cost': cost}
        calcs.update_dict(key, temp_dict)

    return totals_dict


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
