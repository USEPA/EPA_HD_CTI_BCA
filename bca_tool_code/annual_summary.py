import pandas as pd


class AnnualSummary:

    def __init__(self):
        self._dict = dict()

    # _dict = dict()

    # @staticmethod
    # def create_annual_summary_dict():
    #
    #     AnnualSummaryGHG._dict.clear()
    #
    #     return AnnualSummaryGHG._dict

    # @staticmethod
    def annual_summary(self, settings, source, destination, options):
        """

        Parameters:
            settings: The SetInputs class.\n
            source: Object; the fleet data object to summarize.\n
            destination: Object; the annual summary object to be updated.\n
            options: Object; the options object associated with the source object.

        Returns:
            Updates the annual summary dictionary with annual, present and annualized values based on the source object.

        """
        print(f'\nCalculating Annual Values, Present Values and Annualized Values...')

        source_dict = source._dict
        destination_dict = destination._dict
        num_alts = len(options._dict)

        costs_start = settings.general_inputs.get_attribute_value('costs_start')
        discount_to_year = pd.to_numeric(settings.general_inputs.get_attribute_value('discount_to_yearID'))
        discount_offset = 0
        annualized_offset = 1
        if costs_start == 'end-year':
            discount_offset = 1
            annualized_offset = 0

        # get cost attributes but only totals, per vehicle or mile costs are not relevant here
        nested_dict = [n_dict for key, n_dict in source_dict.items()][0]
        all_costs = tuple([k for k, v in nested_dict.items() if 'Cost' in k and 'Per' not in k])
        emission_cost_args_25 = tuple([item for item in all_costs if '_0.025' in item])
        emission_cost_args_3 = tuple([item for item in all_costs if '_0.03' in item])
        emission_cost_args_5 = tuple([item for item in all_costs if '_0.05' in item])
        emission_cost_args_7 = tuple([item for item in all_costs if '_0.07' in item])
        non_emission_cost_args = tuple([item for item in all_costs if '_0.0' not in item])

        rates = tuple([settings.general_inputs.get_attribute_value('social_discount_rate_1'),
                       settings.general_inputs.get_attribute_value('social_discount_rate_2')])
        rates = tuple([pd.to_numeric(rate) for rate in rates])
        years = source.years

        # build the destination dictionary to house data

        # first undiscounted annual values
        for alt in range(0, num_alts):
            rate = 0
            series = 'AnnualValue'
            for calendar_year in years:
                destination_dict.update({(series, alt, calendar_year, rate): {'optionID': alt,
                                                                              'yearID': calendar_year,
                                                                              'DiscountRate': rate,
                                                                              'Series': series,
                                                                              'Periods': 1,
                                                                              }
                                         }
                                        )

        # then for discounted values
        for series in ('AnnualValue', 'PresentValue', 'AnnualizedValue'):
            for alt in range(0, num_alts):
                for rate in rates:
                    for calendar_year in years:
                        destination_dict.update({(series, alt, calendar_year, rate): {'optionID': alt,
                                                                                      'yearID': calendar_year,
                                                                                      'DiscountRate': rate,
                                                                                      'Series': series,
                                                                                      'Periods': 1,
                                                                                      }
                                                 }
                                                )

        # first sum by year for each cost arg
        series = 'AnnualValue'
        for alt in range(0, num_alts):
            for rate in (0, *rates):
                for calendar_year in years:
                    for arg in all_costs:
                        arg_sum = sum(v[arg] for k, v in source_dict.items()
                                      if v['yearID'] == calendar_year
                                      and v['DiscountRate'] == rate
                                      and v['optionID'] == alt)
                        destination_dict[(series, alt, calendar_year, rate)][arg] = arg_sum

        # now do a cumulative sum year-over-year for each cost arg - these will be present values
        # (note change to destination_dict in arg_value calc and removal of rate=0)
        series = 'PresentValue'
        for alt in range(0, num_alts):
            for rate in rates:
                for arg in all_costs:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        arg_value = sum(v[arg] for k, v in destination_dict.items()
                                        if v['yearID'] <= calendar_year
                                        and v['DiscountRate'] == rate
                                        and v['optionID'] == alt
                                        and v['Series'] == 'AnnualValue')
                        destination_dict[(series, alt, calendar_year, rate)][arg] = arg_value
                        destination_dict[(series, alt, calendar_year, rate)]['Periods'] = periods

        # now annualize those present values
        series = 'AnnualizedValue'
        for alt in range(0, num_alts):
            for social_discount_rate in rates:
                rate = social_discount_rate
                for arg in non_emission_cost_args:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict['PresentValue', alt, calendar_year, rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, rate, periods, annualized_offset)
                        destination_dict[(series, alt, calendar_year, social_discount_rate)][arg] = arg_annualized
                        destination_dict[(series, alt, calendar_year, social_discount_rate)]['Periods'] = periods

                rate = 0.025
                for arg in emission_cost_args_25:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict['PresentValue', alt, calendar_year, rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, rate, periods, annualized_offset)
                        destination_dict[(series, alt, calendar_year, social_discount_rate)][arg] = arg_annualized

                rate = 0.03
                for arg in emission_cost_args_3:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict['PresentValue', alt, calendar_year, rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, rate, periods, annualized_offset)
                        destination_dict[(series, alt, calendar_year, social_discount_rate)][arg] = arg_annualized

                rate = 0.05
                for arg in emission_cost_args_5:
                    for calendar_year in settings.years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict['PresentValue', alt, calendar_year, rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, rate, periods, annualized_offset)
                        destination_dict[(series, alt, calendar_year, social_discount_rate)][arg] = arg_annualized

                rate = 0.07
                for arg in emission_cost_args_7:
                    for calendar_year in settings.years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict['PresentValue', alt, calendar_year, rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, rate, periods, annualized_offset)
                        destination_dict[(series, alt, calendar_year, social_discount_rate)][arg] = arg_annualized

    # @staticmethod
    def get_attribute_value(self, key, attribute_name):

        return self._dict[key][attribute_name]

    # @staticmethod
    def update_dict(self, key, input_dict):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            The dictionary instance with each attribute updated with the appropriate value.

        """
        for attribute_name, attribute_value in input_dict.items():
            self._dict[key][attribute_name] = attribute_value

    # @staticmethod
    def add_key_value_pairs(self, key, input_dict):

        self._dict[key] = input_dict

    @staticmethod
    def calc_annualized_value(present_value, rate, periods, annualized_offset):

        return present_value * rate * (1 + rate) ** periods \
               / ((1 + rate) ** (periods + annualized_offset) - 1)
