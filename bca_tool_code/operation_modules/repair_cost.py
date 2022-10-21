

class EmissionRepairCost:

    def __init__(self):
        self.repair_cost_details = dict()

    def calc_repair_cost(self, settings, vehicle):
        """

        Args:
            settings: object; an object of the SetInputs class.
            vehicle: object; an object of the Vehicle class.

        Returns:
            Repair and maintenance cost per vehicle, total cost, cost per mile and cost per hour; also updates the
            object dictionary for inclusion with the run results.

        """
        dollars_per_mile = dollars_per_hour = 0

        vehicle_id, engine_id, option_id, modelyear_id \
            = vehicle.vehicle_id, \
              vehicle.engine_id,\
              vehicle.option_id, \
              vehicle.modelyear_id

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

        # scale HHD inputs to other engine sizes
        in_ul_scaler = base_pkg_cost / reference_pkg_cost

        # scale repair costs beyond UL based on new tech vs existing tech
        beyond_ul_scaler = pkg_cost / base_pkg_cost

        # get repair cost calculation attribute
        calc_basis = settings.repair_calc_attr.get_attribute_value(vehicle.sourcetype_id)

        # get inputs from repair_calc_attributes
        emission_repair_share \
            = settings.repair_and_maintenance.get_attribute_value(('emission_repair_share',
                                                                   'share_of_total_repair_and_maintenance'))

        if 'mile' in calc_basis:
            dollars_per_mile \
                = settings.repair_and_maintenance.get_attribute_value(('repair_and_maintenance', 'dollars_per_mile')) \
                  * in_ul_scaler * emission_repair_share
        else:
            dollars_per_hour \
                = settings.repair_and_maintenance.get_attribute_value(('repair_and_maintenance', 'dollars_per_hour')) \
                  * in_ul_scaler * emission_repair_share

        # age estimated warranty and useful life ages
        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'Warranty'
        warranty_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        estimated_ages_dict_key = vehicle_id, option_id, modelyear_id, 'UsefulLife'
        ul_age \
            = settings.estimated_age.get_attribute_value(estimated_ages_dict_key, 'estimated_age')

        avg_speed = settings.average_speed.get_attribute_value(vehicle.sourcetype_id)
        operating_hours = vehicle.vmt_per_veh / avg_speed

        if dollars_per_mile:
            r_and_m_per_veh = dollars_per_mile * vehicle.vmt_per_veh
        else:
            r_and_m_per_veh = dollars_per_hour * operating_hours

        if vehicle.age_id < warranty_age < vehicle.age_id + 1:
            # plus 1 here because MOVES uses age_id=0 for first year but EstimatedAge does not
            portion_beyond_warranty = vehicle.age_id + 1 - warranty_age
            r_and_m_cost_per_veh = r_and_m_per_veh * portion_beyond_warranty

        elif vehicle.age_id + 1 <= warranty_age:
            # plus 1 here because MOVES uses age_id=0 for first year but EstimatedAge does not
            r_and_m_cost_per_veh = 0

        elif vehicle.age_id < ul_age < vehicle.age_id + 1:
            portion_at_lower_cost = ul_age - vehicle.age_id
            portion_at_higher_cost = vehicle.age_id + 1 - ul_age

            r_and_m_cost_per_veh \
                = r_and_m_per_veh * portion_at_lower_cost \
                  + r_and_m_per_veh * beyond_ul_scaler * portion_at_higher_cost

        elif vehicle.age_id + 1 <= ul_age:
            r_and_m_cost_per_veh = r_and_m_per_veh

        else:
            r_and_m_cost_per_veh = r_and_m_per_veh * beyond_ul_scaler

        r_and_m_cost = r_and_m_cost_per_veh * vehicle.vpop
        cpm = r_and_m_cost_per_veh / vehicle.vmt_per_veh
        cph = r_and_m_cost_per_veh / operating_hours

        # get warranty cost for inclusion in repair cost dictionary
        warranty_cost_per_veh = 0
        if vehicle.age_id == 0:
            contribution_factors_dict_key = vehicle_id, engine_id, option_id, modelyear_id
            warranty_cost_per_veh \
                = settings.markups.get_contribution_factors_data(contribution_factors_dict_key, 'WarrantyCost_PerVeh')

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
            'in_ul_scaler': in_ul_scaler,
            'beyond_ul_scaler': beyond_ul_scaler,
            'estimated_warranty_age': warranty_age,
            'estimated_ul_age': ul_age,
            'emission_repair_dollars_per_mile': cpm,
            'emission_repair_dollars_per_hour': cph,
            'emission_repair_dollars_per_veh': r_and_m_cost_per_veh,
            'warranty_cost_per_veh': warranty_cost_per_veh,
            'emission_repair_cost_dollars': r_and_m_cost,
        }

        return r_and_m_cost_per_veh, r_and_m_cost, cpm, cph
