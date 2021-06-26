

def calc_sum_of_costs(dict_to_sum, name_of_sum, *args):
    """

    Parameters::
        dict_to_sum: A dictionary containing the parameters to be summed.\n
        name_of_sum: A string used to identify the sum being done.\n
        args: The parameters (strings) to be summed.

    Returns:
        The passed dictionary updated to include a new 'name_of_sum' parameter that sums the passed args for each dictionary key.

    """
    for key in dict_to_sum.keys():
        vehicle, alt, model_year, age_id, discount_rate = key
        print(f'Calculating sum of {name_of_sum} for {vehicle}, optionID {alt}, MY {model_year}, age {age_id}, DR {discount_rate}')
        sum_of_costs = 0
        # note that some key, value pairs lack some data (e.g., ft=1 has no DEF cost) so the try/except addresses that
        for arg in args:
            try:
                sum_of_costs += dict_to_sum[key][arg]
            except:
                pass
        dict_to_sum[key].update({f'{name_of_sum}': sum_of_costs})
    return dict_to_sum
