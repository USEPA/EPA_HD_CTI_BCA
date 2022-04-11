import pandas as pd


def calc_avg_package_cost_per_step(settings, costs_object, scalers_object, sales_object):
    """

    Parameters:
        settings: The SetInputs class. \n
        costs_object: Object; the cost data object. \n
        scalers_object: Object; the learning scalers object.\n
        sales_object: Object; the sales data object.

    Returns:
        Updates to the sales object dictionary to include the year-over-year package costs, including learning
        effects, at each cost step.

    """
    learning_rate = pd.to_numeric(settings.general_inputs.get_attribute_value('learning_rate'))

    age0_keys = [k for k, v in sales_object._dict.items() if v['ageID'] == 0]

    cost_steps = costs_object.cost_steps

    for key in age0_keys:
        unit, alt, model_year = key
        for cost_step in cost_steps:
            cost_step = pd.to_numeric(cost_step)
            cumulative_sales = sales_object.get_attribute_value(key, f'VPOP_withTech_Cumulative_{cost_step}')
            sales_year1 = sales_object.get_attribute_value((unit, alt, cost_step), f'VPOP_withTech_Cumulative_{cost_step}')

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


def calc_package_costs_per_veh(settings, data_object, sales_object, attribute_name):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.\n
        sales_object: Object; the sales data object.\n
        attribute_name: String; the name of the package cost attribute, e.g., 'Direct' or 'Tech.'

    Returns:
        Updates to the fleet data object to include the package cost per vehicle (average cost/veh).

    """
    print(f'\nCalculating {attribute_name} costs per vehicle...')

    age0_keys = [k for k, v in data_object._dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        vehicle, alt, model_year, age_id, disc_rate = key

        cost_steps = settings.sourcetype_costs.cost_steps

        if alt == 0:
            cost_step = cost_steps[0]
            cost = sales_object.get_attribute_value((vehicle, alt, model_year), f'Cost_PerVeh_{cost_step}')
        else:
            cost = sales_object.get_attribute_value((vehicle, 0, model_year), f'Cost_PerVeh_{cost_steps[0]}')
            for cost_step in cost_steps:
                if model_year >= int(cost_step):
                    cost += sales_object.get_attribute_value((vehicle, alt, model_year), f'Cost_PerVeh_{cost_step}')

        # GHG program costs are to be averaged over all VPOP for the given unit
        vpop_with_tech = data_object.get_attribute_value(key, 'VPOP_withTech')
        vpop = data_object.get_attribute_value(key, 'VPOP')
        cost = cost * vpop_with_tech / vpop

        update_dict = {f'{attribute_name}Cost_PerVeh': cost}
        data_object.update_dict(key, update_dict)


def calc_package_costs(data_object, attribute_name, sales_arg):
    """

    Parameters:
        data_object: Object; the fleet data object.\n
        attribute_name: String; the name of the package cost attribute, e.g., 'Direct' or 'Tech.'\n
        sales_arg: String; the sales to use when calculating sales * cost/veh.

    Returns:
        Updates to the fleet data object to include the package costs (package cost/veh * sales).

    """
    print(f'\nCalculating {attribute_name} costs...')

    age0_keys = [k for k, v in data_object._dict.items() if v['ageID'] == 0]

    for key in age0_keys:
        cost_per_veh = data_object.get_attribute_value(key, f'{attribute_name}Cost_PerVeh')
        sales = data_object.get_attribute_value(key, sales_arg)
        cost = cost_per_veh * sales

        update_dict = {f'{attribute_name}Cost': cost}
        data_object.update_dict(key, update_dict)