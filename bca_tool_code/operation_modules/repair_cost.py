import pandas as pd
from scipy.optimize import curve_fit


class EmissionRepairCost:

    def __init__(self):
        self.repair_cpm_dict = dict()
        self.repair_cost_details = dict()
        self.repair_cpm_curve_coeffs = dict()

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

        # veh_id, option, my, age = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id

        direct_cost_scaler = pkg_cost / reference_pkg_cost

        in_warranty_cpm = in_warranty_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        at_usefullife_cpm = at_usefullife_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        max_cpm = max_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler

        typical_vmt = settings.fleet_cap.get_typical_vmt_per_year(settings, vehicle)
        # typical_vmt = settings.fleet_cap.calc_typical_vmt_per_year(settings, vehicle)

        # calculate estimated ages at which warranty and useful life will occur
        warranty_estimated_age, usefullife_estimated_age \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt)

        # calculate the slope of the cost per mile curve between warranty and useful life estimated ages
        if usefullife_estimated_age > warranty_estimated_age:
            slope_within_usefullife = (at_usefullife_cpm - in_warranty_cpm) \
                                      / (usefullife_estimated_age - warranty_estimated_age)
        else:
            slope_within_usefullife = 0

        # now calulate the cost per mile
        if (vehicle.age_id + 1) < warranty_estimated_age:
            cpm = in_warranty_cpm
        elif warranty_estimated_age <= (vehicle.age_id + 1) < usefullife_estimated_age:
            cpm = slope_within_usefullife * ((vehicle.age_id + 1) - warranty_estimated_age) + in_warranty_cpm
        elif (vehicle.age_id + 1) == usefullife_estimated_age:
            cpm = at_usefullife_cpm
        else:
            cpm = max_cpm

        self.repair_cpm_dict[vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id] = {
            'optionID': vehicle.option_id,
            'sourceTypeID': vehicle.sourcetype_id,
            'regClassID': vehicle.regclass_id,
            'fuelTypeID': vehicle.fueltype_id,
            'modelYearID': vehicle.modelyear_id,
            'ageID': vehicle.age_id,
            'optionName': vehicle.option_name,
            'sourceTypeName': vehicle.sourcetype_name,
            'regClassName': vehicle.regclass_name,
            'fuelTypeName': vehicle.fueltype_name,
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

    def calc_emission_repair_and_warranty_cost(self, settings, vehicle, pkg_cost, reference_pkg_cost):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.\n
            pkg_cost: numeric; the direct manufacturing cost of the passed vehicle.\n
            reference_pkg_cost: numeric; the direct manufacturing cost of the reference vehicle.

        Returns:
            Updates the data_object dictionary to include emission repair costs/mile.\n
            Updates the repair cost/mile dictionary (repair_cpm_dict) containing details used in the calculation of repair
            cost/mile; this dictionary is then written to an output file for the given run.

        """
        in_warranty_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('in-warranty_R&M_CPM')
        at_usefullife_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('at-usefullife_R&M_CPM')
        max_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('max_R&M_CPM')
        emission_repair_share_input_value = settings.repair_and_maintenance.get_attribute_value('emission_repair_share')

        direct_cost_scaler = pkg_cost / reference_pkg_cost

        in_warranty_cpm = in_warranty_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        at_usefullife_cpm = at_usefullife_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        max_cpm = max_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler

        new_tech_adj_factor = settings.warranty_new_tech_adj.get_attribute_value(vehicle)

        typical_vmt = settings.fleet_cap.get_typical_vmt_per_year(settings, vehicle)

        # NOTE: nap refers to "no action provisions"; ap refers to "action provisions"
        warranty_age_nap, ul_age_nap \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt,
                                                        warranty_provisions=settings.no_action_alt)

        warranty_age_ap, ul_age_ap \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt,
                                                        warranty_provisions=vehicle.option_id)

        # get the share with extended warranty in the no-action scenario
        share_with_extended = 0
        if vehicle.engine_id in settings.warranty_extended._dict:
            share_with_extended = settings.warranty_extended.get_share(vehicle.engine_id)

        # calculate the repair cost per mile slopes between warranty and useful life
        slope_nap = self.calc_slope(in_warranty_cpm, at_usefullife_cpm, warranty_age_nap, ul_age_nap)
        slope_ap = self.calc_slope(in_warranty_cpm, at_usefullife_cpm, warranty_age_ap, ul_age_ap)
        slope_mixed = self.calc_slope(in_warranty_cpm, at_usefullife_cpm, warranty_age_nap, ul_age_ap)

        # now calculate the cost per mile under the no_action provisions
        cpm_nap = self.calc_repair_cpm(vehicle.age_id, warranty_age_nap, ul_age_nap, slope_nap,
                                       in_warranty_cpm, at_usefullife_cpm, max_cpm)

        # now calculate the cost per mile under the action provisions
        cpm_ap = self.calc_repair_cpm(vehicle.age_id, warranty_age_ap, ul_age_ap, slope_ap,
                                      in_warranty_cpm, at_usefullife_cpm, max_cpm)

        # now calculate the cost per mile under the mixed provisions
        cpm_mixed = self.calc_repair_cpm(vehicle.age_id, warranty_age_nap, ul_age_ap, slope_mixed,
                                         in_warranty_cpm, at_usefullife_cpm, max_cpm)

        # now calc the cost per vehicle and cost for each condition
        cost_per_veh_nap = cpm_nap * vehicle.vmt_per_veh

        cost_per_veh_ap = cpm_ap * vehicle.vmt_per_veh
        cost_ap = cost_per_veh_ap * vehicle.vpop

        cost_per_veh_mixed = cpm_mixed * vehicle.vmt_per_veh

        # now determine whether costs are warranty or owner repair - estimated ages here are option_id provisions
        # determine if age_id=0 in which case warranty costs equal the base warranty costs and there are no repair costs
        if vehicle.age_id == 0:
            key = vehicle.engine_id
            in_warranty_cost_per_veh \
                = settings.warranty_base_costs.get_warranty_cost(key) * share_with_extended * (1 + new_tech_adj_factor)
            in_warranty_cost_per_veh += cost_per_veh_mixed * (1 - share_with_extended) * (1 + new_tech_adj_factor)
            in_warranty_cost = in_warranty_cost_per_veh * vehicle.vpop
            repair_cost_per_veh = 0
            repair_cost = 0
        elif 0 < vehicle.age_id + 1 <= warranty_age_ap:
            in_warranty_cost_per_veh = cost_per_veh_mixed * (1 - share_with_extended) * (1 + new_tech_adj_factor)
            in_warranty_cost = in_warranty_cost_per_veh * vehicle.vpop
            repair_cost_per_veh = 0  # in_warranty_cost_per_veh
            repair_cost = 0  # repair_cost_per_veh * vehicle.vpop
        else:
            in_warranty_cost_per_veh = 0
            in_warranty_cost = 0
            repair_cost_per_veh = cost_per_veh_ap
            repair_cost = cost_ap

        key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id
        self.repair_cost_details[key] = {
            'optionID': vehicle.option_id,
            'sourceTypeID': vehicle.sourcetype_id,
            'regClassID': vehicle.regclass_id,
            'fuelTypeID': vehicle.fueltype_id,
            'modelYearID': vehicle.modelyear_id,
            'ageID': vehicle.age_id,
            'optionName': vehicle.option_name,
            'sourceTypeName': vehicle.sourcetype_name,
            'regClassName': vehicle.regclass_name,
            'fuelTypeName': vehicle.fueltype_name,
            'vmt_per_veh': vehicle.vmt_per_veh,
            'vpop': vehicle.vpop,
            'reference_direct_cost': reference_pkg_cost,
            'direct_cost_scaler': direct_cost_scaler,
            'share_with_ext_warranty': share_with_extended,
            'warranty_est_age_nap': warranty_age_nap,
            'warranty_est_age_ap': warranty_age_ap,
            'ul_est_age_nap': ul_age_nap,
            'ul_est_age_ap': ul_age_ap,
            'in_warranty_cpm': in_warranty_cpm,
            'at_ul_cpm': at_usefullife_cpm,
            'slope_within_ul_nap': slope_nap,
            'slope_within_ul_ap': slope_ap,
            'slope_within_ul_mixed': slope_mixed,
            'max_cpm': max_cpm,
            'cpm_nap': cpm_nap,
            'cpm_mixed': cpm_mixed,
            'final_repair_cpm': cpm_ap,
            'in_warranty_repair_cost_per_veh': in_warranty_cost_per_veh,
            'beyond_warranty_repair_cost_per_veh': repair_cost_per_veh,
            'repair_cost_per_veh_nap': cost_per_veh_nap,
            'repair_cost_per_veh_mixed': cost_per_veh_mixed,
            'warranty_cost_per_veh': 0,
            'warranty_cost': 0,
            'repair_cost': repair_cost,
        }

        # Now sum the in_warranty_repair_costs as the warranty_cost at age_id=0.
        if vehicle.age_id == 0:
            self.repair_cost_details[key].update({
                'warranty_cost_per_veh': in_warranty_cost_per_veh,
                'warranty_cost': in_warranty_cost,
            })
        else:
            k = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0
            cost_per_veh = self.repair_cost_details[k]['warranty_cost_per_veh']
            cost = self.repair_cost_details[k]['warranty_cost']
            cost_per_veh += in_warranty_cost_per_veh
            cost += in_warranty_cost
            self.repair_cost_details[k].update({
                'warranty_cost_per_veh': cost_per_veh,
                'warranty_cost': cost,
            })

        return repair_cost_per_veh, repair_cost, cpm_ap

    @staticmethod
    def calc_slope(cpm_1, cpm_2, age_1, age_2):
        """

        Parameters:
            cpm_1: numeric; the cost/mile at age_1.
            cpm_2: numeric; the cost/mile at age_2.
            age_1: int; the age when cpm_1 is valid.
            age_2: int; the age when cpm_2 is valid.

        Returns:
            The slope of a cost/mile line at different ages.

        """
        if age_2 == age_1:
            m = 0
        else:
            m = (cpm_2 - cpm_1) / (age_2 - age_1)

        return m

    @staticmethod
    def calc_repair_cpm(veh_age, age_1, age_2, slope, cpm_1, cpm_2, max_cpm=None):
        """

        Parameters:
            veh_age: int; the vehicle age_id.
            age_1: int; the age when cpm_1 is valid (e.g., the estimated warranty age, or maybe age=0).
            age_2: int; the age when cpm_2 is valid (e.g., the estimated useful life age).
            slope: numeric; the slope of the repair cost per mile curve versus age.
            cpm_1: numeric; the cost/mile at age_1.
            cpm_2: numeric; the cost/mile at age_2.
            max_cpm: numeric; the max cost/mile if applicable.

        Returns:
            The cost per mile of repairs for the passed metrics.

        """
        if max_cpm:
            if (veh_age + 1) <= age_1:
                cpm = cpm_1
            elif age_1 < (veh_age + 1) < age_2:
                cpm = slope * ((veh_age + 1) - age_1) + cpm_1
            elif (veh_age + 1) == age_2:
                cpm = cpm_2
            else:
                cpm = max_cpm
        else:
            cpm = slope * ((veh_age + 1) - age_1) + cpm_1

        return cpm

    def calc_using_cost_per_year(self, settings, vehicle, pkg_cost, reference_pkg_cost):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.\n
            pkg_cost: numeric; the direct manufacturing cost of the passed vehicle.\n
            reference_pkg_cost: numeric; the direct manufacturing cost of the reference vehicle.

        Returns:
            Updates the data_object dictionary to include emission repair costs/mile.\n
            Updates the repair cost/mile dictionary (repair_cpm_dict) containing details used in the calculation of repair
            cost/mile; this dictionary is then written to an output file for the given run.

        """
        at_usefullife_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('at-usefullife_R&M_CPM')
        emission_repair_share_input_value = settings.repair_and_maintenance.get_attribute_value('emission_repair_share')

        direct_cost_scaler = pkg_cost / reference_pkg_cost

        # in_warranty_cpm = in_warranty_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        in_warranty_cpm = 0
        at_usefullife_cpm = at_usefullife_cpm_input_value * emission_repair_share_input_value * direct_cost_scaler
        max_cpm = None

        warranty_cost_per_year = settings.warranty_base_costs.get_warranty_cost(vehicle.engine_id)
        warranty_cost_per_year = warranty_cost_per_year * direct_cost_scaler

        new_tech_adj_factor = settings.warranty_new_tech_adj.get_attribute_value(vehicle)

        typical_vmt = settings.fleet_cap.get_typical_vmt_per_year(settings, vehicle)

        # NOTE: nap refers to "no action provisions"; ap refers to "action provisions"
        warranty_age_nap, warranty_miles_nap, ul_age_nap, ul_miles_nap, share_with_extended \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt,
                                                        warranty_provisions=settings.no_action_alt)

        warranty_age_ap, warranty_miles_ap, ul_age_ap, ul_miles_ap, share_with_extended \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt,
                                                        warranty_provisions=vehicle.option_id)

        # calculate the repair cost per mile slopes starting at age=warranty_age_nap
        slope_nap = self.calc_slope(in_warranty_cpm, at_usefullife_cpm, warranty_age_nap, ul_age_nap)
        slope_ap = self.calc_slope(in_warranty_cpm, at_usefullife_cpm, warranty_age_nap, ul_age_ap)

        # now calculate the cost per mile under the no_action provisions
        cpm_nap = max(self.calc_repair_cpm(vehicle.age_id, warranty_age_nap, ul_age_nap, slope_nap,
                                           in_warranty_cpm, at_usefullife_cpm, max_cpm=max_cpm), 0)

        # now calculate the cost per mile under the action provisions
        cpm_ap = max(self.calc_repair_cpm(vehicle.age_id, warranty_age_nap, ul_age_ap, slope_ap,
                                          in_warranty_cpm, at_usefullife_cpm, max_cpm=max_cpm), 0)

        # now calc the cost per vehicle and cost for each condition
        cost_per_veh_nap = cpm_nap * vehicle.vmt_per_veh

        cost_per_veh_ap = cpm_ap * vehicle.vmt_per_veh

        # now determine warranty and repair/operating cost
        if vehicle.age_id == 0 and vehicle.option_id == settings.no_action_alt:
            warranty_cost_per_veh = warranty_cost_per_year * warranty_age_ap
            repair_cost_per_veh = 0

        elif vehicle.age_id == 0 and vehicle.option_id != settings.no_action_alt:
            warranty_cost_per_veh = warranty_cost_per_year * warranty_age_ap * (1 + new_tech_adj_factor)
            repair_cost_per_veh = 0

        elif 0 < vehicle.age_id <= warranty_age_ap:
            warranty_cost_per_veh = 0
            repair_cost_per_veh = 0

        else:
            warranty_cost_per_veh = 0
            repair_cost_per_veh = cost_per_veh_ap

        warranty_cost = warranty_cost_per_veh * vehicle.vpop
        repair_cost = repair_cost_per_veh * vehicle.vpop

        key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id
        self.repair_cost_details[key] = {
            'optionID': vehicle.option_id,
            'sourceTypeID': vehicle.sourcetype_id,
            'regClassID': vehicle.regclass_id,
            'fuelTypeID': vehicle.fueltype_id,
            'modelYearID': vehicle.modelyear_id,
            'ageID': vehicle.age_id,
            'optionName': vehicle.option_name,
            'sourceTypeName': vehicle.sourcetype_name,
            'regClassName': vehicle.regclass_name,
            'fuelTypeName': vehicle.fueltype_name,
            'vmt_per_veh': vehicle.vmt_per_veh,
            'vpop': vehicle.vpop,
            'reference_direct_cost': reference_pkg_cost,
            'direct_cost_scaler': direct_cost_scaler,
            'share_with_ext_warranty': share_with_extended,
            'warranty_est_age_nap': warranty_age_nap,
            'warranty_est_age_ap': warranty_age_ap,
            'ul_est_age_nap': ul_age_nap,
            'ul_est_age_ap': ul_age_ap,
            'in_warranty_cpm': in_warranty_cpm,
            'at_ul_cpm': at_usefullife_cpm,
            'slope_within_ul_nap': slope_nap,
            'slope_within_ul_ap': slope_ap,
            # 'slope_within_ul_mixed': slope_mixed,
            'max_cpm': max_cpm,
            'cpm_nap': cpm_nap,
            'cpm_ap': cpm_ap,
            # 'cpm_mixed': cpm_mixed,
            'final_repair_cpm': cpm_ap,
            # 'in_warranty_repair_cost_per_veh': in_warranty_cost_per_veh,
            'beyond_warranty_repair_cost_per_veh': repair_cost_per_veh,
            'repair_cost_per_veh_nap': cost_per_veh_nap,
            # 'repair_cost_per_veh_mixed': cost_per_veh_mixed,
            'warranty_cost_per_veh': warranty_cost_per_veh,
            'warranty_cost': warranty_cost,
            'repair_cost': repair_cost,
        }

        return repair_cost_per_veh, repair_cost, cpm_ap

