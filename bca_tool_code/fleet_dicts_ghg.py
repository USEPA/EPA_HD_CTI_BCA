import pandas as pd


def add_keys_for_discounting(input_dict, *rates):

    return_dict = input_dict.copy()
    for rate in rates:
        update_dict = dict()
        for key in input_dict.keys():
            vehicle, alt, model_year, age, discount_rate = key
            update_dict[vehicle, alt, model_year, age, rate] = input_dict[key].copy()
            update_dict[vehicle, alt, model_year, age, rate]['DiscountRate'] = rate
        return_dict.update(update_dict)
    return return_dict


class FleetTotalsGHG:
    def __init__(self, fleet_dict):
        # TODO: If emission costs are being calculated, those attributes have to be added to new_attributes
        self.new_attributes = ['TechCost',
                               'FuelCost_Retail',
                               'FuelCost_Pretax',
                               'OperatingCost',
                               'TechAndOperatingCost',
                               ]
        self.fleet_dict = fleet_dict

    def create_fleet_totals_dict(self, settings, fleet_df):
        """This method creates a dictionary of fleet total values and adds a discount rate element to the key.

        Parameters:
            fleet_df: A DataFrame of the project fleet.

        Returns:
            A dictionary of the fleet having keys equal to ((vehicle), modelYearID, ageID, discount_rate) where vehicle is a tuple representing
            an alt_sourcetype_regclass_fueltype vehicle, and values representing totals for each key over time.

        """
        df = fleet_df.copy()
        df.insert(0, 'DiscountRate', 0)
        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.insert(0, 'id', key)
        df.set_index('id', inplace=True)

        for attribute in self.new_attributes:
            df.insert(len(df.columns), f'{attribute}', 0)

        fleet_dict = df.to_dict('index')

        fleet_dict = add_keys_for_discounting(fleet_dict, settings.social_discount_rate_1, settings.social_discount_rate_2)

        return fleet_dict

    def update_dict(self, key, attribute, value):
        self.fleet_dict[key][attribute] = value
        return self.fleet_dict

    def get_attribute_value(self, key, attribute):
        value = self.fleet_dict[key][attribute]
        return value


class FleetAveragesGHG:
    def __init__(self, fleet_dict):
        self.new_attributes = ['VMT_AvgPerVeh',
                               'VMT_AvgPerVeh_Cumulative',
                               'TechCost_AvgPerVeh',
                               'FuelCost_Retail_AvgPerMile',
                               'FuelCost_Retail_AvgPerVeh',
                               'OperatingCost_Owner_AvgPerVeh',
                               ]
        self.fleet_dict = fleet_dict

    def create_fleet_averages_dict(self, settings, fleet_df):
        """This function creates a dictionary of fleet average values and adds a discount rate element to the key. It also calculates an average annual VMT/vehicle and
        a cumulative annual average VMT/vehicle.

        Parameters:
            fleet_df: A DataFrame of the project fleet.\n

        Returns:
            A dictionary of the fleet having keys equal to ((vehicle), modelYearID, ageID, discount_rate) where vehicle is a tuple representing
            an alt_sourcetype_regclass_fueltype vehicle, and values representing per vehicle or per mile averages for each key over time.

        """
        attributes_to_use = [item for item in fleet_df.columns
                             if 'tons' not in item
                             and 'Gallons' not in item
                             and 'Energy' not in item
                             and 'VMT' not in item]

        df = pd.DataFrame(fleet_df[attributes_to_use]).reset_index(drop=True)
        df.insert(0, 'DiscountRate', 0)
        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.insert(0, 'id', key)

        for attribute in self.new_attributes:
            df.insert(len(df.columns), f'{attribute}', 0)

        df['VMT_AvgPerVeh'] = fleet_df['VMT'] / fleet_df['VPOP']

        df.set_index('id', inplace=True)
        fleet_dict = df.to_dict('index')

        fleet_dict = self.calc_per_veh_cumulative_vmt(fleet_dict)
        fleet_dict = add_keys_for_discounting(fleet_dict, settings.social_discount_rate_1, settings.social_discount_rate_2)

        return fleet_dict

    def update_dict(self, key, attribute, value):
        self.fleet_dict[key][attribute] = value
        return self.fleet_dict

    def get_attribute_value(self, key, attribute):
        value = self.fleet_dict[key][attribute]
        return value

    @staticmethod
    def calc_per_veh_cumulative_vmt(fleet_dict):
        """This function calculates cumulative average VMT/vehicle year-over-year for use in estimating a typical VMT per year and for estimating emission
        repair costs.

        Parameters:
            averages_dict: A dictionary containing annual average VMT/vehicle.

        Returns:
            The averages_dict dictionary updated with cumulative annual average VMT/vehicle.

        Note:
            VMT does not differ across options.

        """
        # this loop calculates the cumulative vmt for each key with the averages_dict and saves it in the cumulative_vmt_dict
        cumulative_vmt_dict = dict()
        for key in fleet_dict.keys():
            vehicle, alt, model_year, age_id, disc_rate = key
            if (vehicle, alt, model_year, age_id-1, 0) in cumulative_vmt_dict.keys():
                cumulative_vmt = cumulative_vmt_dict[(vehicle, 0, model_year, age_id-1, 0)] + FleetAveragesGHG(fleet_dict).get_attribute_value(key, 'VMT_AvgPerVeh')
            else:
                cumulative_vmt = FleetAveragesGHG(fleet_dict).get_attribute_value(key, 'VMT_AvgPerVeh')
            cumulative_vmt_dict[key] = cumulative_vmt
        # this loop updates the averages_dict with the contents of the cumulative_vmt_dict
        for key in fleet_dict.keys():
            cumulative_vmt = cumulative_vmt_dict[key]
            FleetAveragesGHG(fleet_dict).update_dict(key, 'VMT_AvgPerVeh_Cumulative', cumulative_vmt)
        return fleet_dict
