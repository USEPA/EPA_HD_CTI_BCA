import pandas as pd


def calc_def_doserate(settings, vehicle):
    """

    Parameters:
        settings: The SetInputs class \n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n

    Returns:
        The DEF dose rate for the passed vehicle (engine) based on the DEF dose rate input file.

    """
    st, rc, ft = vehicle
    engine = rc, ft
    nox_std = settings.def_doserates.get_attribute_value(engine, 'standard_NOx')
    nox_engine_out = settings.def_doserates.get_attribute_value(engine, 'engineout_NOx')
    slope, intercept = settings.def_doserates.get_curve_coefficients(engine)
    base_doserate = ((nox_std - nox_engine_out) - intercept) / slope

    return base_doserate


def calc_nox_reduction(settings, key):
    """

    Parameters:
        settings: The SetInputs class. \n
        key: Tuple; represents the vehicle, alt, model year, age and discount rate.

    Returns:
        The NOx reduction for the passed model year vehicle in the given calendar year.

    Notes:
        The nox_reduction calculation should be done such that it is positive if action has lower nox than no action.

    """
    vehicle, alt, model_year, age_id, disc_rate = key
    no_action_key = vehicle, settings.no_action_alt, model_year, age_id, disc_rate
    nox_no_action = settings.fleet_cap.get_attribute_value(no_action_key, 'NOx_UStons')
    nox_action = settings.fleet_cap.get_attribute_value(key, 'NOx_UStons')
    nox_reduction = nox_no_action - nox_action

    return nox_reduction


# def calc_def_gallons(settings, vehicle, alt, calendar_year, model_year, totals_dict, fuel_arg):
#     """
#
#     Parameters:
#         settings: The SetInputs class. \n
#         vehicle: Tuple; represents an alt_sourcetype_regclass_fueltype vehicle. \n
#         alt: Numeric; represents the Alternative or optionID. \n
#         calendar_year: Numeric; represents the calendar year (yearID). \n
#         model_year: Numeric; represents the model year of the passed vehicle. \n
#         totals_dict: Dictionary; provides gallons (fuel consumption) by vehicle.\n
#         fuel_arg: String; specifies the fuel attribute to use (e.g., "Gallons" or "Gallons_withTech")
#
#     Returns:
#         The gallons of DEF consumption for the passed model year vehicle in the given calendar year.
#
#     """
#     calcs = FleetTotals(totals_dict)
#     age_id = calendar_year - model_year
#     gallons_fuel = calcs.get_attribute_value((vehicle, alt, model_year, age_id, 0), fuel_arg)
#     base_doserate = calc_def_doserate(settings, vehicle)
#     nox_reduction = calc_nox_reduction(settings, vehicle, alt, calendar_year, model_year, totals_dict)
#     gallons_def = gallons_fuel * base_doserate + nox_reduction * settings.def_gallons_per_ton_nox_reduction
#
#     return gallons_def


def calc_def_costs(settings):
    """

    Parameters:
        settings: The SetInputs class.

    Returns:
        The passed dictionary updated with costs associated with DEF consumption.

    """
    print('\nCalculating DEF costs...')

    # get keys where fueltype=2 (Diesel since they are the only vehicles that use DEF)
    ft2_keys = [k for k, v in settings.fleet_cap._data.items() if v['fuelTypeID'] == 2]

    def_gallons_per_ton_nox_reduction \
        = pd.to_numeric(settings.general_inputs.get_attribute_value('def_gallons_per_ton_nox_reduction'))

    for key in ft2_keys:
        vehicle, alt, model_year, age_id, disc_rate = key
        calendar_year = model_year + age_id

        def_price = settings.def_prices.get_price(calendar_year)
        gallons_fuel = settings.fleet_cap.get_attribute_value(key, 'Gallons_withTech')
        base_doserate = calc_def_doserate(settings, vehicle)
        nox_reduction = calc_nox_reduction(settings, key)

        gallons_def = gallons_fuel * base_doserate + nox_reduction * def_gallons_per_ton_nox_reduction
        cost = def_price * gallons_def

        update_dict = {'DEF_Gallons': gallons_def,
                       'DEFCost': cost,
                       }
        settings.fleet_cap.update_dict(key, update_dict)


