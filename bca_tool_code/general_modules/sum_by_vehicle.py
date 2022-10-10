

def calc_sum_of_costs(key, data_dict, *args):
    """

    Parameters:
        key: tuple; the key of the passed data_dict that contains needed attributes.\n
        data_dict: dictionary; the data.\n
        args: str(s); the attributes to be summed.

    Returns:
        The sum of the passed args.

    """
    sum_of_args = 0
    for arg in args:
        sum_of_args += data_dict[key][arg]

    return sum_of_args
