import pandas as pd

from bca_tool_code.cap_modules.package_cost import calc_package_cost
from bca_tool_code.cap_modules.indirect_cost import calc_indirect_cost
from bca_tool_code.cap_modules.tech_cost import calc_tech_cost
from bca_tool_code.cap_modules.def_cost import calc_def_cost
from bca_tool_code.cap_modules.fuel_cost import calc_fuel_cost
from bca_tool_code.sum_by_vehicle import calc_sum_of_costs
from bca_tool_code.emission_cost import calc_criteria_emission_cost
from bca_tool_code.weighted_results import create_weighted_cost_dict
from bca_tool_code.discounting import discount_values


class CapCosts:

    def __init__(self):
        self.results = dict()
        self.attributes_to_sum = {
            'OperatingCost': ['DEFCost', 'FuelCost_Pretax', 'EmissionRepairCost'],
            'TechAndOperatingCost': ['TechCost', 'OperatingCost'],
            'OperatingCost_Owner_PerMile': ['DEFCost_PerMile', 'FuelCost_Retail_PerMile', 'EmissionRepairCost_PerMile'],
            'OperatingCost_Owner_PerVeh': ['DEFCost_PerVeh', 'FuelCost_Retail_PerVeh', 'EmissionRepairCost_PerVeh']
        }

    def calc_cap_costs(self, settings, set_paths):
        print('Calculating CAP costs...')

        discount_rate = 0

        # create a new attributes dictionary that can be included for each dictionary key
        new_attributes = self.create_new_attributes(settings)
        new_attributes_dict = dict()
        for new_attribute in new_attributes:
            new_attributes_dict.update({new_attribute: 0})

        # create keys and include physical data for each vehicle and attributes from the new attributes dictionary
        for veh in settings.fleet_cap.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)

            update_dict = {
                'yearID': veh.year_id,
                'modelYearID': veh.modelyear_id,
                'ageID': veh.age_id,
                'optionID': veh.option_id,
                'sourceTypeID': veh.sourcetype_id,
                'regClassID': veh.regclass_id,
                'fuelTypeID': veh.fueltype_id,
                'OptionName': veh.option_name,
                'sourceTypeName': veh.sourcetype_name,
                'regClassName': veh.regclass_name,
                'fuelTypeName': veh.fueltype_name,
                'DiscountRate': discount_rate,
                'THC_UStons': veh.thc_ustons,
                'CO_UStons': veh.co_ustons,
                'NOx_UStons': veh.nox_ustons,
                'PM25_exhaust_UStons': veh.pm25_exhaust_ustons,
                'PM25_brakewear_UStons': veh.pm25_brakewear_ustons,
                'PM25_tirewear_UStons': veh.pm25_tirewear_ustons,
                'PM25_UStons': veh.pm25_ustons,
                'VOC_UStons': veh.voc_ustons,
                'CO2_UStons': veh.co2_ustons,
                'Energy_KJ': veh.energy_kj,
                'VMT': veh.vmt,
                'VMT_PerVeh': veh.vmt_per_veh,
                'VMT_PerVeh_Cumulative': veh.vmt_per_veh_cumulative,
                'VPOP': veh.vpop,
                'Gallons': veh.gallons,
            }
            self.update_object_dict(key, update_dict)
            self.update_object_dict(key, new_attributes_dict)
        #
        # add_keys_for_discounting(settings.general_inputs, self.results)

        # calc tech costs for age_id = 0 vehicle objects
        for veh in settings.fleet_cap.vehicles_age0:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)

            pkg_cost_per_veh, pkg_cost = calc_package_cost(settings, veh)

            indirect_cost_dict = calc_indirect_cost(settings, veh, pkg_cost_per_veh)
            warranty_cost_per_veh = indirect_cost_dict['Warranty_cost_per_veh']
            rnd_cost_per_veh = indirect_cost_dict['RnD_cost_per_veh']
            other_cost_per_veh = indirect_cost_dict['Other_cost_per_veh']
            profit_cost_per_veh = indirect_cost_dict['Profit_cost_per_veh']
            indirect_cost_per_veh = indirect_cost_dict['ic_sum_per_veh']
            warranty_cost = indirect_cost_dict['Warranty_cost']
            rnd_cost = indirect_cost_dict['RnD_cost']
            other_cost = indirect_cost_dict['Other_cost']
            profit_cost = indirect_cost_dict['Profit_cost']
            indirect_cost = indirect_cost_dict['ic_sum']

            tech_cost_per_veh, tech_cost = calc_tech_cost(veh, pkg_cost_per_veh, indirect_cost_per_veh)
            
            # update object dict with tech costs, all of which are for age_id=0 only
            update_dict = {
                'DirectCost': pkg_cost,
                'WarrantyCost': warranty_cost,
                'RnDCost': rnd_cost,
                'OtherCost': other_cost,
                'ProfitCost': profit_cost,
                'IndirectCost': indirect_cost,
                'TechCost': tech_cost,
                'DirectCost_PerVeh': pkg_cost_per_veh,
                'WarrantyCost_PerVeh': warranty_cost_per_veh,
                'RnDCost_PerVeh': rnd_cost_per_veh,
                'OtherCost_PerVeh': other_cost_per_veh,
                'ProfitCost_PerVeh': profit_cost_per_veh,
                'IndirectCost_PerVeh': indirect_cost_per_veh,
                'TechCost_PerVeh': tech_cost_per_veh,
            }
            self.update_object_dict(key, update_dict)

        # calculate DEF cost for diesel fueled vehicles
        for veh in settings.fleet_cap.vehicles_ft2:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
            def_cost_per_veh, def_cost, def_cost_per_mile = calc_def_cost(settings, veh)
            update_dict = {
                'DEFCost': def_cost,
                'DEFCost_PerVeh': def_cost_per_veh,
                'DEFCost_PerMile': def_cost_per_mile,
            }
            self.update_object_dict(key, update_dict)

        # calculate fuel cost for all vehicles
        for veh in settings.fleet_cap.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
            fuel_cost_per_veh, retail_cost, pretax_cost, fuel_cost_per_mile = calc_fuel_cost(settings, veh)
            update_dict = {
                'FuelCost_Retail': retail_cost,
                'FuelCost_Pretax': pretax_cost,
                'FuelCost_Retail_PerVeh': fuel_cost_per_veh,
                'FuelCost_Retail_PerMile': fuel_cost_per_mile,
            }
            self.update_object_dict(key, update_dict)

        # calculate emission repair cost for all vehicles
        # Note: the reference_pkg_cost should be diesel regclass=47, no_action_alt.
        for veh in settings.fleet_cap.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
            pkg_cost_per_veh = self.results[veh.vehicle_id, veh.option_id, veh.modelyear_id, 0, 0]['DirectCost_PerVeh']
            reference_pkg_cost = self.results[(61, 47, 2), 0, veh.modelyear_id, 0, 0]['DirectCost_PerVeh']
            repair_cost_per_veh, repair_cost, repair_cost_per_mile \
                = settings.emission_repair_cost.calc_emission_repair_cost(settings, veh, pkg_cost_per_veh,
                                                                          reference_pkg_cost)
            update_dict = {
                'EmissionRepairCost': repair_cost,
                'EmissionRepairCost_PerVeh': repair_cost_per_veh,
                'EmissionRepairCost_PerMile': repair_cost_per_mile,
            }
            self.update_object_dict(key, update_dict)

        # sum attributes in the attributes_to_sum dictionary
        for veh in settings.fleet_cap.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
            for summed_attribute, sum_attributes in self.attributes_to_sum.items():
                summed_attribute_value = calc_sum_of_costs(key, self.results, *sum_attributes)
                update_dict = {summed_attribute: summed_attribute_value}
                self.update_object_dict(key, update_dict)

        # calc CAP pollution effects, if applicable
        if settings.calc_cap_pollution:
            for veh in settings.fleet_cap.vehicles:
                key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
                update_dict = calc_criteria_emission_cost(settings, veh)
                self.update_object_dict(key, update_dict)

        # calc some weighted cost per mile results
        arg = 'VMT_PerVeh'
        year_max = settings.cap_vehicle.year_max
        create_weighted_cost_dict(settings, self, year_max, settings.wtd_def_cpm_dict,
                                  arg_to_weight='DEFCost_PerMile', arg_to_weight_by=arg)
        create_weighted_cost_dict(settings, self, year_max, settings.wtd_repair_cpm_dict,
                                  arg_to_weight='EmissionRepairCost_PerMile', arg_to_weight_by=arg)
        create_weighted_cost_dict(settings, self, year_max, settings.wtd_cap_fuel_cpm_dict,
                                  arg_to_weight='FuelCost_Retail_PerMile', arg_to_weight_by=arg)

        # discount things
        add_keys_for_discounting(settings.general_inputs, self.results)
        discount_values(settings, self)

    # TODO calc deltas then GHG
        stop = 0
            # calc CAP pollution effects, if applicable
            # if settings.calc_cap_pollution:
            #     bca_tool_code.emission_costs.calc_criteria_emission_costs(settings, settings.fleet_cap)
            #
            # bca_tool_code.weighted_results.create_weighted_cost_dict(settings, settings.fleet_cap,
            #                                                          settings.wtd_def_cpm_dict,
            #                                                          'DEFCost_PerMile', 'VMT_PerVeh')
            # bca_tool_code.weighted_results.create_weighted_cost_dict(settings, settings.fleet_cap,
            #                                                          settings.wtd_repair_cpm_dict,
            #                                                          'EmissionRepairCost_PerMile', 'VMT_PerVeh')
            # bca_tool_code.weighted_results.create_weighted_cost_dict(settings, settings.fleet_cap,
            #                                                          settings.wtd_cap_fuel_cpm_dict,
            #                                                          'FuelCost_Retail_PerMile', 'VMT_PerVeh')
            #
            # bca_tool_code.discounting.discount_values(settings, settings.fleet_cap)
            #
            # # calc the annual summary, present values and annualized values (excluding cost/veh and cost/mile results)
            # settings.annual_summary_cap.annual_summary(settings, settings.fleet_cap, settings.options_cap)
            #
            # # calc deltas relative to the no-action scenario
            # bca_tool_code.calc_deltas.calc_deltas(settings, settings.fleet_cap)
            # bca_tool_code.calc_deltas.calc_deltas(settings, settings.annual_summary_cap)
            #
            # settings.wtd_def_cpm_dict \
            #     = bca_tool_code.calc_deltas.calc_deltas_weighted(settings, settings.wtd_def_cpm_dict)
            # settings.wtd_repair_cpm_dict \
            #     = bca_tool_code.calc_deltas.calc_deltas_weighted(settings, settings.wtd_repair_cpm_dict)
            # settings.wtd_cap_fuel_cpm_dict \
            #     = bca_tool_code.calc_deltas.calc_deltas_weighted(settings, settings.wtd_cap_fuel_cpm_dict)

    def update_object_dict(self, key, update_dict):
        """

        Parameters:
            key: tuple; ((vehicle_id), option_id, modelyear_id, age_id, discount_rate).\n
            update_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        """
        if key in self.results:
            for attribute_name, attribute_value in update_dict.items():
                self.results[key][attribute_name] = attribute_value

        else:
            self.results.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self.results[key].update({attribute_name: attribute_value})

    def get_attribute_values(self, key, *attribute_names):
        """

        Parameters:
            key: tuple; ((sourcetype_id, regclass_id, fueltype_id), option_id, model_year, age_id, discount_rate).\n
            attribute_names: str(s); the attribute names for which values are sought.

        Returns:
            A list of attribute values associated with attribute_names for the given key.

        """
        attribute_values = list()
        for attribute_name in attribute_names:
            attribute_values.append(self.results[key][attribute_name])

        return attribute_values

    @staticmethod
    def create_new_attributes(settings):
        """

        Parameters:
            settings: object; the SetInputs class object.

        Returns:
            A list of new attributes to be added to the data_object dictionary.

        """
        new_attributes = ['DirectCost',
                          'WarrantyCost',
                          'RnDCost',
                          'OtherCost',
                          'ProfitCost',
                          'IndirectCost',
                          'TechCost',
                          'DEF_Gallons',
                          'DEFCost',
                          'GallonsCaptured_byORVR',
                          'FuelCost_Retail',
                          'FuelCost_Pretax',
                          'EmissionRepairCost',
                          'OperatingCost',
                          'TechAndOperatingCost',
                          'DirectCost_PerVeh',
                          'WarrantyCost_PerVeh',
                          'RnDCost_PerVeh',
                          'OtherCost_PerVeh',
                          'ProfitCost_PerVeh',
                          'IndirectCost_PerVeh',
                          'TechCost_PerVeh',
                          'DEFCost_PerMile',
                          'DEFCost_PerVeh',
                          'FuelCost_Retail_PerMile',
                          'FuelCost_Retail_PerVeh',
                          'EmissionRepairCost_PerMile',
                          'EmissionRepairCost_PerVeh',
                          'OperatingCost_Owner_PerMile',
                          'OperatingCost_Owner_PerVeh',
                          ]

        if settings.calc_cap_pollution:
            cap_attributes = ['PM25Cost_tailpipe_0.03', 'NOxCost_tailpipe_0.03',
                              'PM25Cost_tailpipe_0.07', 'NOxCost_tailpipe_0.07',
                              'CriteriaCost_tailpipe_0.03', 'CriteriaCost_tailpipe_0.07',
                              ]
            new_attributes = new_attributes + cap_attributes

        return new_attributes


def add_keys_for_discounting(general_inputs, input_dict):
    """

    Parameters:
        general_inputs: object; the GeneralInputs class object.\n
        input_dict: Dictionary; into which new keys will be added that provide room for discounting data.

    Returns:
        The passed dictionary with new keys added.

    """
    rates = [general_inputs.get_attribute_value('social_discount_rate_1'),
             general_inputs.get_attribute_value('social_discount_rate_2')]
    rates = [pd.to_numeric(rate) for rate in rates]
    for rate in rates:
        update_dict = dict()
        for key in input_dict:
            vehicle_id, option_id, modelyear_id, age_id, discount_rate = key
            update_dict[vehicle_id, option_id, modelyear_id, age_id, rate] = input_dict[key].copy()
            update_dict[vehicle_id, option_id, modelyear_id, age_id, rate]['DiscountRate'] = rate
        input_dict.update(update_dict)
