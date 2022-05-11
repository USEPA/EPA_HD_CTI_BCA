import pandas as pd


def calc_avg_package_cost_per_step(settings):
    """

    Parameters:
        settings: object; the SetInputs class object.

    Returns:
        Updates the sales object dictionary to include the year-over-year package costs, including learning
        effects, associated with each cost step.

    """
    learning_rate = pd.to_numeric(settings.general_inputs.get_attribute_value('learning_rate'))
    costs_object = settings.engine_costs
    scalers_object = settings.engine_learning_scalers
    sales_object = settings.regclass_sales

    cost_steps = costs_object.start_years

    for key in sales_object.age0_keys:
        unit, alt, model_year = key
        for cost_step in cost_steps:
            cost_step = pd.to_numeric(cost_step)
            cumulative_sales = sales_object.get_attribute_value(key, f'VPOP_Cumulative_{cost_step}')
            sales_year1 = sales_object.get_attribute_value((unit, alt, cost_step), f'VPOP_Cumulative_{cost_step}')

            if sales_year1 == 0:
                pass # this is for modelYearID < cost_step to protect against zero division error below

            else:
                if model_year >= int(cost_step):
                    pkg_cost = costs_object.get_cost((unit, alt), cost_step)
                    seedvolume_factor = scalers_object.get_seedvolume_factor(unit, alt)

                    pkg_cost_learned = pkg_cost \
                                       * (((cumulative_sales + (sales_year1 * seedvolume_factor))
                                           / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate)

                    update_dict = {f'Cost_PerVeh_{cost_step}': pkg_cost_learned}
                    sales_object.update_dict(key, update_dict)


def calc_package_costs_per_veh(settings, data_object):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        data_object: object; the fleet data object.

    Returns:
        Updates the data_object dictionary to include the package cost per vehicle (average cost/veh) including the
        summation of costs associated with each cost step, if applicable.

    """
    print(f'\nCalculating CAP Direct costs per vehicle...')
    sales_object = settings.regclass_sales

    for key in data_object.age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = rc, ft

        cost_steps = settings.engine_costs.start_years

        if alt == 0:
            cost_step = cost_steps[0]
            cost = sales_object.get_attribute_value((engine, alt, model_year), f'Cost_PerVeh_{cost_step}')
        else:
            cost = sales_object.get_attribute_value((engine, 0, model_year), f'Cost_PerVeh_{cost_steps[0]}')
            for cost_step in cost_steps:
                if model_year >= int(cost_step):
                    cost += sales_object.get_attribute_value((engine, alt, model_year), f'Cost_PerVeh_{cost_step}')

        update_dict = {'DirectCost_PerVeh': cost}
        data_object.update_dict(key, update_dict)


def calc_package_costs(data_object):
    """

    Parameters:
        data_object: object; the fleet data object.

    Returns:
        Updates the data_object dictionary to include the package costs (package cost/veh * sales).

    """
    print(f'\nCalculating CAP Direct costs...')

    # Note: use age=0 keys only since only new vehicles incur package costs.
    for key in data_object.age0_keys:
        cost_per_veh = data_object.get_attribute_value(key, 'DirectCost_PerVeh')
        sales = data_object.get_attribute_value(key, 'VPOP')
        cost = cost_per_veh * sales

        update_dict = {'DirectCost': cost}
        data_object.update_dict(key, update_dict)
