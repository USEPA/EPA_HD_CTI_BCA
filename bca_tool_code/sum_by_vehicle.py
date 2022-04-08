

def calc_sum_of_costs(settings, name_of_sum, *args):
    """

    Parameters:
        settings: The SetInputs class.
        name_of_sum: String; used to identify the sum being done.\n
        args: String(s); the attributes to be summed.

    Returns:
        Updates the fleet dictionary to include a new 'name_of_sum' parameter that sums the passed args.

    """
    print(f'\nCalculating {name_of_sum}...')

    for key in settings.fleet_cap._data.keys():
        sum_of_costs = 0
        for arg in args:
            sum_of_costs += settings.fleet_cap.get_attribute_value(key, arg)
        update_dict = {f'{name_of_sum}': sum_of_costs}

        settings.fleet_cap.update_dict(key, update_dict)
