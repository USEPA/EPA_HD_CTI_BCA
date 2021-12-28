import pandas as pd
from bca_tool_code.fleet_totals_dict import add_keys_for_discounting


class FleetAverages:
    """
    A FleetAverages object contains annual averages for vehicles by model year and by calendar year.

    Parameters:
        fleet_dict: Dictionary; contains fleet data, averages by model year and calendar year.

    """
    def __init__(self, fleet_dict):
        self.fleet_dict = fleet_dict

    def create_new_attributes(self):
        """

        Returns:
            A list of new attributes to be calculated and provided in output files.

        """
        new_attributes = ['VMT_AvgPerVeh',
                          'VMT_AvgPerVeh_Cumulative',
                          'DirectCost_AvgPerVeh',
                          'WarrantyCost_AvgPerVeh',
                          'RnDCost_AvgPerVeh',
                          'OtherCost_AvgPerVeh',
                          'ProfitCost_AvgPerVeh',
                          'IndirectCost_AvgPerVeh',
                          'TechCost_AvgPerVeh',
                          'DEFCost_AvgPerMile',
                          'DEFCost_AvgPerVeh',
                          'FuelCost_Retail_AvgPerMile',
                          'FuelCost_Retail_AvgPerVeh',
                          'EmissionRepairCost_AvgPerMile',
                          'EmissionRepairCost_AvgPerVeh',
                          'OperatingCost_Owner_AvgPerMile',
                          'OperatingCost_Owner_AvgPerVeh',
                          ]
        return new_attributes

    def create_fleet_averages_dict(self, settings, fleet_df):
        """
        This function creates a dictionary of fleet average values and adds a discount rate element to the key. It also calculates an average annual VMT/vehicle and
        a cumulative annual average VMT/vehicle.

        Parameters:
            settings: The SetInputs class.\n
            fleet_df: DataFrame; the project fleet DataFrame.

        Returns:
            A dictionary of the fleet having keys equal to ((vehicle), modelYearID, ageID, discount_rate) where vehicle is a tuple representing
            an alt_sourcetype_regclass_fueltype vehicle, and values representing per vehicle or per mile averages for each key over time.

        """
        fleet_df_attributes_to_use = [item for item in fleet_df.columns
                                      if 'tons' not in item
                                      and 'Gallons' not in item
                                      and 'Energy' not in item
                                      and 'VMT' not in item]
        new_attributes = self.create_new_attributes()

        df = pd.DataFrame(fleet_df[fleet_df_attributes_to_use]).reset_index(drop=True)
        df.insert(0, 'DiscountRate', 0)
        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.insert(0, 'id', key)

        for attribute in new_attributes:
            df.insert(len(df.columns), f'{attribute}', 0)

        df['VMT_AvgPerVeh'] = fleet_df['VMT'] / fleet_df['VPOP']

        df.set_index('id', inplace=True)
        fleet_dict = df.to_dict('index')

        fleet_dict = self.calc_per_veh_cumulative_vmt(fleet_dict)
        fleet_dict = add_keys_for_discounting(fleet_dict, settings.social_discount_rate_1, settings.social_discount_rate_2)

        return fleet_dict

    def update_dict(self, key, input_dict):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with 'attribute' updated with 'value.'

        """
        for attribute, value in input_dict.items():
            self.fleet_dict[key][attribute] = value

        return self.fleet_dict

    def get_attribute_value(self, key, attribute):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            attribute: String; represents the attribute to be updated.

        Returns:
            The value of 'attribute' within the dictionary instance.

        """
        value = self.fleet_dict[key][attribute]

        return value

    @staticmethod
    def calc_per_veh_cumulative_vmt(fleet_dict):
        """This function calculates cumulative average VMT/vehicle year-over-year for use in estimating a typical VMT per year and for estimating emission
        repair costs.

        Parameters:
            fleet_dict: Dictionary; represents the dictionary instance.

        Returns:
            The dictionary instance updated with cumulative annual average VMT/vehicle.

        Note:
            VMT does not differ across options.

        """
        # this loop calculates the cumulative vmt for each key with the averages_dict and saves it in the cumulative_vmt_dict
        cumulative_vmt_dict = dict()
        for key in fleet_dict.keys():
            vehicle, alt, model_year, age_id, disc_rate = key
            if (vehicle, alt, model_year, age_id-1, 0) in cumulative_vmt_dict.keys():
                cumulative_vmt = cumulative_vmt_dict[(vehicle, 0, model_year, age_id-1, 0)] + FleetAverages(fleet_dict).get_attribute_value(key, 'VMT_AvgPerVeh')
            else:
                cumulative_vmt = FleetAverages(fleet_dict).get_attribute_value(key, 'VMT_AvgPerVeh')
            cumulative_vmt_dict[key] = cumulative_vmt

        # this loop updates the averages_dict with the contents of the cumulative_vmt_dict
        for key in fleet_dict.keys():
            cumulative_vmt = cumulative_vmt_dict[key]
            FleetAverages(fleet_dict).update_dict(key, {'VMT_AvgPerVeh_Cumulative': cumulative_vmt})

        return fleet_dict
