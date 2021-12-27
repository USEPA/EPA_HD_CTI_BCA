

def pv_annualized(settings, dict_of_values, program):
    """

    Parameters:
        settings: The SetInputs class. \n
        dict_of_values: Dictionary; provides the values to be summed and annualized. \n
        program: String; the program represented ('CAP', 'GHG') in the dict_of_values.

    Returns:
        A dictionary of annual, present and annualized values based on the dict_of_values.

    """
    print(f'\nGetting Annual Values, Present Values and Annualized Values for {program}...')

    if program == 'CAP':
        num_alts = settings.number_alts_cap
    else:
        num_alts = settings.number_alts_ghg

    if settings.costs_start == 'start-year':
        discount_offset = 0
        annualized_offset = 1
    elif settings.costs_start == 'end-year':
        discount_offset = 1
        annualized_offset = 0
    discount_to_year = settings.discount_to_yearID

    for key, value in dict_of_values.items():
        all_costs = [k for k, v in value.items() if 'Cost' in k]
    emission_cost_args_25 = [item for item in all_costs if '_0.025' in item]
    emission_cost_args_3 = [item for item in all_costs if '_0.03' in item]
    emission_cost_args_5 = [item for item in all_costs if '_0.05' in item]
    emission_cost_args_7 = [item for item in all_costs if '_0.07' in item]
    non_emission_cost_args = [item for item in all_costs if '_0.0' not in item]

    # first create a dictionary to house data
    calcs_dict = dict()

    # first undiscounted annual values
    for alt in range(0, num_alts):
        rate = 0
        series = 'AnnualValue'
        for calendar_year in settings.years:
            calcs_dict.update({(alt, calendar_year, rate, series): {'optionID': alt,
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
            for rate in [settings.social_discount_rate_1, settings.social_discount_rate_2]:
                for calendar_year in settings.years:
                    calcs_dict.update({(alt, calendar_year, rate, series): {'optionID': alt,
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
        for rate in [0, settings.social_discount_rate_1, settings.social_discount_rate_2]:
            for calendar_year in settings.years:
                for arg in all_costs:
                    arg_sum = sum(v[arg] for k, v in dict_of_values.items()
                                  if v['yearID'] == calendar_year
                                  and v['DiscountRate'] == rate
                                  and v['optionID'] == alt)
                                  # if v['modelYearID'] + v['ageID'] == calendar_year
                                  # and v['DiscountRate'] == rate and v['optionID'] == alt)
                    calcs_dict[(alt, calendar_year, rate, series)][arg] = arg_sum

    # now do a cumulative sum year-over-year for each cost arg - these will be present values (note change to calcs_dict in arg_value calc and removal of rate=0)
    series = 'PresentValue'
    for alt in range(0, num_alts):
        for rate in [settings.social_discount_rate_1, settings.social_discount_rate_2]:
            for arg in all_costs:
                for calendar_year in settings.years:
                    periods = calendar_year - discount_to_year + discount_offset
                    arg_value = sum(v[arg] for k, v in calcs_dict.items()
                                    if v['yearID'] <= calendar_year
                                    and v['DiscountRate'] == rate
                                    and v['optionID'] == alt
                                    and v['Series'] == 'AnnualValue')
                    calcs_dict[(alt, calendar_year, rate, series)][arg] = arg_value
                    calcs_dict[(alt, calendar_year, rate, series)]['Periods'] = periods

    # now annualize those present values
    series = 'AnnualizedValue'
    for alt in range(0, num_alts):
        for social_discount_rate in [settings.social_discount_rate_1, settings.social_discount_rate_2]:
            rate = social_discount_rate
            for arg in non_emission_cost_args:
                for calendar_year in settings.years:
                    periods = calendar_year - discount_to_year + discount_offset
                    present_value = calcs_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                    arg_annualized = present_value * rate * (1 + rate) ** periods \
                                     / ((1 + rate) ** (periods + annualized_offset) - 1)
                    calcs_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized
                    calcs_dict[(alt, calendar_year, social_discount_rate, series)]['Periods'] = periods

            rate = 0.025
            for arg in emission_cost_args_25:
                for calendar_year in settings.years:
                    periods = calendar_year - discount_to_year + discount_offset
                    present_value = calcs_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                    arg_annualized = present_value * rate * (1 + rate) ** periods \
                                     / ((1 + rate) ** (periods + annualized_offset) - 1)
                    calcs_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

            rate = 0.03
            for arg in emission_cost_args_3:
                for calendar_year in settings.years:
                    periods = calendar_year - discount_to_year + discount_offset
                    present_value = calcs_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                    arg_annualized = present_value * rate * (1 + rate) ** periods \
                                     / ((1 + rate) ** (periods + annualized_offset) - 1)
                    calcs_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

            rate = 0.05
            for arg in emission_cost_args_5:
                for calendar_year in settings.years:
                    periods = calendar_year - discount_to_year + discount_offset
                    present_value = calcs_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                    arg_annualized = present_value * rate * (1 + rate) ** periods \
                                     / ((1 + rate) ** (periods + annualized_offset) - 1)
                    calcs_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

            rate = 0.07
            for arg in emission_cost_args_7:
                for calendar_year in settings.years:
                    periods = calendar_year - discount_to_year + discount_offset
                    present_value = calcs_dict[alt, calendar_year, rate, 'PresentValue'][arg]
                    arg_annualized = present_value * rate * (1 + rate) ** periods \
                                     / ((1 + rate) ** (periods + annualized_offset) - 1)
                    calcs_dict[(alt, calendar_year, social_discount_rate, series)][arg] = arg_annualized

    return calcs_dict
