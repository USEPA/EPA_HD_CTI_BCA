import pandas as pd


def calc_avg_regclass_cost_per_step(settings):
    """

    Parameters:
        settings: The SetInputs class.

    Returns:
        Updates to the regclass sales dictionary to include the package costs at each cost step.

    """
    learning_rate = pd.to_numeric(settings.general_inputs.get_attribute('learning_rate'))

    age0_keys = [k for k, v in settings.fleet_cap._data.items() if v['ageID'] == 0]

    for key in age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = rc, ft
        rc_sales_key = engine, alt, model_year

        cost_steps = settings.regclass_costs.cost_steps

        for cost_step in cost_steps:
            cost_step = pd.to_numeric(cost_step)
            cumulative_sales = settings.regclass_sales.get_attribute_value(rc_sales_key, f'VPOP_withTech_Cumulative_{cost_step}')
            sales_year1 = settings.regclass_sales.get_attribute_value((engine, alt, cost_step), f'VPOP_withTech_Cumulative_{cost_step}')

            if sales_year1 == 0:
                pass # this is for modelYearID < cost_step to protect against zero division error below

            else:
                if model_year >= int(cost_step):
                    pkg_cost = settings.regclass_costs.get_cost((engine, alt), cost_step)
                    seedvolume_factor = settings.regclass_learning_scalers.get_seedvolume_factor(engine, alt)
                    pkg_cost_learned = pkg_cost \
                                       * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate)

                    update_dict = {f'Cost_PerVeh_{cost_step}': pkg_cost_learned}
                    settings.regclass_sales.update_dict(rc_sales_key, update_dict)


def calc_direct_costs_per_veh(settings):
    """

    Parameters:
        settings: The SetInputs class.

    Returns:
        The averages_dict dictionary updated with tech package costs/vehicle.

    """
    print(f'\nCalculating direct costs per vehicle...')

    age0_keys = [k for k, v in settings.fleet_cap._data.items() if v['ageID'] == 0]

    for key in age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = rc, ft
        rc_sales_key = engine, alt, model_year

        cost_steps = settings.regclass_costs.cost_steps

        if alt == 0:
            cost_step = cost_steps[0]
            cost = settings.regclass_sales.get_attribute_value(rc_sales_key, f'Cost_PerVeh_{cost_step}')
        else:
            cost = settings.regclass_sales.get_attribute_value((engine, 0, model_year), f'Cost_PerVeh_{cost_steps[0]}')
            for cost_step in cost_steps:
                if model_year >= int(cost_step):
                    cost += settings.regclass_sales.get_attribute_value(rc_sales_key, f'Cost_PerVeh_{cost_step}')

        # if program == 'GHG':
        #     # GHG program costs are to be averaged over all VPOP for the given unit
        #     vpop_with_tech = calcs_avg.get_attribute_value(key, 'VPOP_withTech')
        #     vpop = calcs_avg.get_attribute_value(key, 'VPOP')
        #     cost = cost * vpop_with_tech / vpop
        #     temp_dict = {'TechCost_AvgPerVeh': cost}
        #     calcs_avg.update_dict(key, temp_dict)
        # else:
        update_dict = {'DirectCost_PerVeh': cost}
        settings.fleet_cap.update_dict(key, update_dict)


def calc_direct_costs(settings):
    """

    Parameters:
        settings: The SetInputs class.

    Returns:
        The totals_dict dictionary updated with tech package direct costs (package cost * sales).

    """
    print(f'\nCalculating direct costs...')

    age0_keys = [k for k, v in settings.fleet_cap._data.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost_per_veh = settings.fleet_cap.get_attribute_value(key, 'DirectCost_PerVeh')
        sales = settings.fleet_cap.get_attribute_value(key, 'VPOP')
        cost = cost_per_veh * sales

        update_dict = {'DirectCost': cost}
        settings.fleet_cap.update_dict(key, update_dict)


if __name__ == '__main__':
    import pandas as pd
    from pathlib import Path
    from bca_tool_code.tool_setup import SetInputs
    from bca_tool_code.project_fleet import create_fleet_df

    settings = SetInputs()

    path_project = Path(__file__).parent.parent
    path_dev = path_project / 'dev'
    path_dev.mkdir(exist_ok=True)

    # create project fleet DataFrame which will include adjustments to the MOVES input file that are unique to the project.
    cap_fleet_df = create_fleet_df(settings, settings.moves_cap, settings.options_cap_dict,
                                   settings.moves_adjustments_cap_dict, 'VPOP', 'VMT', 'Gallons')

    # create totals, averages and sales by regclass dictionaries
    cap_totals_dict, cap_averages_dict, regclass_sales_dict = dict(), dict(), dict()
    cap_totals_dict = FleetTotals(cap_totals_dict).create_fleet_totals_dict(settings, cap_fleet_df)
    cap_averages_dict = FleetAverages(cap_averages_dict).create_fleet_averages_dict(settings, cap_fleet_df)
    regclass_sales_dict = FleetTotals(regclass_sales_dict).create_regclass_sales_dict(cap_fleet_df)

    # calculate direct costs per reg class based on cumulative regclass sales (learning is applied to cumulative sales)
    regclass_yoy_costs_per_step = calc_yoy_costs_per_step(settings, regclass_sales_dict, 'VPOP_withTech', 'CAP')
    df = pd.DataFrame(regclass_yoy_costs_per_step).transpose()

    df.to_csv(path_dev / 'regclass_yoy_costs_per_step.csv', index=True)
    print(f'\nOutput files have been saved to {path_dev}\n')
