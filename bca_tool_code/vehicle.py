# import attr


# @attr.s
class Vehicle:
    """

    Define vehicle attribute names for, sourceTypeID, regClassID, fuelTypeID.

    Parameters::
        id: The associated ID from the MOVES input file.

    Returns:
        Source type name, Regclass name, Fuel type name.

    """
    def __init__(self, id):
        self.id = id

    def fueltype_name(self):
        """

        Returns: The fuel type name for the passed ID.

        """
        fueltype_dict = {1: 'Gasoline',
                         2: 'Diesel',
                         3: 'CNG',
                         5: 'E85-Capable',
                         9: 'Electric',
                         }
        return fueltype_dict[self.id]

    def regclass_name(self):
        """

        Returns: The regclass name for the passed ID.

        """
        regclass_dict = {10: 'MC',
                         20: 'LDV',
                         30: 'LDT',
                         41: 'LHD',
                         42: 'LHD45',
                         46: 'MHD67',
                         47: 'HHD8',
                         48: 'Urban Bus',
                         49: 'Gliders',
                         }
        return regclass_dict[self.id]

    def sourcetype_name(self):
        """

        Returns: The source type name for the passed ID.

        """
        sourcetype_dict = {0: 'NotApplicable',
                           11: 'Motorcycles',
                           21: 'Passenger Cars',
                           31: 'Passenger Trucks',
                           32: 'Light Commercial Trucks',
                           41: 'Other Buses',
                           42: 'Transit Buses',
                           43: 'School Buses',
                           51: 'Refuse Trucks',
                           52: 'Short-Haul Single Unit Trucks',
                           53: 'Long-Haul Single Unit Trucks',
                           54: 'Motor Homes',
                           61: 'Short-Haul Combination Trucks',
                           62: 'Long-Haul Combination Trucks',
                           }
        return sourcetype_dict[self.id]


def vehicle_name(settings, options_dict, dict_of_vehicles):
    """

    Args:
        settings: The SetInputs class.
        options_dict: A dictionary of option ID numbers and associated names.
        dict_of_vehicles: A dictionary containing a key of vehicle tuples.

    Returns: The passed dictionary with new attributes identifying the vehicle based on the vehicle tuples (keys).

    Note:
         The calc_deltas function added option names for the deltas so this function maintains option names for
         any keys that are deltas.

    """
    no_action_name = options_dict[settings.no_action_alt]['OptionName']
    for key in dict_of_vehicles.keys():
        vehicle, alt = key[0], key[1]
        st, rc, ft = vehicle
        if alt > len(options_dict):
            action_alt = alt / 10
            action_name = options_dict[action_alt]['OptionName']
            option_name = f'{action_name}_minus_{no_action_name}'
        else: option_name = options_dict[alt]['OptionName']
        sourcetype_name = Vehicle(st).sourcetype_name()
        regclass_name = Vehicle(rc).regclass_name()
        fueltype_name = Vehicle(ft).fueltype_name()
        dict_of_vehicles[key].update({'optionID': alt,
                                      'sourceTypeID': st,
                                      'regClassID': rc,
                                      'fuelTypeID': ft,
                                      'OptionName': option_name,
                                      'sourceTypeName': sourcetype_name,
                                      'regClassName': regclass_name,
                                      'fuelTypeName': fueltype_name,
                                      })
    return dict_of_vehicles
