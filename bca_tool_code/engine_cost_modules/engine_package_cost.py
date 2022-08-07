import pandas as pd


def calc_avg_package_cost_per_step(settings, cost_object, vehicle, standardyear_id, labor=False):
    """
    Tech penetrations are applied here
    Parameters:
        settings: object; the SetInputs class object.
        cost_object: object; an object of the PieceCost class (e.g., settings.engine_costs or settings.replacement_costs).
        vehicle: object; an object of the Vehicle class.
        standardyear_id: int; the implementation year associated with the cost.
        labor: boolean; if True, a labor cost from the RepairAndMaintenance class will be included in the package cost.

    Returns:
        Updates the engine_costs object dictionary to include the year-over-year package costs, including learning
        effects, associated with implementation of each new standard.

    """    
    learning_rate = pd.to_numeric(settings.general_inputs.get_attribute_value('learning_rate'))

    engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
    key = (engine_id, option_id, modelyear_id)

    pkg_cost = techpen = pkg_cost_learned = pkg_applied_cost_learned = learning_effect = labor_cost = 0
    if labor:
        labor_cost = settings.repair_and_maintenance.get_attribute_value(('replacement_cost_labor', 'dollars'))

    if modelyear_id < standardyear_id:
        pass
    else:
        if (engine_id, option_id, standardyear_id) not in cost_object._dict:
            pass
        else:

            techpen = settings.techpens_cap.get_attribute_value(vehicle, standardyear_id)

            sales_year1 \
                = settings.fleet_cap.sales_by_start_year[engine_id, option_id, standardyear_id]['engine_sales'] \
                  * techpen

            cumulative_sales \
                = settings.fleet_cap.sales_by_start_year[key][f'cumulative_engine_sales_{standardyear_id}_std']\
                  * techpen

            pkg_cost = cost_object.get_start_year_cost((engine_id, option_id, standardyear_id), 'pkg_cost')

            # seedvolume_factor = settings.engine_learning_scalers.get_seedvolume_factor(engine_id, option_id)

            # if sales_year1 + (sales_year1 * seedvolume_factor) != 0:
            if sales_year1 != 0:
                learning_effect \
                    = settings.engine_learning_scalers.calc_learning_effect(vehicle, sales_year1, cumulative_sales,
                                                                            learning_rate)

                # learning_effect = ((cumulative_sales + (sales_year1 * seedvolume_factor))
                #                    / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate

                pkg_cost_learned = pkg_cost * learning_effect + labor_cost
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
        f'learning_effect_{standardyear_id}_std': learning_effect,
        f'tech_cost_per_vehicle_{standardyear_id}_std': pkg_cost_learned,
        f'techpen_{standardyear_id}_std': techpen,
        f'tech_applied_cost_per_vehicle_{standardyear_id}_std': pkg_applied_cost_learned,
    }

    cost_object.update_package_cost_by_step(vehicle, update_dict)


def calc_package_cost(settings, cost_object, vehicle):
    """

    Parameters:
        settings: object; the SetInputs class object.\n
        cost_object: object; an object of the PieceCost class (e.g., settings.engine_costs or settings.replacement_costs).
        vehicle: object; an object of the Vehicle class.

    Returns:
        The package average cost and package cost associated with the passed vehicle.

    """
    engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
    standardyear_ids = cost_object.standardyear_ids

    if option_id == settings.no_action_alt:
        standardyear_id = standardyear_ids[0]
        pkg_cost_per_veh \
            = cost_object.get_package_cost_by_standardyear_id(
            (engine_id, option_id, modelyear_id),
            f'tech_cost_per_vehicle_{standardyear_id}_std')[0]
        cost_per_veh \
            = cost_object.get_package_cost_by_standardyear_id(
            (engine_id, option_id, modelyear_id),
            f'tech_applied_cost_per_vehicle_{standardyear_id}_std')[0]
    else:
        pkg_cost_per_veh \
            = cost_object.get_package_cost_by_standardyear_id(
            (engine_id, settings.no_action_alt, modelyear_id),
            f'tech_cost_per_vehicle_{standardyear_ids[0]}_std')[0]
        cost_per_veh \
            = cost_object.get_package_cost_by_standardyear_id(
            (engine_id, settings.no_action_alt, modelyear_id),
            f'tech_applied_cost_per_vehicle_{standardyear_ids[0]}_std')[0]
        for standardyear_id in standardyear_ids:
            if modelyear_id >= int(standardyear_id):
                pkg_cost_per_veh \
                    += cost_object.get_package_cost_by_standardyear_id(
                    (engine_id, option_id, modelyear_id),
                    f'tech_cost_per_vehicle_{standardyear_id}_std')[0]
                cost_per_veh \
                    += cost_object.get_package_cost_by_standardyear_id(
                    (engine_id, option_id, modelyear_id),
                    f'tech_applied_cost_per_vehicle_{standardyear_id}_std')[0]

    cost = cost_per_veh * vehicle.vpop

    return cost_per_veh, cost, pkg_cost_per_veh


if __name__ == '__main__':
    from bca_tool_code.set_inputs import SetPaths
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
