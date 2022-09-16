import pandas as pd
from scipy.optimize import curve_fit
from math import ceil, floor


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

        typical_vmt = settings.fleet.get_typical_vmt_per_year(settings, vehicle)
        # typical_vmt = settings.fleet.calc_typical_vmt_per_year(settings, vehicle)

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

        typical_vmt = settings.fleet.get_typical_vmt_per_year(settings, vehicle)

        # NOTE: nap refers to "no action provisions"; ap refers to "action provisions"
        warranty_age_nap, ul_age_nap \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt,
                                                        provisions=settings.no_action_alt)

        warranty_age_ap, ul_age_ap \
            = settings.estimated_age.calc_estimated_age(settings, vehicle, typical_vmt,
                                                        provisions=vehicle.option_id)

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
    def calc_repair_cpm(veh_age, age_1, slope, cpm_1, max_cpm=None):
        """

        Parameters:
            veh_age: int; the vehicle age_id.
            age_1: int; the age when cpm_1 is valid (e.g., the estimated warranty age, or maybe age=0).
            slope: numeric; the slope of the repair cost per mile curve versus age.
            cpm_1: numeric; the cost/mile at age_1.
            max_cpm: numeric; the max cost/mile if applicable.

        Returns:
            The cost per mile of repairs for the passed metrics.

        """
        if max_cpm:
            cpm = max(min(slope * ((veh_age + 1) - age_1) + cpm_1, max_cpm), 0)
        else:
            cpm = max(slope * ((veh_age + 1) - age_1) + cpm_1, 0)

        return cpm

    def calc_using_cost_per_year(self, settings, vehicle):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.

        Returns:
            Updates the data_object dictionary to include emission repair costs/mile.\n
            Updates the repair cost/mile dictionary (repair_cpm_dict) containing details used in the calculation of repair
            cost/mile; this dictionary is then written to an output file for the given run.

        """
        at_usefullife_cpm_input_value = settings.repair_and_maintenance.get_attribute_value('at-usefullife_R&M_CPM')
        emission_repair_share_input_value = settings.repair_and_maintenance.get_attribute_value('emission_repair_share')

        vehicle_id, option_id, modelyear_id = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
        cost_key = vehicle_id, option_id, modelyear_id, 0, 0

        pkg_cost = settings.cost_calcs.get_attribute_value(cost_key, 'DirectCost_PerVeh')

        # Note: the reference_pkg_cost should be diesel regclass=47, no_action_alt and the same model year as vehicle.
        reference_pkg_cost \
            = settings.cost_calcs.get_attribute_value(((61, 47, 2), 0, modelyear_id, 0, 0), 'DirectCost_PerVeh')

        direct_cost_scaler = pkg_cost / reference_pkg_cost

        in_warranty_cpm = 0
        at_usefullife_cpm = at_usefullife_cpm_input_value \
                            * emission_repair_share_input_value * direct_cost_scaler

        # determine whether to use max_cpm or not (setting in general inputs file)
        use_max_cpm = settings.general_inputs.get_attribute_value('use_max_R&M_cost_per_mile')
        if use_max_cpm != 'Y':
            max_cpm = None
        else:
            max_cpm = settings.repair_and_maintenance.get_attribute_value('max_R&M_CPM') \
                      * emission_repair_share_input_value * direct_cost_scaler

        # age estimated warranty and useful life ages
        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'Warranty'
        warranty_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'UsefulLife'
        ul_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        # calc the repair cost per mile curve slope
        slope = self.calc_slope(in_warranty_cpm, at_usefullife_cpm, warranty_age, ul_age)

        # calc the emission-repair cost per mile
        cpm = self.calc_repair_cpm(vehicle.age_id, warranty_age, slope, in_warranty_cpm, max_cpm=max_cpm)

        cost_per_veh = cpm * vehicle.vmt_per_veh

        if 0 < vehicle.age_id <= warranty_age:
            repair_cost_per_veh = 0
            cpm = 0

        else:
            repair_cost_per_veh = cost_per_veh

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
            'warranty_est_age': warranty_age,
            'ul_est_age': ul_age,
            'in_warranty_cpm': in_warranty_cpm,
            'at_ul_cpm': at_usefullife_cpm,
            'slope_within_ul': slope,
            'max_cpm': max_cpm,
            'repair_cpm': cpm,
            'repair_cost_per_veh': repair_cost_per_veh,
            'repair_cost': repair_cost,
        }

        return repair_cost_per_veh, repair_cost, cpm

    def calc_repair_cost(self, settings, vehicle):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.

        Returns:
            Updates the data_object dictionary to include emission repair costs/mile.\n
            Updates the repair cost/mile dictionary (repair_cpm_dict) containing details used in the calculation of repair
            cost/mile; this dictionary is then written to an output file for the given run.

        """
        dollars_per_mile_1 = dollars_per_mile_2 = max_dollars_per_mile = slope = avg_speed = operating_hours = None
        dollars_per_mile = dollars_per_hour = 0

        vehicle_id, option_id, modelyear_id = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
        cost_key = vehicle_id, option_id, modelyear_id, 0, 0

        pkg_cost = settings.cost_calcs.get_attribute_value(cost_key, 'DirectCost_PerVeh')
        base_pkg_cost \
            = settings.cost_calcs.get_attribute_value((vehicle_id, settings.no_action_alt, modelyear_id, 0, 0),
                                                      'DirectCost_PerVeh')

        # calc an emission repair cost scaler to adjust the HHD inputs to LHD and MHD
        # Note: the reference_pkg_cost should be diesel regclass=47, no_action_alt and the same model year as vehicle.
        reference_pkg_cost \
            = settings.cost_calcs.get_attribute_value(((61, 47, 2), 0, modelyear_id, 0, 0), 'DirectCost_PerVeh')

        # repair_cost_scaler = base_pkg_cost / reference_pkg_cost
        # beyond_ul_cost_scaler = pkg_cost / base_pkg_cost
        repair_cost_scaler = pkg_cost / reference_pkg_cost
        beyond_ul_cost_scaler = pkg_cost / reference_pkg_cost

        # get repair cost calculation attribute
        calc_basis = settings.repair_calc_attr.get_attribute_value(vehicle.sourcetype_id)

        # get inputs from repair_calc_attributes
        emission_repair_share \
            = settings.repair_and_maintenance.get_attribute_value(('emission_repair_share',
                                                                   'share_of_total_repair_and_maintenance'))
        if 'mile' in calc_basis:
            dollars_per_mile_1 \
                = settings.repair_and_maintenance.get_attribute_value(('independent_variable_1', 'dollars_per_mile')) \
                  * repair_cost_scaler * emission_repair_share

            dollars_per_mile_2 \
                = settings.repair_and_maintenance.get_attribute_value(('independent_variable_2', 'dollars_per_mile')) \
                  * repair_cost_scaler * emission_repair_share

            use_max_cpm = settings.general_inputs.get_attribute_value('use_max_R&M_cost_per_mile')
            if use_max_cpm == 'Y':
                max_dollars_per_mile \
                    = settings.repair_and_maintenance.get_attribute_value(('max', 'dollars_per_mile')) \
                      * repair_cost_scaler * emission_repair_share
        else:
            dollars_per_hour \
                = settings.repair_and_maintenance.get_attribute_value(('max', 'dollars_per_hour')) \
                  * repair_cost_scaler * emission_repair_share

        # age estimated warranty and useful life ages
        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'Warranty'
        warranty_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'UsefulLife'
        ul_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        avg_speed = settings.average_speed.get_attribute_value(vehicle.sourcetype_id)
        operating_hours = vehicle.vmt_per_veh / avg_speed

        # calc the repair cost per mile curve slope, if needed
        if dollars_per_mile_2:
            slope = self.calc_slope(dollars_per_mile_1, dollars_per_mile_2, warranty_age, ul_age)

            # calc the emission-repair cost per mile
            dollars_per_mile \
                = self.calc_repair_cpm(vehicle.age_id, warranty_age, slope, dollars_per_mile_1,
                                       max_cpm=max_dollars_per_mile)

            cost_per_veh = dollars_per_mile * vehicle.vmt_per_veh

        else:
            cost_per_veh = dollars_per_hour * operating_hours

        oem_warranty_liability_per_veh = 0
        cumulative_value = 0
        if vehicle.age_id < warranty_age < vehicle.age_id + 1:
            # this calcs the portion not covered during the year in-which warranty is reached
            # plus 1 here because MOVES uses age_id=0 for first year but EstimatedAge does not
            fraction_under_warranty = warranty_age - floor(warranty_age)
            fraction = ceil(warranty_age) - warranty_age
            oem_warranty_liability_per_veh = cost_per_veh * fraction_under_warranty
            r_and_m_cost_per_veh = cost_per_veh * fraction

        elif vehicle.age_id + 1 <= warranty_age:
            # plus 1 here because MOVES uses age_id=0 for first year but EstimatedAge does not
            oem_warranty_liability_per_veh = cost_per_veh
            r_and_m_cost_per_veh = 0

        elif vehicle.age_id + 1 < ul_age < vehicle.age_id + 1:
            fraction_at_lower_cost = ul_age - floor(ul_age)
            fraction_at_higher_cost = ceil(ul_age) - ul_age

            r_and_m_cost_per_veh \
                = cost_per_veh * (fraction_at_lower_cost + fraction_at_higher_cost * beyond_ul_cost_scaler)

        else:
            r_and_m_cost_per_veh = cost_per_veh * beyond_ul_cost_scaler

        if (vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0) in self.repair_cost_details:
            cumulative_value \
                = self.repair_cost_details[vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0]['cumulative_oem_warranty_liability_per_veh']

        cumulative_oem_warranty_liability_per_veh = oem_warranty_liability_per_veh + cumulative_value
        # oem_warranty_liability_cost = oem_warranty_liability_per_veh * vehicle.vpop
        r_and_m_cost = r_and_m_cost_per_veh * vehicle.vpop
        cpm = r_and_m_cost_per_veh / vehicle.vmt_per_veh
        cph = r_and_m_cost_per_veh / operating_hours

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
            'avg_speed': avg_speed,
            'hours_per_veh': operating_hours,
            'vpop': vehicle.vpop,
            'reference_pkg_direct_cost': reference_pkg_cost,
            'base_pkg_direct_cost': base_pkg_cost,
            'pkg_direct_cost': pkg_cost,
            'emission_repair_cost_scaler': repair_cost_scaler,
            'beyond_ul_cost_scaler': beyond_ul_cost_scaler,
            'warranty_est_age': warranty_age,
            'ul_est_age': ul_age,
            'at_ul_cpm': dollars_per_mile_2,
            'slope_within_ul': slope,
            'max_cpm': max_dollars_per_mile,
            'emission_repair_cpm': cpm,
            'emission_repair_cph': cph,
            'emission_repair_cost_per_veh': r_and_m_cost_per_veh,
            'emission_repair_cost': r_and_m_cost,
            'oem_warranty_liability_cost_per_veh': oem_warranty_liability_per_veh,
            'cumulative_oem_warranty_liability_per_veh': 0,
            # 'r_and_m_cpm': cpm,
            # 'r_and_m_cph': cph,
            # 'r_and_m_cost_per_veh': r_and_m_cost_per_veh,
            # 'r_and_m_cost': r_and_m_cost,
        }

        # have to be sure to get full upfront warranty liability when there's not enough years of data
        year_max = settings.vehicle.year_id_max
        if vehicle.modelyear_id + warranty_age > year_max:
            modelyear_id = year_max - ceil(warranty_age)
            needed_key = vehicle.vehicle_id, vehicle.option_id, modelyear_id, 0
            cumulative_oem_warranty_liability_per_veh \
                = self.repair_cost_details[needed_key]['cumulative_oem_warranty_liability_per_veh']

        update_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0
        self.repair_cost_details[update_key].update({
            'cumulative_oem_warranty_liability_per_veh': cumulative_oem_warranty_liability_per_veh
        })
        return r_and_m_cost_per_veh, r_and_m_cost, cpm, cph

    def transfer_at_cost_per_year(self, settings, vehicle):
        """

        Args:
            settings:
            vehicle:

        Returns:

        """
        dollars_per_mile = dollars_per_hour = 0

        vehicle_id, option_id, modelyear_id = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id
        cost_key = vehicle_id, option_id, modelyear_id, 0, 0

        pkg_cost = settings.cost_calcs.get_attribute_value(cost_key, 'DirectCost_PerVeh')
        base_pkg_cost \
            = settings.cost_calcs.get_attribute_value((vehicle_id, settings.no_action_alt, modelyear_id, 0, 0),
                                                      'DirectCost_PerVeh')

        # calc an emission repair cost scaler to adjust the HHD inputs to LHD and MHD
        # Note: the reference_pkg_cost should be diesel regclass=47, no_action_alt and the same model year as vehicle.
        reference_pkg_cost \
            = settings.cost_calcs.get_attribute_value(((61, 47, 2), settings.no_action_alt, modelyear_id, 0, 0),
                                                      'DirectCost_PerVeh')

        base_warranty_scaler = base_pkg_cost / reference_pkg_cost # scales HHD inputs to other engine sizes
        beyond_warranty_scaler = pkg_cost / reference_pkg_cost # scales emission repair for additional tech
        beyond_ul_scaler = pkg_cost / base_pkg_cost

        # get repair cost calculation attribute
        # calc_basis = settings.repair_calc_attr.get_attribute_value(vehicle.sourcetype_id)
        #
        # # get inputs from repair_calc_attributes
        # emission_repair_share \
        #     = settings.repair_and_maintenance.get_attribute_value(('emission_repair_share',
        #                                                            'share_of_total_repair_and_maintenance'))

        warranty_per_year = settings.warranty_base_costs.get_warranty_cost(vehicle.engine_id)
        warranty_per_year = warranty_per_year * base_warranty_scaler

        # age estimated warranty and useful life ages
        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'Warranty'
        warranty_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'UsefulLife'
        ul_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        avg_speed = settings.average_speed.get_attribute_value(vehicle.sourcetype_id)
        operating_hours = vehicle.vmt_per_veh / avg_speed

        oem_warranty_liability_per_veh = 0
        cumulative_value = 0
        if vehicle.age_id < warranty_age < vehicle.age_id + 1:
            # this calcs the portion not covered during the year in-which warranty is reached
            # plus 1 here because MOVES uses age_id=0 for first year but EstimatedAge does not
            portion_under_warranty = warranty_age - floor(warranty_age)
            portion_beyond_warranty = ceil(warranty_age) - warranty_age
            oem_warranty_liability_per_veh = warranty_per_year * portion_under_warranty
            r_and_m_cost_per_veh = warranty_per_year * beyond_warranty_scaler * portion_beyond_warranty

        elif vehicle.age_id + 1 <= warranty_age:
            # plus 1 here because MOVES uses age_id=0 for first year but EstimatedAge does not
            oem_warranty_liability_per_veh = warranty_per_year
            r_and_m_cost_per_veh = 0

        elif vehicle.age_id + 1 < ul_age < vehicle.age_id + 1:
            portion_at_lower_cost = ul_age - floor(ul_age)
            portion_at_higher_cost = ceil(ul_age) - ul_age

            r_and_m_cost_per_veh \
                = warranty_per_year * beyond_warranty_scaler \
                  * (portion_at_lower_cost + portion_at_higher_cost * beyond_ul_scaler)

        else:
            r_and_m_cost_per_veh = warranty_per_year * beyond_ul_scaler

        if (vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0) in self.repair_cost_details:
            cumulative_value \
                = self.repair_cost_details[vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0]['cumulative_oem_warranty_liability_per_veh']

        cumulative_oem_warranty_liability_per_veh = oem_warranty_liability_per_veh + cumulative_value
        r_and_m_cost = r_and_m_cost_per_veh * vehicle.vpop
        cpm = r_and_m_cost_per_veh / vehicle.vmt_per_veh
        cph = r_and_m_cost_per_veh / operating_hours

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
            'avg_speed': avg_speed,
            'hours_per_veh': operating_hours,
            'vpop': vehicle.vpop,
            'reference_pkg_direct_cost': reference_pkg_cost,
            'base_pkg_direct_cost': base_pkg_cost,
            'pkg_direct_cost': pkg_cost,
            'base_warranty_scaler': base_warranty_scaler,
            'beyond_warranty_scaler': beyond_warranty_scaler,
            'beyond_ul_scaler': beyond_ul_scaler,
            'warranty_est_age': warranty_age,
            'ul_est_age': ul_age,
            'emission_repair_dollars_per_mile': cpm,
            'emission_repair_dollars_per_hour': cph,
            'emission_repair_dollars_per_veh': r_and_m_cost_per_veh,
            'oem_warranty_liability_dollars_per_veh': oem_warranty_liability_per_veh,
            'cumulative_oem_warranty_liability_per_veh': 0,
            'emission_repair_dollar_cost': r_and_m_cost,
        }

        # have to be sure to get full upfront warranty liability when there's not enough years of data
        year_max = settings.vehicle.year_id_max
        if vehicle.modelyear_id + warranty_age > year_max:
            modelyear_id = year_max - ceil(warranty_age)
            needed_key = vehicle.vehicle_id, vehicle.option_id, modelyear_id, 0
            cumulative_oem_warranty_liability_per_veh \
                = self.repair_cost_details[needed_key]['cumulative_oem_warranty_liability_per_veh']

        update_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 0
        self.repair_cost_details[update_key].update({
            'cumulative_oem_warranty_liability_per_veh': cumulative_oem_warranty_liability_per_veh
        })

        return r_and_m_cost_per_veh, r_and_m_cost, cpm, cph
