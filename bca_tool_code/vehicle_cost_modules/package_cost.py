import pandas as pd


def calc_avg_package_cost_per_step(settings, vehicle, start_year):
    """

    Parameters:
        settings: object; the SetInputs class object.
        vehicle: object; an object of the Vehicle class.
        start_year: int; the implementation year associated with the cost.

    Returns:
        Updates to the sales object dictionary to include the year-over-year package costs, including learning
        effects, at each cost step.

    """
    learning_rate = pd.to_numeric(settings.general_inputs.get_attribute_value('learning_rate'))

    vehicle_id, option_id, modelyear_id = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
    key = (vehicle_id, option_id, modelyear_id)

    pkg_cost = techpen = pkg_cost_learned = pkg_applied_cost_learned = 0

    if modelyear_id < start_year:
        pass
    else:
        techpen = settings.techpens_ghg.get_attribute_value(vehicle)

        sales_year1 \
            = settings.fleet_ghg.sales_by_start_year[vehicle_id, option_id, start_year][f'cumulative_vehicle_sales_{start_year}_std'] \
              * techpen

        cumulative_sales \
            = settings.fleet_ghg.sales_by_start_year[key][f'cumulative_vehicle_sales_{start_year}_std'] \
              * techpen

        pkg_cost = settings.vehicle_costs.get_start_year_cost((vehicle_id, option_id, start_year), 'pkg_cost')

        seedvolume_factor = settings.vehicle_learning_scalers.get_seedvolume_factor(vehicle_id, option_id)

        if sales_year1 + (sales_year1 * seedvolume_factor) != 0:
            pkg_cost_learned = pkg_cost \
                               * ((cumulative_sales + (sales_year1 * seedvolume_factor))
                                   / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate
            pkg_applied_cost_learned = pkg_cost_learned * techpen
        else:
            pass

    update_dict = {
        'optionID': vehicle.option_id,
        'vehicleID': vehicle.vehicle_id,
        'sourceTypeID': vehicle.sourcetype_id,
        'regClassID': vehicle.regclass_id,
        'fuelTypeID': vehicle.fueltype_id,
        'modelYearID': vehicle.modelyear_id,
        'optionName': vehicle.option_name,
        'sourceTypeName': vehicle.sourcetype_name,
        'regClassName': vehicle.regclass_name,
        'fuelTypeName': vehicle.fueltype_name,
        f'tech_cost_per_vehicle_{start_year}_std': pkg_cost_learned,
        f'techpen_{start_year}_std': techpen,
        f'tech_applied_cost_per_vehicle_{start_year}_std': pkg_applied_cost_learned,
    }

    settings.vehicle_costs.update_package_cost_by_step(vehicle, update_dict)


def calc_package_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        The package average cost and package cost associated with the passed vehicle.

    """
    vehicle_id, option_id, modelyear_id = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
    start_years = settings.vehicle_costs.start_years

    if option_id == settings.no_action_alt:
        start_year = start_years[0]
        pkg_cost_per_veh \
            = settings.vehicle_costs.get_package_cost_by_step(
            (vehicle_id, option_id, modelyear_id),
            f'tech_cost_per_vehicle_{start_year}_std')[0]
        cost_per_veh \
            = settings.vehicle_costs.get_package_cost_by_step(
            (vehicle_id, option_id, modelyear_id),
            f'tech_applied_cost_per_vehicle_{start_year}_std')[0]
    else:
        pkg_cost_per_veh \
            = settings.vehicle_costs.get_package_cost_by_step(
            (vehicle_id, settings.no_action_alt, modelyear_id),
            f'tech_cost_per_vehicle_{start_years[0]}_std')[0]
        cost_per_veh \
            = settings.vehicle_costs.get_package_cost_by_step(
            (vehicle_id, settings.no_action_alt, modelyear_id),
            f'tech_applied_cost_per_vehicle_{start_years[0]}_std')[0]
        for start_year in start_years:
            if modelyear_id >= int(start_year):
                pkg_cost_per_veh \
                    += settings.vehicle_costs.get_package_cost_by_step(
                    (vehicle_id, option_id, modelyear_id),
                    f'tech_cost_per_vehicle_{start_year}_std')[0]
                cost_per_veh \
                    += settings.vehicle_costs.get_package_cost_by_step(
                    (vehicle_id, option_id, modelyear_id),
                    f'tech_applied_cost_per_vehicle_{start_year}_std')[0]

    cost = cost_per_veh * vehicle.vpop

    return cost_per_veh, cost, pkg_cost_per_veh
