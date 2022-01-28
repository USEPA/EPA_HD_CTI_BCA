from bca_tool_code.fleet_totals_dict import FleetTotals
from bca_tool_code.fleet_averages_dict import FleetAverages
from bca_tool_code.project_dicts import InputFileDict


def get_orvr_adjustment(settings, vehicle, alt, program):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; the Alternative or option ID. \n
        program: String; represents which program is being run, CAP or GHG.

    Returns:
        A single value representing the milliliter per gram adjustment to be applied to total hydrocarbon emission reductions to
        estimate the gallons of fuel saved.

    """
    if program == 'CAP': orvr_inputs = InputFileDict(settings.orvr_inputs_dict_cap)
    else: orvr_inputs = InputFileDict(settings.orvr_inputs_dict_ghg)

    st, rc, ft = vehicle
    engine = (rc, ft)
    orvr_inputs_key = (engine, alt)
    adjustment = orvr_inputs.get_attribute_value(orvr_inputs_key, 'ml/g')

    return adjustment


def calc_thc_reduction(settings, vehicle, alt, calendar_year, model_year, totals_dict):
    """
    
    Parameters:
        settings: The SetInputs class.\n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; the Alternative or option ID.\n
        calendar_year: Numeric; the calendar year.\n
        model_year: Numeric; the model year of the passed vehicle.\n
        totals_dict: Dictionary; provides fleet total hydrocarbon (THC) tons by vehicle.

    Returns:
        A single THC reduction for the given model year vehicle in the given year.

    """
    calcs = FleetTotals(totals_dict)
    age = calendar_year - model_year
    thc_no_action = calcs.get_attribute_value((vehicle, settings.no_action_alt, model_year, age, 0), 'THC_UStons')
    thc_action = calcs.get_attribute_value((vehicle, alt, model_year, age, 0), 'THC_UStons')
    thc_reduction = thc_no_action - thc_action

    return thc_reduction


def calc_captured_gallons(settings, vehicle, alt, calendar_year, model_year, totals_dict, program):
    """

    Parameters:
        settings: The SetInputs class.\n
        vehicle: Tuple; represents a sourcetype_regclass_fueltype vehicle.\n
        alt: Numeric; the Alternative or option ID.\n
        calendar_year: Numeric; the calendar year.\n
        model_year: Numeric; the model year of the passed vehicle.\n
        totals_dict: Dictionary; provides fleet total hydrocarbon (THC) tons by vehicle.
        program: String; represents which program is being run, CAP or GHG.

    Returns:
        The gallons captured by ORVR that would have otherwise evaporated during refueling.

    """
    adjustment = get_orvr_adjustment(settings, vehicle, alt, program)
    thc_reduction = calc_thc_reduction(settings, vehicle, alt, calendar_year, model_year, totals_dict)
    captured_gallons = thc_reduction * adjustment * settings.grams_per_short_ton * settings.gallons_per_ml

    return captured_gallons


def calc_fuel_costs(settings, totals_dict, fuel_arg, program):
    """

    Parameters:
        settings: The SetInputs class.\n
        totals_dict: Dictionary; provides the fleet Gallons consumed by all vehicles. \n
        fuel_arg: String; specifies the fuel attribute to use (e.g., "Gallons" or "Gallons_withTech")\n
        program: String; represents which program is being run, CAP or GHG.

    Returns:
        The passed dictionary updated to reflect fuel consumption (Gallons) adjusted to account for the fuel saved in association with ORVR.
        The dictionary is also updated to include the fuel costs associated with the gallons consumed (Gallons * $/gallon fuel).

    Note:
        Note that gallons of fuel captured are not included in the MOVES runs that serve as the input fleet data for the tool although the inventory impacts
        are included in the MOVES runs.

    """
    print('\nCalculating CAP-related fuel costs...')

    calcs = FleetTotals(totals_dict)
    prices = InputFileDict(settings.fuel_prices_dict)

    for key in totals_dict.keys():
        captured_gallons = 0
        vehicle, alt, model_year, age_id, disc_rate = key
        st, rc, ft = vehicle
        calendar_year = model_year + age_id
        fuel_price_retail = prices.get_attribute_value((calendar_year, ft), 'retail_fuel_price')
        fuel_price_pretax = prices.get_attribute_value((calendar_year, ft), 'pretax_fuel_price')
        if ft == 1:
            captured_gallons = calc_captured_gallons(settings, vehicle, alt, calendar_year, model_year, totals_dict, program)

        gallons = calcs.get_attribute_value(key, fuel_arg)
        gallons_paid_for = gallons - captured_gallons

        cost_retail = fuel_price_retail * gallons_paid_for
        cost_pretax = fuel_price_pretax * gallons_paid_for

        temp_dict = {'GallonsCaptured_byORVR': captured_gallons,
                     'FuelCost_Retail': cost_retail,
                     'FuelCost_Pretax': cost_pretax,
                     }
        calcs.update_dict(key, temp_dict)

    return totals_dict


def calc_average_fuel_costs(totals_dict, averages_dict, vpop_arg, vmt_arg):
    """

    Parameters:
        totals_dict: Dictionary; provides fleet fuel costs for all vehicles.\n
        averages_dict: Dictionary; the destination for fuel costs/vehicle and costs/mile results.\n
        vpop_arg: String; specifies the population attribute to use (e.g., "VPOP" or "VPOP_withTech")\n
        vmt_arg: String; specifies the VMT attribute to use (e.g., "VMT" or "VMT_withTech")

    Returns:
        The passed averages_dict updated to include fuel costs/vehicle and costs/mile.

    """
    print('\nCalculating average fuel costs...')
    calcs_avg = FleetAverages(averages_dict)
    calcs = FleetTotals(totals_dict)

    for key in averages_dict.keys():
        fuel_cost = calcs.get_attribute_value(key, 'FuelCost_Retail')
        vmt = calcs.get_attribute_value(key, vmt_arg)
        vpop = calcs.get_attribute_value(key, vpop_arg)

        # try/except block to protect against divide by 0 error
        try:
            cost_per_mile = fuel_cost / vmt
            cost_per_veh = fuel_cost / vpop
        except:
            cost_per_mile = 0
            cost_per_veh = 0

        temp_dict = {'FuelCost_Retail_AvgPerMile': cost_per_mile,
                     'FuelCost_Retail_AvgPerVeh': cost_per_veh,
                     }
        calcs_avg.update_dict(key, temp_dict)

    return averages_dict
