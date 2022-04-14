import pandas as pd


def calc_thc_reduction(settings, data_object, key):
    """

    Parameters:
        settings: The SetInputs class. \n
        data_object: Object; the fleet data object.
        key: Tuple; represents the vehicle, alt, model year, age and discount rate.

    Returns:
        The THC reduction for the passed model year vehicle in the given calendar year.

    Notes:
        The thc_reduction calculation should be done such that it is positive if action has lower thc than no action.

    """
    vehicle, alt, model_year, age_id, disc_rate = key
    no_action_key = vehicle, settings.no_action_alt, model_year, age_id, disc_rate
    thc_no_action = data_object.get_attribute_value(no_action_key, 'THC_UStons')
    thc_action = data_object.get_attribute_value(key, 'THC_UStons')
    thc_reduction = thc_no_action - thc_action

    return thc_reduction


def calc_fuel_costs(settings, data_object):
    """

    Parameters:
        settings: The SetInputs class.\n
        data_object: Object; the fleet data object.

    Returns:
        Updates the fleet dictionary to reflect fuel consumption (Gallons) adjusted to account for the fuel saved in
        association with ORVR. The dictionary is also updated to include the fuel costs associated with the gallons
        consumed (Gallons paid for * $/gallon fuel).

    Note:
        Note that gallons of fuel captured are not included in the MOVES runs that serve as the input fleet data for the
        tool although the inventory impacts are included in the MOVES runs.

    """
    print('\nCalculating CAP fuel costs...')

    gallons_per_ml = pd.to_numeric(settings.general_inputs.get_attribute_value('gallons_per_ml'))
    grams_per_short_ton = pd.to_numeric(settings.general_inputs.get_attribute_value('grams_per_short_ton'))

    for key in data_object.keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        engine = rc, ft
        calendar_year = model_year + age_id

        captured_gallons = 0
        prices = ['retail_fuel_price', 'pretax_fuel_price']
        price_retail, price_pretax = settings.fuel_prices.get_price(calendar_year, ft, *prices)

        # calculate gallons that would have evaporated without new ORVR
        if ft == 1:
            orvr_adjustment = settings.orvr_fuelchanges_cap.get_ml_per_gram(engine, alt)
            thc_reduction = calc_thc_reduction(settings, data_object, key)
            captured_gallons = thc_reduction * orvr_adjustment * grams_per_short_ton * gallons_per_ml

        gallons = data_object.get_attribute_value(key, 'Gallons')
        gallons_paid_for = gallons - captured_gallons

        cost_retail = price_retail * gallons_paid_for
        cost_pretax = price_pretax * gallons_paid_for

        update_dict = {'GallonsCaptured_byORVR': captured_gallons,
                       'FuelCost_Retail': cost_retail,
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

    for key in data_object.keys:
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
