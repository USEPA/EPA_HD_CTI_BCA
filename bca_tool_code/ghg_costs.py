import pandas as pd

from bca_tool_code.vehicle_cost_modules.package_cost import calc_package_cost
from bca_tool_code.operation_modules.fuel_cost import calc_fuel_cost
from bca_tool_code.general_modules.sum_by_vehicle import calc_sum_of_costs
from bca_tool_code.general_modules.weighted_results import create_weighted_cost_dict
from bca_tool_code.general_modules.discounting import discount_values
from bca_tool_code.general_modules.calc_deltas import calc_deltas, calc_deltas_weighted


class GhgCosts:

    def __init__(self):
        self.results = dict()
        self.attributes_to_sum = {
            'OperatingCost': ['FuelCost_Pretax'],
            'TechAndOperatingCost': ['TechCost', 'OperatingCost'],
            'OperatingCost_Owner_PerMile': ['FuelCost_Retail_PerMile'],
            'OperatingCost_Owner_PerVeh': ['FuelCost_Retail_PerVeh']
        }

    def calc_ghg_costs(self, settings):
        print('\nCalculating GHG costs...')

        discount_rate = 0

        # create a new attributes dictionary that can be included for each dictionary key
        new_attributes = self.create_new_attributes(settings)
        new_attributes_dict = dict()
        for new_attribute in new_attributes:
            new_attributes_dict.update({new_attribute: 0})

        # create keys and include physical data for each vehicle and attributes from the new attributes dictionary
        for veh in settings.fleet_ghg.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)

            update_dict = {
                'yearID': veh.year_id,
                'modelYearID': veh.modelyear_id,
                'ageID': veh.age_id,
                'optionID': veh.option_id,
                'sourceTypeID': veh.sourcetype_id,
                'regClassID': veh.regclass_id,
                'fuelTypeID': veh.fueltype_id,
                'optionName': veh.option_name,
                'sourceTypeName': veh.sourcetype_name,
                'regClassName': veh.regclass_name,
                'fuelTypeName': veh.fueltype_name,
                'DiscountRate': discount_rate,
                'THC_UStons': veh.thc_ustons,
                'CH4_UStons': veh.ch4_ustons,
                'N2O_UStons': veh.n2o_ustons,
                'SO2_UStons': veh.so2_ustons,
                'CO2_UStons': veh.co2_ustons,
                'Energy_KJ': veh.energy_kj,
                'VMT': veh.vmt,
                'VMT_PerVeh': veh.vmt_per_veh,
                'Odometer': veh.odometer,
                'VPOP': veh.vpop,
                'Gallons': veh.gallons,
            }
            self.update_object_dict(key, update_dict)
            self.update_object_dict(key, new_attributes_dict)

        # calc tech costs for age_id=0 vehicle objects
        for veh in settings.fleet_ghg.vehicles_age0:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)

            tech_cost_per_veh, tech_cost, pkg_cost_per_veh = calc_package_cost(settings, veh)
            update_dict = {
                'PackageCost_PerVeh': pkg_cost_per_veh,
                'TechCost_PerVeh': tech_cost_per_veh,
                'TechCost': tech_cost,
            }
            self.update_object_dict(key, update_dict)

        # calculate fuel cost for all vehicles
        for veh in settings.fleet_ghg.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
            fuel_cost_per_veh, retail_cost, pretax_cost, fuel_cost_per_mile, captured_gallons \
                = calc_fuel_cost(settings, veh, thc_reduction=None)
            update_dict = {
                'FuelCost_Retail_PerVeh': fuel_cost_per_veh,
                'FuelCost_Retail_PerMile': fuel_cost_per_mile,
                'FuelCost_Retail': retail_cost,
                'FuelCost_Pretax': pretax_cost,
            }
            self.update_object_dict(key, update_dict)

        # sum attributes in the attributes_to_sum dictionary
        for veh in settings.fleet_ghg.vehicles:
            key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
            for summed_attribute, sum_attributes in self.attributes_to_sum.items():
                summed_attribute_value = calc_sum_of_costs(key, self.results, *sum_attributes)
                update_dict = {summed_attribute: summed_attribute_value}
                self.update_object_dict(key, update_dict)

        # calc GHG pollution effects, if applicable
        if settings.calc_ghg_pollution:
            for veh in settings.fleet_ghg.vehicles:
                key = (veh.vehicle_id, veh.option_id, veh.modelyear_id, veh.age_id, discount_rate)
                # update_dict = calc_ghg_emission_cost(settings, veh)
                # self.update_object_dict(key, update_dict)

        # calc some weighted cost per mile results
        arg = 'VMT_PerVeh'
        year_max = settings.ghg_vehicle.year_id_max
        create_weighted_cost_dict(settings, self, year_max, settings.wtd_ghg_fuel_cpm_dict,
                                  arg_to_weight='FuelCost_Retail_PerMile', arg_to_weight_by=arg)

        # discount things
        add_keys_for_discounting(settings.general_inputs, self.results)
        discount_values(settings, self)

        # calc the annual summary, present values and annualized values (excluding cost/veh and cost/mile results)
        settings.annual_summary_ghg.annual_summary(settings, self, settings.options_ghg, settings.ghg_vehicle.year_ids)

        # calc deltas relative to the no-action scenario
        calc_deltas(settings, self, settings.options_ghg)
        calc_deltas(settings, settings.annual_summary_ghg, settings.options_ghg)

        settings.wtd_ghg_fuel_cpm_dict = calc_deltas_weighted(settings, settings.wtd_ghg_fuel_cpm_dict,
                                                              settings.options_ghg)

    def update_object_dict(self, key, update_dict):
        """

        Parameters:
            key: tuple; (vehicle_id, option_id, modelyear_id, age_id, discount_rate).\n
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
        new_attributes = [
            'PackageCost_PerVeh',
            'TechCost_PerVeh',
            'FuelCost_Retail_PerMile',
            'FuelCost_Retail_PerVeh',
            'OperatingCost_Owner_PerMile',
            'OperatingCost_Owner_PerVeh',
            'TechCost',
            'FuelCost_Retail',
            'FuelCost_Pretax',
            'OperatingCost',
            'TechAndOperatingCost',
        ]
        if settings.calc_ghg_pollution:
            ghg_attributes = [
                'CO2Cost_tailpipe_0.05',
                'CO2Cost_tailpipe_0.03',
                'CO2Cost_tailpipe_0.025',
                'CO2Cost_tailpipe_0.03_95',
                'CH4Cost_tailpipe_0.05',
                'CH4Cost_tailpipe_0.03',
                'CH4Cost_tailpipe_0.025',
                'CH4Cost_tailpipe_0.03_95',
                'N2OCost_tailpipe_0.05',
                'N2OCost_tailpipe_0.03',
                'N2OCost_tailpipe_0.025',
                'N2OCost_tailpipe_0.03_95',
                'GHGCost_tailpipe_0.05',
                'GHGCost_tailpipe_0.03',
                'GHGCost_tailpipe_0.025',
                'GHGCost_tailpipe_0.03_95',
            ]
            new_attributes = new_attributes + ghg_attributes

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
