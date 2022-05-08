

# def calc_typical_vmt_per_year(settings, vehicle):
#     """
#     This function calculates a typical annual VMT/vehicle over a set number of years as set via the General Inputs
#     workbook. This typical annual VMT/vehicle can then be used to estimate the ages at which warranty and useful life
#     will be reached. When insufficient years are available -- e.g., if the typical_vmt_thru_ageID is set to >5 years and
#     the given vehicle is a MY2041 vintage vehicle and the fleet input file contains data only thru CY2045, then
#     insufficient data exist to calculate the typical VMT for that vehicle -- the typical VMT for that vehicle will be
#     set equal to the last prior MY vintage for which sufficient data were present.
#
#     Parameters:
#         settings: object; the SetInputs class object.\n
#         vehicle: object; an object of the Vehicle class.\n
#
#     Returns:
#         A single typical annual VMT/veh value for the given vehicle.
#
#     """
#     vmt_thru_age_id = int(settings.repair_and_maintenance.get_attribute_value('typical_vmt_thru_ageID'))
#     year_max = settings.cap_vehicle.year_max
#
#     if vehicle.modelyear_id + vmt_thru_age_id <= year_max:
#         year = vehicle.modelyear_id
#     else:
#         year = year_max - vmt_thru_age_id # can't get appropriate cumulative VMT if modelyear+vmt_thru_age_id>year_max
#
#     cumulative_vmt = settings.fleet_cap.cumulative_vmt_dict[vehicle.vehicle_id, vehicle.option_id, year, vehicle.age_id]
#
#     typical_vmt = cumulative_vmt / (vmt_thru_age_id + 1)
#
#     return typical_vmt
#
#
# def calc_estimated_age(settings, vehicle, typical_vmt):
#     """
#
#     Parameters:
#         settings: object; the SetInputs class object.\n
#         vehicle: object; an object of the Vehicle class.\n
#         typical_vmt: numeric; the typical annual VMT/vehicle over a set number of years as set via the General Inputs
#         workbook (see calc_typical_vmt_per_year function).
#
#     Returns:
#         Updates the estimated ages dictionary with the ages at which warranty and useful life will be reached for the
#         passed key.
#
#     """
#     miles_and_ages_dict = {'Warranty': settings.warranty,
#                            'UsefulLife': settings.useful_life,
#                            }
#
#     for identifier in ['Warranty', 'UsefulLife']:
#         miles_and_ages = miles_and_ages_dict[identifier]
#         estimated_ages_dict_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, identifier
#
#         required_age \
#             = miles_and_ages.get_attribute_value((vehicle.engine_id, vehicle.option_id, 'Age'), str(vehicle.modelyear_id))
#         required_miles \
#             = miles_and_ages.get_attribute_value((vehicle.engine_id, vehicle.option_id, 'Miles'), str(vehicle.modelyear_id))
#         calculated_age = round(required_miles / typical_vmt)
#         estimated_age = min(required_age, calculated_age)
#         settings.estimated_ages_dict[estimated_ages_dict_key] = ({'vehicle': vehicle.vehicle_id,
#                                                                   'optionID': vehicle.option_id,
#                                                                   'modelYearID': vehicle.modelyear_id,
#                                                                   'identifier': identifier,
#                                                                   'typical_vmt': typical_vmt,
#                                                                   'required_age': required_age,
#                                                                   'calculated_age': calculated_age,
#                                                                   'estimated_age': estimated_age,
#                                                                   })
class EmissionRepairCost:

    def __init__(self):
        self.repair_cpm_dict = dict()

    def calc_emission_repair_cost(self, settings, vehicle, pkg_cost, reference_pkg_cost):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            data_object: object; the fleet data object.

        Returns:
            Updates the data_object dictionary to include emission repair costs/mile.\n
            Updates the repair cost/mile dictionary (repair_cpm_dict) containing details used in the calculation of repair
            cost/mile; this dictionary is then written to an output file for the given run.

        """
        in_warranty_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('in-warranty_R&M_CPM')
        at_usefullife_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('at-usefullife_R&M_CPM')
        max_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('max_R&M_CPM')
        emission_repair_share_input_value = settings.repair_and_maintenance.get_attribute_value('emission_repair_share')

        veh_id, option, my, age = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id

        direct_cost_scaler = pkg_cost / reference_pkg_cost

        typical_vmt = settings.fleet_cap.calc_typical_vmt_per_year(settings, vehicle)

        # calculate estimated ages at which warranty and useful life will occur
        warranty_estimated_age, usefullife_estimated_age \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt, 'Warranty', 'UsefulLife')
        # warranty_estimated_age = settings.estimated_ages_dict[veh_id, option, my, 'Warranty']['estimated_age']
        # usefullife_estimated_age = settings.estimated_ages_dict[veh_id, option, my, 'UsefulLife']['estimated_age']

        in_warranty_cpm = in_warranty_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        at_usefullife_cpm = at_usefullife_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        max_cpm = max_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler

        # calculate the slope of the cost per mile curve between warranty and useful life estimated ages
        if usefullife_estimated_age > warranty_estimated_age:
            slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) \
                                      / (usefullife_estimated_age - warranty_estimated_age)
        else:
            slope_within_usefullife = 0

        # now calulate the cost per mile
        if (age + 1) < warranty_estimated_age:
            cpm = in_warranty_cpm
        elif warranty_estimated_age <= (age + 1) < usefullife_estimated_age:
            cpm = slope_within_usefullife * ((age + 1) - warranty_estimated_age) + in_warranty_cpm
        elif (age + 1) == usefullife_estimated_age:
            cpm = at_usefullife_cpm
        else:
            cpm = max_cpm

        self.repair_cpm_dict[veh_id, option, my, age] = {
            'reference_direct_cost': reference_pkg_cost,
            'direct_cost_scaler': direct_cost_scaler,
            'warranty_estimated_age': warranty_estimated_age,
            'usefullife_estimated_age': usefullife_estimated_age,
            'in_warranty_cpm': in_warranty_cpm,
            'at_usefullife_cpm': at_usefullife_cpm,
            'slope_within_usefullife': slope_within_usefullife,
            'max_cpm': max_cpm,
            'cpm': cpm
        }

        cost_per_veh = cpm * vehicle.vmt_per_veh
        cost = cost_per_veh * vehicle.vpop

        return cost_per_veh, cost, cpm

#
# def calc_emission_repair_costs_per_veh(data_object):
#     """
#
#     Parameters:
#         data_object: object; the fleet data object.
#
#     Returns:
#         Updates the data_object dictionary with annual emission repair costs/vehicle for each dictionary key.
#
#     """
#     print('\nCalculating emission repair costs per vehicle...')
#
#     for key in data_object.keys:
#         repair_cpm = data_object.get_attribute_value(key, 'EmissionRepairCost_PerMile')
#         vmt_per_veh = data_object.get_attribute_value(key, 'VMT_PerVeh')
#         cost_per_veh = repair_cpm * vmt_per_veh
#
#         update_dict = {'EmissionRepairCost_PerVeh': cost_per_veh}
#         data_object.update_dict(key, update_dict)
#
#
# def calc_emission_repair_costs(data_object):
#     """
#
#     Parameters:
#         data_object: object; the fleet data object.
#
#     Returns:
#         Updates the data_object dictionary with emission repair costs for all vehicles.
#
#     """
#     print(f'\nCalculating total emission repair costs...')
#
#     for key in data_object.keys:
#         cost_per_veh = data_object.get_attribute_value(key, 'EmissionRepairCost_PerVeh')
#         vpop = data_object.get_attribute_value(key, 'VPOP')
#         cost = cost_per_veh * vpop
#
#         update_dict = {'EmissionRepairCost': cost}
#         data_object.update_dict(key, update_dict)
