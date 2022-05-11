import pandas as pd


def calc_avg_package_cost_per_step(settings, vehicle, start_year):
    """
    Tech penetrations are applied here
    Parameters:
        settings: object; the SetInputs class object.
        vehicle: object; an object of the Vehicle class.
        start_year: int; the implementation year associated with the cost.

    Returns:
        Updates the sales object dictionary to include the year-over-year package costs, including learning
        effects, associated with each cost step.

    """
    learning_rate = pd.to_numeric(settings.general_inputs.get_attribute_value('learning_rate'))

    engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
    key = (engine_id, option_id, modelyear_id)

    pkg_cost = techpen = pkg_cost_learned = pkg_applied_cost_learned = 0

    if modelyear_id < start_year:
        pass
    else:
        techpen = settings.techpens_cap.get_attribute_value(vehicle)

        sales_year1 \
            = settings.fleet_cap.sales_by_start_year[engine_id, option_id, start_year]['engine_sales'] \
              * techpen

        cumulative_sales \
            = settings.fleet_cap.sales_by_start_year[key][f'cumulative_engine_sales_{start_year}_std']\
              * techpen

        pkg_cost = settings.engine_costs.get_start_year_cost((engine_id, option_id, start_year), 'pkg_cost')

        seedvolume_factor = settings.engine_learning_scalers.get_seedvolume_factor(engine_id, option_id)

        if sales_year1 + (sales_year1 * seedvolume_factor) != 0:
            pkg_cost_learned = pkg_cost \
                               * ((cumulative_sales + (sales_year1 * seedvolume_factor))
                                  / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate
            pkg_applied_cost_learned = pkg_cost_learned * techpen
        else:
            pass

    update_dict = {
        'optionID': vehicle.option_id,
        'engineID': vehicle.engine_id,
        'regClassID': vehicle.regclass_id,
        'fuelTypeID': vehicle.fueltype_id,
        'modelYearID': vehicle.modelyear_id,
        'optionName': vehicle.option_name,
        'regClassName': vehicle.regclass_name,
        'fuelTypeName': vehicle.fueltype_name,
        f'tech_cost_per_vehicle_{start_year}_std': pkg_cost_learned,
        f'techpen_{start_year}_std': techpen,
        f'tech_applied_cost_per_vehicle_{start_year}_std': pkg_applied_cost_learned,
    }

    settings.engine_costs.update_package_cost_by_step(vehicle, update_dict)


def calc_package_cost(settings, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        vehicle: object; an object of the Vehicle class.

    Returns:
        The package average cost and package cost associated with the passed vehicle.

    """
    engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
    start_years = settings.engine_costs.start_years

    if option_id == settings.no_action_alt:
        start_year = start_years[0]
        pkg_cost_per_veh \
            = settings.engine_costs.get_package_cost_by_step(
            (engine_id, option_id, modelyear_id),
            f'tech_cost_per_vehicle_{start_year}_std')[0]
        cost_per_veh \
            = settings.engine_costs.get_package_cost_by_step(
            (engine_id, option_id, modelyear_id),
            f'tech_applied_cost_per_vehicle_{start_year}_std')[0]
    else:
        pkg_cost_per_veh \
            = settings.engine_costs.get_package_cost_by_step(
            (engine_id, settings.no_action_alt, modelyear_id),
            f'tech_cost_per_vehicle_{start_years[0]}_std')[0]
        cost_per_veh \
            = settings.engine_costs.get_package_cost_by_step(
            (engine_id, settings.no_action_alt, modelyear_id),
            f'tech_applied_cost_per_vehicle_{start_years[0]}_std')[0]
        for start_year in start_years:
            if modelyear_id >= int(start_year):
                pkg_cost_per_veh \
                    += settings.engine_costs.get_package_cost_by_step(
                    (engine_id, option_id, modelyear_id),
                    f'tech_cost_per_vehicle_{start_year}_std')[0]
                cost_per_veh \
                    += settings.engine_costs.get_package_cost_by_step(
                    (engine_id, option_id, modelyear_id),
                    f'tech_applied_cost_per_vehicle_{start_year}_std')[0]

    cost = cost_per_veh * vehicle.vpop

    return cost_per_veh, cost, pkg_cost_per_veh


if __name__ == '__main__':
    from bca_tool_code.tool_setup import SetPaths
    from bca_tool_code.general_input_modules.options import Options
    # vehicle = settings.cap_vehicles_list[0]
    cost_step = '2027'

    set_paths = SetPaths()

    df = pd.DataFrame({
        'year_id': [2027, 2028, 2028, 2029, 2029, 2029, 2030, 2030, 2030, 2030],
        'sourcetype_id': [62, 62, 62, 62, 62, 62, 62, 62, 62, 62],
        'regclass_id': [47, 47, 47, 47, 47, 47, 47, 47, 47, 47],
        'fueltype_id': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'modelyear_id': [2027, 2027, 2028, 2028, 2027, 2028, 2029, 2027, 2029, 2029, 2030],
        'option_id': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'vpop': [75761, 76128.20313, 78092, 76628.79688, 78605.5, 80412.20313, 77234.5, 79226.89844, 81047.79688, 81878.29688]
    }
    )

    options_cap = Options()
    options_cap.init_from_file(set_paths.path_inputs / 'options_cap.csv')
    # cap_vehicls = Vehicles().create_cap_vehicles(options_cap)
