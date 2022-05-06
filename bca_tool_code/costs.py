import pandas as pd


class Costs:

    def __init__(self):
        self._dict = dict()
        self.attributes_to_sum = None

    def create_costs_dict(self, settings, program, vehicles):

        discount_rate = 0
        new_attributes = self.create_new_attributes(settings, program)
        update_dict = dict()
        for new_attribute in new_attributes:
            update_dict.update({new_attribute: 0})

        for vehicle in vehicles:
            key = (vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, vehicle.age_id, discount_rate)
            self.update_object_dict(key, update_dict)

        add_keys_for_discounting(settings.general_inputs, self._dict)

    def update_object_dict(self, key, update_dict):
        """

        Parameters:
            key: tuple; ((vehicle_id), option_id, modelyear_id, age_id, discount_rate).\n
            update_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        """
        if key in self._dict:
            for attribute_name, attribute_value in update_dict.items():
                self._dict[key][attribute_name] = attribute_value

        else:
            self._dict.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self._dict[key].update({attribute_name: attribute_value})

    def define_attributes_to_sum(self, program):
        """

        Parameters:
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').\n

        Returns:
            Updates the attributes_to_sum object dictionary.

        """
        # create a dictionary of attributes to be summed (dict keys) and what attributes to include in the sum (dict values)
        # use pre-tax fuel price for total costs since it serves as the basis for social costs; use retail for averages
        if program == 'CAP':
            self.attributes_to_sum = {'OperatingCost':
                                          ['DEFCost', 'FuelCost_Pretax', 'EmissionRepairCost'],
                                      'TechAndOperatingCost':
                                          ['TechCost', 'OperatingCost'],
                                      'OperatingCost_Owner_PerMile':
                                          ['DEFCost_PerMile', 'FuelCost_Retail_PerMile', 'EmissionRepairCost_PerMile'],
                                      'OperatingCost_Owner_PerVeh':
                                          ['DEFCost_PerVeh', 'FuelCost_Retail_PerVeh', 'EmissionRepairCost_PerVeh']}
        else:
            self.attributes_to_sum = {'OperatingCost':
                                          ['FuelCost_Pretax'],
                                      'TechAndOperatingCost':
                                          ['TechCost', 'OperatingCost'],
                                      'OperatingCost_Owner_PerMile':
                                          ['FuelCost_Retail_PerMile'],
                                      'OperatingCost_Owner_PerVeh':
                                          ['FuelCost_Retail_PerVeh']}

    @staticmethod
    def create_new_attributes(settings, program):
        """

        Parameters:
            settings: object; the SetInputs class object. \n
            program: str; represents the program for the given instance (i.e., 'CAP' or 'GHG').

        Returns:
            A list of new attributes to be added to the data_object dictionary.

        """
        if program == 'CAP':
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
                              'TechAndOperatingCost'
                              'VMT_PerVeh',
                              'VMT_PerVeh_Cumulative',
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
        else:
            new_attributes = ['TechCost',
                              'FuelCost_Retail',
                              'FuelCost_Pretax',
                              'OperatingCost',
                              'TechAndOperatingCost'
                              'VMT_PerVeh',
                              'VMT_PerVeh_Cumulative',
                              'TechCost_PerVeh',
                              'FuelCost_Retail_PerMile',
                              'FuelCost_Retail_PerVeh',
                              'OperatingCost_Owner_PerMile',
                              'OperatingCost_Owner_PerVeh',
                              ]

        if settings.calc_cap_pollution:
            cap_attributes = ['PM25Cost_tailpipe_0.03', 'NOxCost_tailpipe_0.03',
                              'PM25Cost_tailpipe_0.07', 'NOxCost_tailpipe_0.07',
                              'CriteriaCost_tailpipe_0.03', 'CriteriaCost_tailpipe_0.07',
                              ]
            new_attributes = new_attributes + cap_attributes

        if settings.calc_ghg_pollution:
            ghg_attributes = ['CO2Cost_tailpipe_0.05', 'CO2Cost_tailpipe_0.03', 'CO2Cost_tailpipe_0.025',
                              'CO2Cost_tailpipe_0.03_95',
                              'CH4Cost_tailpipe_0.05', 'CH4Cost_tailpipe_0.03', 'CH4Cost_tailpipe_0.025',
                              'CH4Cost_tailpipe_0.03_95',
                              'N2OCost_tailpipe_0.05', 'N2OCost_tailpipe_0.03', 'N2OCost_tailpipe_0.025',
                              'N2OCost_tailpipe_0.03_95',
                              'GHGCost_tailpipe_0.05', 'GHGCost_tailpipe_0.03', 'GHGCost_tailpipe_0.025',
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
        for key in input_dict.keys():
            vehicle, alt, model_year, age, discount_rate = key
            update_dict[vehicle, alt, model_year, age, rate] = input_dict[key].copy()
            update_dict[vehicle, alt, model_year, age, rate]['DiscountRate'] = rate
        input_dict.update(update_dict)
