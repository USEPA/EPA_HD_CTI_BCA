

def calc_sum_of_costs(key, data_dict, *args):
    """

    Parameters:
        key: tuple; the key of the passed data_dict that contains needed attributes.\n
        data_dict: dictionary; the data.\n
        name_of_sum: str; used to identify the sum being done.\n
        args: str(s); the attributes to be summed as name_of_sum.

    Returns:
        The sum of the passed args.

    """
    sum_of_args = 0
    for arg in args:
        sum_of_args += data_dict[key][arg]

    return sum_of_args
    # update_dict = {f'{name_of_sum}': sum_of_args}

    # data_dict[key].update(update_dict)