#     # @staticmethod
#     def calc_repair_cpm_curve(self, in_warranty_cpm, at_usefullife_cpm, warranty_units, ul_units, vehicle, provisions):
#
#         key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, provisions
#
#         x_series = pd.Series([0, warranty_units, ul_units])
#         y_series = pd.Series([0, in_warranty_cpm, at_usefullife_cpm])
#
#         coeffs, _ = curve_fit(curve_coefficients, x_series, y_series)
#         constant, x_term, x2_term = coeffs
#
#         self.repair_cpm_curve_coeffs[key] = {
#             'optionID': vehicle.option_id,
#             'sourceTypeID': vehicle.sourcetype_id,
#             'regClassID': vehicle.regclass_id,
#             'fuelTypeID': vehicle.fueltype_id,
#             'modelYearID': vehicle.modelyear_id,
#             'optionName': vehicle.option_name,
#             'sourceTypeName': vehicle.sourcetype_name,
#             'regClassName': vehicle.regclass_name,
#             'fuelTypeName': vehicle.fueltype_name,
#             'provisions': provisions,
#             'constant': constant,
#             'x_term': x_term,
#             'x2_term': x2_term,
#         }
#
#         return coeffs
#
#     def calc_cpm_from_curve(self, vehicle, provisions):
#
#         key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, provisions
#         constant = self.repair_cpm_curve_coeffs[key]['constant']
#         x_term = self.repair_cpm_curve_coeffs[key]['x_term']
#         x2_term = self.repair_cpm_curve_coeffs[key]['x2_term']
#         cpm = constant \
#               + x_term * vehicle.vmt_per_veh \
#               + x2_term * vehicle.vmt_per_veh ** 2
#
#         return cpm
#
#
# def curve_coefficients(x_data, const, a, b):
#     """
#
#     Second degree polynomial curve fit function.
#
#     :param x_data: Series of floats; the independent variable in the curve fit (e.g., odometer miles or age)
#     :param const: Float; the constant coefficient in the curve fit.
#     :param a: Float; the first degree coefficient in the curve fit.
#     :param b: Float; the second degree coefficient in the curve fit.
#     :return: const, a and b coefficient values based on the y-data passed via the function call.
#
#     """
#     return const + a * x_data + b * x_data ** 2
