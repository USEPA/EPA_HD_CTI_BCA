

base_doserate_dict = dict()


def calc_def_doserate(settings, vehicle):
    """

    Args:
        settings: The SetInputs class.
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.

    Returns: The DEF dose rate for the passed vehicle based on the DEF dose rate input file.

    """
    alt, st, rc, ft = vehicle
    base_doserate_dict_id = (rc, ft)
    if base_doserate_dict_id in base_doserate_dict:
        base_doserate = base_doserate_dict[base_doserate_dict_id]
    else:
        nox_std = settings.def_doserate_inputs_dict[(rc, ft)]['standard_NOx']
        nox_engine_out = settings.def_doserate_inputs_dict[(rc, ft)]['engineout_NOx']
        doserate_intercept = settings.def_doserate_inputs_dict[(rc, ft)]['intercept_DEFdoserate']
        doserate_slope = settings.def_doserate_inputs_dict[(rc, ft)]['slope_DEFdoserate']
        base_doserate = ((nox_std - nox_engine_out) - doserate_intercept) / doserate_slope
        base_doserate_dict[base_doserate_dict_id] = base_doserate
    return base_doserate


def calc_nox_reduction(settings, vehicle, year, model_year, totals_dict):
    """

    Args:
        settings: The SetInputs class.
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.
        year: The calendar year (yearID).
        model_year: The model year of the passed vehicle.
        totals_dict: A dictionary of fleet NOx tons by vehicle.

    Returns: The NOx reduction for the passed model year vehicle in the given calendar year.

    """
    alt, st, rc, ft = vehicle
    age_id = year - model_year
    nox_reduction = totals_dict[((settings.no_action_alt, st, rc, ft), model_year, age_id, 0)]['NOx_UStons'] \
                    - totals_dict[((vehicle), model_year, age_id, 0)]['NOx_UStons']
    return nox_reduction


def calc_def_gallons(settings, vehicle, year, model_year, totals_dict):
    """

    Args:
        settings: The SetInputs class.
        vehicle: A tuple representing an alt_sourcetype_regclass_fueltype vehicle.
        year: The calendar year (yearID).
        model_year: The model year of the passed vehicle.
        totals_dict: A dictionary of fleet Gallons (fuel consumption) by vehicle.

    Returns: The gallons of DEF consumption for the passed model year vehicle in the given calendar year.

    """
    age_id = year - model_year
    gallons_fuel = totals_dict[((vehicle), model_year, age_id, 0)]['Gallons']
    base_doserate = calc_def_doserate(settings, vehicle)
    nox_reduction = calc_nox_reduction(settings, vehicle, year, model_year, totals_dict)
    gallons_def = gallons_fuel * base_doserate + nox_reduction * settings.def_gallons_per_ton_nox_reduction
    return gallons_def


def calc_def_costs(settings, totals_dict):
    """

    Args:
        settings: The SetInputs class.
        totals_dict: A dictionary of fleet DEF consumption by vehicle.

    Returns: The passed dictionary updated with costs associated with DEF consumption.

    """
    print('\nCalculating total DEF costs.')
    for key in totals_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if ft == 2:
            year = model_year + age_id
            def_price = settings.def_prices_dict[year]['DEF_USDperGal']
            gallons_def = calc_def_gallons(settings, vehicle, year, model_year, totals_dict)
            totals_dict[key].update({'DEF_Gallons': gallons_def, 'DEFCost': def_price * gallons_def})
    return totals_dict


def calc_average_def_costs(totals_dict, averages_dict):
    """

    Args:
        totals_dict: A dictionary of fleet DEF costs by vehicle.
        averages_dict: A dictionary into which DEF costs/vehicle will be updated.

    Returns: The passed dictionary updated with costs/mile and costs/vehicle associated with DEF consumption.

    """
    for key in averages_dict.keys():
        vehicle, model_year, age_id = key[0], key[1], key[2]
        alt, st, rc, ft = vehicle
        if ft == 2:
            print(f'Calculating DEF average cost per mile for {vehicle}, MY {model_year}, age {age_id}.')
            def_cost = totals_dict[key]['DEFCost']
            vmt = totals_dict[key]['VMT']
            vpop = totals_dict[key]['VPOP']
            averages_dict[key].update({'DEFCost_AvgPerMile': def_cost / vmt})
            averages_dict[key].update({'DEFCost_AvgPerVeh': def_cost / vpop})
    return averages_dict


if __name__ == '__main__':
    from cti_bca_tool.tool_setup import SetInputs as settings
    from cti_bca_tool.project_fleet import create_fleet_df, sourcetype_vehicles
    from cti_bca_tool.project_dicts import create_fleet_totals_dict, create_fleet_averages_dict
    from cti_bca_tool.general_functions import save_dict_to_csv

    project_fleet_df = create_fleet_df(settings)
    fleet_totals_dict = create_fleet_totals_dict(project_fleet_df)
    fleet_averages_dict = create_fleet_averages_dict(project_fleet_df)

    vehicles_st = sourcetype_vehicles(project_fleet_df)

    fleet_totals_dict = calc_def_costs(settings, fleet_totals_dict)
    fleet_averages_dict = calc_average_def_costs(fleet_totals_dict, fleet_averages_dict)

    save_dict_to_csv(fleet_totals_dict, settings.path_project / 'test/cti_fleet_totals', 'vehicle', 'modelYearID', 'ageID')
    save_dict_to_csv(fleet_averages_dict, settings.path_project / 'test/cti_fleet_averages', 'vehicle', 'modelYearID', 'ageID')
