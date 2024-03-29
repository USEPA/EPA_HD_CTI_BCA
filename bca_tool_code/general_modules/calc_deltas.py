

def calc_deltas(settings, data_object, options):
    """
    This function calculates deltas for action alternatives relative to the no action alternative set via the General Inputs.

    Parameters:
        settings: object; the SetInputs class object. \n
        data_object: object; the fleet data object.\n
        options: object; the options object associated with the data_object.

    Returns:
        Updates the data_object dictionary with deltas relative to the no_action_alt. OptionIDs (numeric) for the deltas
        will be the alt_id followed by the no_action_alt. For example, deltas for optionID=1 relative to optionID=0 will
        have optionID=10. OptionNames will also show as 'OptionID=1_name minus OptionID=0_name'.

    """
    print('\nCalculating deltas...')

    # Note: copy data_object results dictionary because that dictionary cannot be used in the loop that follows since
    # it changes size in the loop which is a looping no-no.
    dict_for_deltas = data_object.results.copy()

    st = rc = ft = st_name = rc_name = ft_name = None
    for key, value in dict_for_deltas.items():
        vehicle_id = modelyear_id = age_id = year_id = series = None
        fleet_object_flag = None
        try:
            # for fleet dictionary deltas
            vehicle_id, option_id, modelyear_id, age_id, discount_rate = key
            st, rc, ft = vehicle_id
            st_name = dict_for_deltas[key]['sourceTypeName']
            rc_name = dict_for_deltas[key]['regClassName']
            ft_name = dict_for_deltas[key]['fuelTypeName']
            fleet_object_flag = 1
        except ValueError:
            # for annual_summary dictionary deltas
            series, option_id, year_id, discount_rate = key

        args_to_delta = [k for k, v in value.items()
                         if 'ID' not in k
                         and 'Name' not in k
                         and 'DiscountRate' not in k
                         and 'Series' not in k
                         and 'Periods' not in k]

        if option_id != settings.no_action_alt:
            delta_option_id = options.create_option_id(option_id, settings.no_action_alt)
            delta_option_name = options.create_option_name(option_id, settings.no_action_alt)

            # note that annual summary doesn't have vehicle_id data
            if fleet_object_flag:
                update_dict_key = (vehicle_id, delta_option_id, modelyear_id, age_id, discount_rate)
                update_dict = {'DiscountRate': discount_rate,
                               'yearID': modelyear_id + age_id,
                               'sourceTypeID': st,
                               'regClassID': rc,
                               'fuelTypeID': ft,
                               'optionID': delta_option_id,
                               'modelYearID': modelyear_id,
                               'ageID': age_id,
                               'optionName': delta_option_name,
                               'sourceTypeName': st_name,
                               'regClassName': rc_name,
                               'fuelTypeName': ft_name,
                               }

            else:
                update_dict_key = (series, delta_option_id, year_id, discount_rate)
                update_dict = {'optionID': delta_option_id,
                               'optionName': delta_option_name,
                               'yearID': year_id,
                               'DiscountRate': discount_rate,
                               'Series': series,
                               'Periods': 1,
                               }

            for arg in args_to_delta:
                if fleet_object_flag:
                    no_action_arg_value = dict_for_deltas[(vehicle_id, settings.no_action_alt, modelyear_id, age_id, discount_rate)][arg]
                else:
                    # this works for annual summary
                    no_action_arg_value = dict_for_deltas[(series, settings.no_action_alt, year_id, discount_rate)][arg]
                    delta_periods = dict_for_deltas[(series, settings.no_action_alt, year_id, discount_rate)]['Periods']
                    update_dict.update({'Periods': delta_periods})
                action_arg_value = dict_for_deltas[key][arg]
                delta_arg_value = action_arg_value - no_action_arg_value
                update_dict.update({arg: delta_arg_value})

            data_object.update_object_dict(update_dict_key, update_dict)


def calc_deltas_weighted(settings, dict_for_deltas, options):
    """
    This function calculates deltas for action alternatives relative to the passed no action alternative specifically
    for the weighted cost per mile dictionaries.

    Parameters:
        settings: object; the SetInputs class object. \n
        dict_for_deltas: Dictionary; contains values for calculating deltas.
        options: object; the options object associated with the data_object.

    Returns:
        An updated dictionary containing deltas relative to the no_action_alt. OptionIDs (numeric) for the deltas will
        be the option_id followed by the no_action_alt. For example, deltas for optionID=1 relative to optionID=0 would
        have optionID=10.

    Note:
        There is no age_id or discount rate in the key for the passed weighted dictionaries; this function was not used for the HD2027 FRM so may not work properly.

    """
    print('\nCalculating weighted deltas...')

    update_dict = dict()
    for key in dict_for_deltas:
        vehicle_id, option_id, modelyear_id = key

        id_args = [k for k, v in dict_for_deltas[key].items() if 'ID' in k or 'Name' in k]
        args_to_delta = [k for k, v in dict_for_deltas[key].items() if k not in id_args]

        if option_id != settings.no_action_alt:
            delta_option_id = options.create_option_id(option_id, settings.no_action_alt)
            delta_option_name = options.create_option_name(option_id, settings.no_action_alt)
            delta_dict = dict()
            for arg in args_to_delta:
                arg_value = dict_for_deltas[key][arg] - dict_for_deltas[(vehicle_id, settings.no_action_alt, modelyear_id)][arg]
                delta_dict.update({arg: arg_value})
            for arg in id_args:
                arg_value = dict_for_deltas[key][arg]
                delta_dict.update({arg: arg_value})
            delta_dict.update({'optionID': delta_option_id,
                               'optionName': delta_option_name,
                               })
            update_dict[(vehicle_id, delta_option_id, modelyear_id)] = delta_dict
    dict_for_deltas.update(update_dict)

    return dict_for_deltas
