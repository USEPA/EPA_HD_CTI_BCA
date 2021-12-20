import pandas as pd


def add_keys_for_discounting(input_dict, *rates):
    """

    Parameters:
        input_dict: Dictionary; into which new keys will be added that provide room for discounting data. \n
        *rates: Numeric; the discount rate keys to add.

    Returns:
        The passed dictionary with new keys added.

    """
    return_dict = input_dict.copy()
    for rate in rates:
        update_dict = dict()
        for key in input_dict.keys():
            vehicle, alt, model_year, age, discount_rate = key
            update_dict[vehicle, alt, model_year, age, rate] = input_dict[key].copy()
            update_dict[vehicle, alt, model_year, age, rate]['DiscountRate'] = rate
        return_dict.update(update_dict)

    return return_dict


class FleetTotals:
    def __init__(self, fleet_dict):
        self.fleet_dict = fleet_dict

    def create_new_attributes(self, calc_cap_pollution, calc_ghg_pollution):
        """

        Parameters:
            calc_cap_pollution: True or None. \n
            calc_ghg_pollution: True or None.

        Returns:
            A list of new attributes to be calculated and provided in output files.

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
                          ]
        if calc_cap_pollution:
            cap_attributes = ['PM25_Costs_tailpipe_0.03', 'NOx_Costs_tailpipe_0.03', 'SO2_Costs_tailpipe_0.03',
                              'PM25_Costs_tailpipe_0.07', 'NOx_Costs_tailpipe_0.07', 'SO2_Costs_tailpipe_0.07',
                              'Criteria_Costs_tailpipe_0.03', 'Criteria_Costs_tailpipe_0.07',
                              ]
            new_attributes = new_attributes + cap_attributes
        if calc_ghg_pollution:
            ghg_attributes = ['CO2_Costs_0.05', 'CO2_Costs_0.03', 'CO2_Costs_0.025', 'CO2_Costs_0.03_95',
                              'CH4_Costs_0.05', 'CH4_Costs_0.03', 'CH4_Costs_0.025', 'CH4_Costs_0.03_95',
                              'N2O_Costs_0.05', 'N2O_Costs_0.03', 'N2O_Costs_0.025', 'N2O_Costs_0.03_95',
                              'GHG_Costs_0.05', 'GHG_Costs_0.03', 'GHG_Costs_0.025', 'GHG_Costs_0.03_95',
                              ]
            new_attributes = new_attributes + ghg_attributes

        return new_attributes

    def create_fleet_totals_dict(self, settings, fleet_df):
        """
        This method creates a dictionary of fleet total values and adds a discount rate element to the key.

        Parameters:
            settings: The SetInputs class.\n
            fleet_df: DataFrame; the project fleet.

        Returns:
            A dictionary of the fleet having keys equal to ((vehicle), modelYearID, ageID, discount_rate) where vehicle is a tuple representing
            an alt_sourcetype_regclass_fueltype vehicle, and values representing totals for each key over time.

        """
        df = fleet_df.copy()
        df.insert(0, 'DiscountRate', 0)
        key = pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']), df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate']))
        df.insert(0, 'id', key)
        df.set_index('id', inplace=True)

        new_attributes = self.create_new_attributes(settings.calc_cap_pollution_effects, settings.calc_ghg_pollution_effects)
        for attribute in new_attributes:
            df.insert(len(df.columns), f'{attribute}', 0)

        fleet_dict = df.to_dict('index')

        fleet_dict = add_keys_for_discounting(fleet_dict, settings.social_discount_rate_1, settings.social_discount_rate_2)

        return fleet_dict

    def create_regclass_sales_dict(self, fleet_df):
        """

        This method simply generates sales by regclass via Pandas which is faster than summing via dictionary.

        Parameters:
            fleet_df: DataFrame; the project fleet.

        Returns:
            A dictionary of the fleet having keys equal to ((unit), alt, modelYearID) where unit is a tuple representing
            a regclass_fueltype, and values representing sales (sales=VPOP at ageID=0) for each key by model year.

        """
        df = fleet_df.copy()
        df.insert(0, 'DiscountRate', 0)
        df = pd.DataFrame(df.loc[df['ageID'] == 0, ['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID', 'DiscountRate',
                                                    'VPOP', 'VPOP_withTech']]).reset_index(drop=True)
        df = df.groupby(by=['optionID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID', 'DiscountRate'], as_index=False).sum()
        df.insert(0,
                  'id',
                  pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']),
                                df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate'])))
        df.set_index('id', inplace=True)

        return df.to_dict('index')

    def create_sourcetype_sales_dict(self, fleet_df):
        """

        This method simply generates sales by sourcetype via Pandas which is faster than summing via dictionary.

        Parameters:
            fleet_df: DataFrame; the project fleet.

        Returns:
            A dictionary of the fleet having keys equal to ((unit), alt, modelYearID) where unit is a tuple representing
            a sourcetype_regclass_fueltype, and values representing sales (sales=VPOP at ageID=0) for each key by model year.

        """
        df = fleet_df.copy()
        df.insert(0, 'DiscountRate', 0)
        df = pd.DataFrame(df.loc[df['ageID'] == 0, ['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID', 'DiscountRate',
                                                    'VPOP', 'VPOP_withTech']]).reset_index(drop=True)
        df = df.groupby(by=['optionID', 'sourceTypeID', 'regClassID', 'fuelTypeID', 'modelYearID', 'ageID', 'DiscountRate'], as_index=False).sum()
        df.insert(0,
                  'id',
                  pd.Series(zip(zip(df['sourceTypeID'], df['regClassID'], df['fuelTypeID']),
                                df['optionID'], df['modelYearID'], df['ageID'], df['DiscountRate'])))
        df.set_index('id', inplace=True)

        return df.to_dict('index')

    def calc_unit_sales(self, unit, alt, model_year, sales_arg):
        """

        Parameters:
            unit: Tuple; represents a regclass-fueltype engine or sourcetype-regclass-fueltype vehicle. \n
            alt: Numeric; represents the Alternative or optionID. \n
            model_year: Numeric; represents the model year of the passed unit. \n
            sales_arg: String; represents the sales attribute to use. \n

        Returns:
            A single sales value (Numeric, i.e., sales_arg value) for the given unit, model_year, alt.

        Note:
            DiscountRate is set to zero since sales numbers will not change with discount rate.

        """
        try:
            rc, ft = unit
            st = None
        except:
            st, rc, ft = unit

        if st:
            sales = sum(v[sales_arg] for k, v in self.fleet_dict.items()
                        if v['sourceTypeID'] == st
                        and v['regClassID'] == rc
                        and v['fuelTypeID'] == ft
                        and v['optionID'] == alt
                        and v['modelYearID'] == model_year
                        and v['ageID'] == 0
                        and v['DiscountRate'] == 0)
        else:
            sales = sum(v[sales_arg] for k, v in self.fleet_dict.items()
                        if v['regClassID'] == rc
                        and v['fuelTypeID'] == ft
                        and v['optionID'] == alt
                        and v['modelYearID'] == model_year
                        and v['ageID'] == 0
                        and v['DiscountRate'] == 0)
        return sales

    def calc_unit_cumulative_sales(self, unit, alt, start_model_year, end_model_year, sales_arg):
        """

        Parameters:
            unit: Tuple; represents a regclass-fueltype engine or sourcetype-regclass-fueltype vehicle. \n
            alt: Numeric; represents the Alternative or optionID. \n
            start_model_year: Numeric; represents the initial model year of sales to include. \n
            end_model_year: Numeric; represents the final model year of sales to include (e.g., the unit's model year. \n
            sales_arg: String; represents the sales attribute to use. \n

        Returns:
            A single cumulative sales value (Numeric, i.e., sales_arg value) for the given unit, model_year, alt.

        Note:
            DiscountRate is set to zero since sales numbers will not change with discount rate.

        """
        try:
            rc, ft = unit
            st = None
        except:
            st, rc, ft = unit

        if st:
            sales = sum(v[sales_arg] for k, v in self.fleet_dict.items()
                        if v['sourceTypeID'] == st
                        and v['regClassID'] == rc
                        and v['fuelTypeID'] == ft
                        and v['optionID'] == alt
                        and (v['modelYearID'] >= start_model_year and v['modelYearID'] <= end_model_year)
                        and v['ageID'] == 0
                        and v['DiscountRate'] == 0)
        else:
            sales = sum(v[sales_arg] for k, v in self.fleet_dict.items()
                        if v['regClassID'] == rc
                        and v['fuelTypeID'] == ft
                        and v['optionID'] == alt
                        and (v['modelYearID'] >= start_model_year and v['modelYearID'] <= end_model_year)
                        and v['ageID'] == 0
                        and v['DiscountRate'] == 0)
        return sales

    def update_dict(self, key, attribute, value):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            attribute: String; represents the attribute to be updated.\n
            value: Any; represents the value of the attribute to be updated.

        Returns:
            The dictionary instance with 'attribute' updated with 'value.'

        """
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
