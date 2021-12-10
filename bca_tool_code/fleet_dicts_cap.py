import pandas as pd
from bca_tool_code.repair_costs import calc_per_veh_cumulative_vmt


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


class FleetTotalsDict:
    def __init__(self, fleet_dict):
        self.new_attributes = ['DirectCost',
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


class FleetAveragesDict:
    def __init__(self, fleet_dict):
        self.new_attributes = ['VMT_AvgPerVeh',
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

        # df.insert(df.columns.get_loc('VMT_AvgPerVeh'), 'VPOP', fleet_df['VPOP'])
        df['VMT_AvgPerVeh'] = fleet_df['VMT'] / fleet_df['VPOP']

        df.set_index('id', inplace=True)
        fleet_dict = df.to_dict('index')

        fleet_dict = add_keys_for_discounting(fleet_dict, settings.social_discount_rate_1, settings.social_discount_rate_2)

        fleet_dict = calc_per_veh_cumulative_vmt(fleet_dict)

        return fleet_dict

    def update_dict(self, key, attribute, value):
        self.fleet_dict[key][attribute] = value
        return self.fleet_dict

    def get_attribute_value(self, key, attribute):
        value = self.fleet_dict[key][attribute]
        return value
