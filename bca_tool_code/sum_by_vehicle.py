

def calc_sum_of_costs(data_object, name_of_sum, *args):
    """

    Parameters:
        data_object: Object; the fleet data object.\n
        name_of_sum: String; used to identify the sum being done.\n
        args: String(s); the attributes to be summed.

    Returns:
        Updates the fleet dictionary to include a new 'name_of_sum' parameter that sums the passed args.

    """
    print(f'\nCalculating {name_of_sum}...')

    for key in data_object.keys:
        sum_of_costs = 0
        for arg in args:
            sum_of_costs += data_object.get_attribute_value(key, arg)
        update_dict = {f'{name_of_sum}': sum_of_costs}

        data_object.update_dict(key, update_dict)
