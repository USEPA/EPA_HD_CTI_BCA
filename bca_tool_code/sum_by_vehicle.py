

def calc_sum_of_costs(dict_to_sum, name_of_sum, *args):
    """

    Parameters::
        dict_to_sum: Dictionary; contains the parameters to be summed.\n
        name_of_sum: String; used to identify the sum being done.\n
        args: String(s); the attributes to be summed.

    Returns:
        The passed dictionary updated to include a new 'name_of_sum' parameter that sums the passed args for each dictionary key.

    """
    print(f'\nCalculating {name_of_sum}...')

    for key in dict_to_sum.keys():
        sum_of_costs = 0
        # note that some key, value pairs lack some data (e.g., ft=1 has no DEF cost) so the try/except addresses that
        for arg in args:
            try:
                sum_of_costs += dict_to_sum[key][arg]
            except:
                pass
        dict_to_sum[key].update({f'{name_of_sum}': sum_of_costs})

    return dict_to_sum
