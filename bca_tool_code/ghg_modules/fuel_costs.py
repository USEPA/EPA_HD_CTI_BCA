import pandas as pd


def calc_fuel_costs(settings, data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        Updates the fleet dictionary to reflect fuel costs.

    """
    print('\nCalculating GHG fuel costs...')

    for key in data_object._dict.keys():
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        calendar_year = model_year + age_id

        prices = ['retail_fuel_price', 'pretax_fuel_price']
        price_retail, price_pretax = settings.fuel_prices.get_price(calendar_year, ft, *prices)

        gallons_paid_for = data_object.get_attribute_value(key, 'Gallons')

        cost_retail = price_retail * gallons_paid_for
        cost_pretax = price_pretax * gallons_paid_for

        update_dict = {'FuelCost_Retail': cost_retail,
                       'FuelCost_Pretax': cost_pretax,
                       }
        data_object.update_dict(key, update_dict)


def calc_fuel_costs_per_veh(data_object):
    """

    Parameters:
        data_object: Object; the fleet data object.

    Returns:
        Updates the fleet dictionary to include fuel costs/vehicle and costs/mile.

    """
    print('\nCalculating average fuel costs...')

    for key in data_object._dict.keys():
        fuel_cost = data_object.get_attribute_value(key, 'FuelCost_Retail')
        vmt = data_object.get_attribute_value(key, 'VMT')
        vpop = data_object.get_attribute_value(key, 'VPOP')

        # try/except block to protect against divide by 0 error
        try:
            cost_per_mile = fuel_cost / vmt
            cost_per_veh = fuel_cost / vpop
        except ZeroDivisionError:
            cost_per_mile = 0
            cost_per_veh = 0

        update_dict = {'FuelCost_Retail_PerMile': cost_per_mile,
                       'FuelCost_Retail_PerVeh': cost_per_veh,
                       }
        data_object.update_dict(key, update_dict)