def calc_def_costs_per_veh(settings, sales_arg):
    """

    Parameters:
        settings: The SetInputs class.\n
        sales_arg: String; the sales to use when calculating sales * cost/veh.

    Returns:
        Updates the fleet dictionary with costs/mile and costs/vehicle associated with DEF consumption.

    """
    print('\nCalculating DEF average costs...')

    # get keys where fueltype=2 (Diesel since they are the only vehicles that use DEF)
    ft2_keys = [k for k, v in settings.fleet_cap._data.items() if v['fuelTypeID'] == 2]

    for key in ft2_keys:
        def_cost = settings.fleet_cap.get_attribute_value(key, 'DEFCost')
        vmt = settings.fleet_cap.get_attribute_value(key, 'VMT_withTech')
        vpop = settings.fleet_cap.get_attribute_value(key, sales_arg)
        cost_per_mile = def_cost / vmt
        cost_per_veh = def_cost / vpop

        update_dict = {'DEFCost_PerMile': cost_per_mile,
                       'DEFCost_PerVeh': cost_per_veh,
                       }
        settings.fleet_cap.update_dict(key, update_dict)

#
# def calc_def_doserate(settings, vehicle):
#     """
#
#     Parameters:
#         settings: The SetInputs class \n
#         vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
#
#     Returns:
#         The DEF dose rate for the passed vehicle based on the DEF dose rate input file.
#
#     """
#     def_doserate_dict = InputFileDict(settings.def_doserate_inputs_dict)
#
#     st, rc, ft = vehicle
#     nox_std = def_doserate_dict.get_attribute_value((rc, ft), 'standard_NOx')
#     nox_engine_out = def_doserate_dict.get_attribute_value((rc, ft), 'engineout_NOx')
#     doserate_intercept = def_doserate_dict.get_attribute_value((rc, ft), 'intercept_DEFdoserate')
#     doserate_slope =  def_doserate_dict.get_attribute_value((rc, ft), 'slope_DEFdoserate')
#     base_doserate = ((nox_std - nox_engine_out) - doserate_intercept) / doserate_slope
#
#     return base_doserate
#
#
# def calc_nox_reduction(settings, vehicle, alt, calendar_year, model_year, totals_dict):
#     """
#
#     Parameters:
#         settings: The SetInputs class. \n
#         vehicle: Tuple; represents an alt_sourcetype_regclass_fueltype vehicle. \n
#         alt: Numeric; represents the Alternative or optionID. \n
#         calendar_year: Numeric; represents the calendar year (yearID). \n
#         model_year: Numeric; represents the model year of the passed vehicle. \n
#         totals_dict: Dictionary; provides fleet NOx tons by vehicle.
#
#     Returns:
#         The NOx reduction for the passed model year vehicle in the given calendar year.
#
#     """
#     calcs = FleetTotals(totals_dict)
#     age_id = calendar_year - model_year
#     nox_no_action = calcs.get_attribute_value((vehicle, settings.no_action_alt, model_year, age_id, 0), 'NOx_UStons')
#     nox_action = calcs.get_attribute_value((vehicle, alt, model_year, age_id, 0), 'NOx_UStons')
#     nox_reduction = nox_no_action - nox_action
#
#     return nox_reduction
#
#
# def calc_def_gallons(settings, vehicle, alt, calendar_year, model_year, totals_dict, fuel_arg):
#     """
#
#     Parameters:
#         settings: The SetInputs class. \n
#         vehicle: Tuple; represents an alt_sourcetype_regclass_fueltype vehicle. \n
#         alt: Numeric; represents the Alternative or optionID. \n
#         calendar_year: Numeric; represents the calendar year (yearID). \n
#         model_year: Numeric; represents the model year of the passed vehicle. \n
#         totals_dict: Dictionary; provides gallons (fuel consumption) by vehicle.\n
#         fuel_arg: String; specifies the fuel attribute to use (e.g., "Gallons" or "Gallons_withTech")
#
#     Returns:
#         The gallons of DEF consumption for the passed model year vehicle in the given calendar year.
#
#     """
#     calcs = FleetTotals(totals_dict)
#     age_id = calendar_year - model_year
#     gallons_fuel = calcs.get_attribute_value((vehicle, alt, model_year, age_id, 0), fuel_arg)
#     base_doserate = calc_def_doserate(settings, vehicle)
#     nox_reduction = calc_nox_reduction(settings, vehicle, alt, calendar_year, model_year, totals_dict)
#     gallons_def = gallons_fuel * base_doserate + nox_reduction * settings.def_gallons_per_ton_nox_reduction
#
#     return gallons_def
#
#
# def calc_def_costs(settings, totals_dict, fuel_arg):
#     """
#
#     Parameters:
#         settings: The SetInputs class. \n
#         totals_dict: Dictionary; provides fleet DEF consumption by vehicle.\n
#         fuel_arg: String; specifies the fuel attribute to use (e.g., "Gallons" or "Gallons_withTech")
#
#     Returns:
#         The passed dictionary updated with costs associated with DEF consumption.
#
#     """
#     print('\nCalculating DEF costs...')
#     calcs = FleetTotals(totals_dict)
#     prices = InputFileDict(settings.def_prices_dict)
#
#     # get keys where fueltype=2 (Diesel since they are the only vehicles that use DEF)
#     ft2_keys = [k for k, v in totals_dict.items() if v['fuelTypeID'] == 2]
#
#     for key in ft2_keys:
#         vehicle, alt, model_year, age_id, disc_rate = key
#         calendar_year = model_year + age_id
#         def_price = prices.get_attribute_value(calendar_year, 'DEF_USDperGal')
#         gallons_def = calc_def_gallons(settings, vehicle, alt, calendar_year, model_year, totals_dict, fuel_arg)
#         cost = def_price * gallons_def
#
#         temp_dict = {'DEF_Gallons': gallons_def,
#                      'DEFCost': cost,
#                      }
#         calcs.update_dict(key, temp_dict)
#
#     return totals_dict
#
#
# def calc_average_def_costs(totals_dict, averages_dict, vpop_arg):
#     """
#
#     Parameters:
#         totals_dict: Dictionary; provides fleet DEF costs by vehicle. \n
#         averages_dict: Dictionary, into which DEF costs/vehicle will be updated.\n
#         vpop_arg: String; specifies the population attribute to use (e.g., "VPOP" or "VPOP_withTech")
#
#     Returns:
#         The passed dictionary updated with costs/mile and costs/vehicle associated with DEF consumption.
#
#     """
#     print('\nCalculating DEF average costs...')
#
#     calcs_avg = FleetAverages(averages_dict)
#     calcs = FleetTotals(totals_dict)
#
#     # get keys where fueltype=2 (Diesel since they are the only vehicles that use DEF)
#     ft2_keys = [k for k, v in averages_dict.items() if v['fuelTypeID'] == 2]
#
#     for key in ft2_keys:
#         def_cost = calcs.get_attribute_value(key, 'DEFCost')
#         vmt = calcs.get_attribute_value(key, 'VMT')
#         vpop = calcs.get_attribute_value(key, vpop_arg)
#         cost_per_mile = def_cost / vmt
#         cost_per_veh = def_cost / vpop
#
#         temp_dict = {'DEFCost_AvgPerMile': cost_per_mile,
#                      'DEFCost_AvgPerVeh': cost_per_veh,
#                      }
#         calcs_avg.update_dict(key, temp_dict)
#
#     return averages_dict
