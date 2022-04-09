import pandas as pd


class AnnualSummary:

    _data = dict()

    @staticmethod
    def create_annual_summary_dict():

        AnnualSummary._data.clear()

    @staticmethod
    def annual_summary(settings, source_object, destination_object):
        """

        Parameters:
            settings: The SetInputs class.

        Returns:
            Updates the pv_annualized dictionary with annual, present and annualized values based on the fleet dictionary.

        """
        print(f'\nGetting Annual Values, Present Values and Annualized Values...')

        source_dict = source_object._data
        destination_dict = destination_object._data

        num_alts = len(settings.options_cap._data)
        # if program == 'CAP':
        #     num_alts = settings.number_alts_cap
        # else:
        #     num_alts = settings.number_alts_ghg

        costs_start = settings.general_inputs.get_attribute_value('costs_start')
        discount_to_year = pd.to_numeric(settings.general_inputs.get_attribute_value('discount_to_yearID'))
        if costs_start == 'start-year':
            discount_offset = 0
            annualized_offset = 1
        elif costs_start == 'end-year':
            discount_offset = 1
            annualized_offset = 0

        # get cost attributes but only totals, per vehicle or mile costs are not relevant here
        nested_dict = [n_dict for key, n_dict in source_dict.items()][0]
        all_costs = [k for k, v in nested_dict.items() if 'Cost' in k and 'Per' not in k]
        emission_cost_args_25 = [item for item in all_costs if '_0.025' in item]
        emission_cost_args_3 = [item for item in all_costs if '_0.03' in item]
        emission_cost_args_5 = [item for item in all_costs if '_0.05' in item]
        emission_cost_args_7 = [item for item in all_costs if '_0.07' in item]
        non_emission_cost_args = [item for item in all_costs if '_0.0' not in item]

        rates = [settings.general_inputs.get_attribute_value('social_discount_rate_1'),
                 settings.general_inputs.get_attribute_value('social_discount_rate_2')]
        rates = [pd.to_numeric(rate) for rate in rates]
        years = settings.fleet_cap.years

        # first create a dictionary to house data
        # calcs_dict = settings.annual_summary_cap

        # first undiscounted annual values
        for alt in range(0, num_alts):
            rate = 0
            series = 'AnnualValue'
            for calendar_year in years:
                destination_dict.update({(alt, calendar_year, rate, series): {'optionID': alt,
                                                                              'yearID': calendar_year,
                                                                              'DiscountRate': rate,
                                                                              'Series': series,
                                                                              'Periods': 1,
                                                                              }
                                         }
                                        )

        # then for discounted values
        for series in ['AnnualValue', 'PresentValue', 'AnnualizedValue']:
            for alt in range(0, num_alts):
                for rate in rates:
                    for calendar_year in years:
                        destination_dict.update({(alt, calendar_year, rate, series): {'optionID': alt,
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
            for rate in [0, *rates]:
                for calendar_year in years:
                    for arg in all_costs:
                        arg_sum = sum(v[arg] for k, v in source_dict.items()
                                      if v['yearID'] == calendar_year
                                      and v['DiscountRate'] == rate
                                      and v['optionID'] == alt)
                        destination_dict[(alt, calendar_year, rate, series)][arg] = arg_sum

        # now do a cumulative sum year-over-year for each cost arg - these will be present values (note change to calcs_dict in arg_value calc and removal of rate=0)
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
                        destination_dict[(alt, calendar_year, rate, series)][arg] = arg_value
                        destination_dict[(alt, calendar_year, rate, series)]['Periods'] = periods

        # now annualize those present values
        series = 'AnnualizedValue'
        for alt in range(0, num_alts):
            for social_discount_rate in rates:
                rate = social_discount_rate
                for arg in non_emission_cost_args:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                        arg_annualized = present_value * rate * (1 + rate) ** periods \
                                         / ((1 + rate) ** (periods + annualized_offset) - 1)
                        destination_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized
                        destination_dict[(alt, calendar_year, social_discount_rate, series)]['Periods'] = periods

                rate = 0.025
                for arg in emission_cost_args_25:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                        arg_annualized = present_value * rate * (1 + rate) ** periods \
                                         / ((1 + rate) ** (periods + annualized_offset) - 1)
                        destination_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

                rate = 0.03
                for arg in emission_cost_args_3:
                    for calendar_year in years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                        arg_annualized = present_value * rate * (1 + rate) ** periods \
                                         / ((1 + rate) ** (periods + annualized_offset) - 1)
                        destination_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

                rate = 0.05
                for arg in emission_cost_args_5:
                    for calendar_year in settings.years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                        arg_annualized = present_value * rate * (1 + rate) ** periods \
                                         / ((1 + rate) ** (periods + annualized_offset) - 1)
                        destination_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

                rate = 0.07
                for arg in emission_cost_args_7:
                    for calendar_year in settings.years:
                        periods = calendar_year - discount_to_year + discount_offset
                        present_value = destination_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                        arg_annualized = present_value * rate * (1 + rate) ** periods \
                                         / ((1 + rate) ** (periods + annualized_offset) - 1)
                        destination_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

    @staticmethod
    def get_attribute_value(key, attribute_name):

        return AnnualSummary._data[key][attribute_name]
