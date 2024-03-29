import pandas as pd


class AnnualSummary:
    """

    The AnnualSummary class creates a summary of results by year_id along with present values and annualized values
    for use in the benefit-cost analysis.

    """
    def __init__(self):
        self.results = dict()

    def annual_summary(self, settings, data_object, options, year_ids):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            data_object: object; the fleet data object to summarize.\n
            options: object; the options object associated with the data_object.\n
            year_ids: range; the min_year_id thru max_year_id as set in settings.

        Returns:
            Updates the annual summary dictionary with annual, present and annualized values based on the data_object.

        """
        print(f'\nCalculating Annual Values, Present Values and Annualized Values...')

        source_dict = data_object.results
        num_option_ids = len(options._dict)

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

        social_rates = tuple([settings.general_inputs.get_attribute_value('social_discount_rate_1'),
                              settings.general_inputs.get_attribute_value('social_discount_rate_2')])
        social_rates = tuple([pd.to_numeric(rate) for rate in social_rates])

        # build the destination dictionary to house data

        # first undiscounted annual values
        for option_id in range(0, num_option_ids):
            rate = 0
            series = 'AnnualValue'
            for year_id in year_ids:
                self.results.update({
                    (series, option_id, year_id, rate): {
                        'optionID': option_id,
                        'optionName': options.get_option_name(option_id),
                        'yearID': year_id,
                        'DiscountRate': rate,
                        'Series': series,
                        'Periods': 1,
                    }
                }
                )

        # then for discounted values
        for series in ('AnnualValue', 'PresentValue', 'AnnualizedValue'):
            for option_id in range(0, num_option_ids):
                for social_rate in social_rates:
                    for year_id in year_ids:
                        self.results.update({
                            (series, option_id, year_id, social_rate): {
                                'optionID': option_id,
                                'optionName': options.get_option_name(option_id),
                                'yearID': year_id,
                                'DiscountRate': social_rate,
                                'Series': series,
                                'Periods': 1,
                            }
                        }
                        )

        # first sum by year for each cost arg
        series = 'AnnualValue'
        for option_id in range(0, num_option_ids):
            for social_rate in (0, *social_rates):
                for year_id in year_ids:
                    temp_dict = {k: v for k, v in source_dict.items()
                                 if v['yearID'] == year_id
                                 and v['DiscountRate'] == social_rate
                                 and v['optionID'] == option_id}
                    for arg in all_costs:
                        arg_sum = sum(v[arg] for k, v in temp_dict.items())
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_sum

        # now do a cumulative sum year-over-year for each cost arg - these will be present values
        # (note change to destination_dict in arg_value calc and removal of rate=0)
        series = 'PresentValue'
        for option_id in range(0, num_option_ids):
            for social_rate in social_rates:
                for arg in all_costs:
                    for year_id in year_ids:
                        periods = year_id - discount_to_year + discount_offset
                        if (series, option_id, year_id - 1, social_rate) not in self.results:
                            arg_value = self.results[('AnnualValue', option_id, year_id, social_rate)][arg]
                        else:
                            arg_value = self.results[(series, option_id, year_id - 1, social_rate)][arg]
                            arg_value += self.results[('AnnualValue', option_id, year_id, social_rate)][arg]
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_value
                        self.results[(series, option_id, year_id, social_rate)]['Periods'] = periods

        # now annualize those present values
        series = 'AnnualizedValue'
        for option_id in range(0, num_option_ids):
            for social_rate in social_rates:
                for arg in non_emission_cost_args:
                    for year_id in year_ids:
                        periods = year_id - discount_to_year + discount_offset
                        present_value = self.results['PresentValue', option_id, year_id, social_rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, social_rate, periods, annualized_offset)
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_annualized
                        self.results[(series, option_id, year_id, social_rate)]['Periods'] = periods

                emission_rate = 0.025
                for arg in emission_cost_args_25:
                    for year_id in year_ids:
                        periods = year_id - discount_to_year + discount_offset
                        present_value = self.results['PresentValue', option_id, year_id, social_rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, emission_rate, periods, annualized_offset)
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_annualized

                emission_rate = 0.03
                for arg in emission_cost_args_3:
                    for year_id in year_ids:
                        periods = year_id - discount_to_year + discount_offset
                        present_value = self.results['PresentValue', option_id, year_id, social_rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, emission_rate, periods, annualized_offset)
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_annualized

                emission_rate = 0.05
                for arg in emission_cost_args_5:
                    for year_id in year_ids:
                        periods = year_id - discount_to_year + discount_offset
                        present_value = self.results['PresentValue', option_id, year_id, social_rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, emission_rate, periods, annualized_offset)
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_annualized

                emission_rate = 0.07
                for arg in emission_cost_args_7:
                    for year_id in year_ids:
                        periods = year_id - discount_to_year + discount_offset
                        present_value = self.results['PresentValue', option_id, year_id, social_rate][arg]
                        arg_annualized = self.calc_annualized_value(present_value, emission_rate, periods, annualized_offset)
                        self.results[(series, option_id, year_id, social_rate)][arg] = arg_annualized

    def get_attribute_value(self, key, attribute_name):
        """

        Parameters:
            key: tuple; (series, option_id, year_id, rate), where series is 'AnnualValue', 'PresentValue' or 'AnnualizedValue'.\n
            attribute_name: str; the attribute for which the value is sought.

        Returns:
            The value associated with the attribute for the given key.

        """
        return self.results[key][attribute_name]

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

    @staticmethod
    def calc_annualized_value(present_value, rate, periods, annualized_offset):
        """

        Parameters:
            present_value: Numeric; the present value to be annualized.\n
            rate: Numeric; the discount rate to use.\n
            periods: int; the number of periods over which to annualize present_value.\n
            annualized_offset: int; 0 or 1 reflecting whether costs are assumed to occur at the start of the year or the end of the year.

        Returns:
            A single annualized value of present_value discounted at rate over periods number of year_ids.

        """
        return present_value * rate * (1 + rate) ** periods \
               / ((1 + rate) ** (periods + annualized_offset) - 1)
