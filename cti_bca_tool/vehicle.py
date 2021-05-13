import attr


@attr.s
class Vehicle:
    """Define vehicle attribute names for, sourceTypeID, regClassID, fuelTypeID.

    Parameters::
        id: The associated ID from the MOVES input file.

    """
    id = attr.ib()
    fueltype_dict = {1: 'Gasoline',
                     2: 'Diesel',
                     3: 'CNG',
                     5: 'E85-Capable',
                     9: 'Electric',
                     }
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

    def fueltype_name(self):
        return self.fueltype_dict[self.id]

    def regclass_name(self):
        return self.regclass_dict[self.id]

    def sourcetype_name(self):
        return self.sourcetype_dict[self.id]


def vehicle_name(settings, dict_of_vehicles):
    """

    Args:
        settings: The SetInputs class.
        dict_of_vehicles: A dictionary containing a key of vehicle tuples.

    Returns: The passed dictionary with new attributes identifying the vehicle based on the vehicle tuples (keys).

    Note:
         The calc_deltas function added option names for the deltas so this function maintains option names for
         any keys that are deltas.

    """
    no_action_name = settings.options_dict[settings.no_action_alt]['OptionName']
    for key in dict_of_vehicles.keys():
        vehicle = key[0]
        alt, st, rc, ft = vehicle
        if alt > len(settings.options_dict):
            action_alt = alt / 10
            action_name = settings.options_dict[action_alt]['OptionName']
            option_name = f'{action_name}_minus_{no_action_name}'
            # option_name = dict_of_vehicles[key]['OptionName']
        else: option_name = settings.options_dict[alt]['OptionName']
        sourcetype_name = Vehicle(st).sourcetype_name()
        regclass_name = Vehicle(rc).regclass_name()
        fueltype_name = Vehicle(ft).fueltype_name()
        dict_of_vehicles[key].update({'OptionName': option_name,
                                      'sourceTypeName': sourcetype_name,
                                      'regClassName': regclass_name,
                                      'fuelTypeName': fueltype_name,
                                      })
    return dict_of_vehicles
