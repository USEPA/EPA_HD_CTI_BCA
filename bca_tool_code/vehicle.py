

class Vehicle:
    """

    Define vehicle attribute names for sourceTypeID, regClassID, fuelTypeID.

    Parameters::
        id: The associated ID from the MOVES input file.

    Returns:
        Source type name, Regclass name, Fuel type name.

    """
    def __init__(self, id=None):
        self.id = id

    def fueltype_name(self):
        """

        Returns:
            The fuel type name for the passed ID.

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

        Returns:
            The regclass name for the passed ID.

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

        Returns:
            The source type name for the passed ID.

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

    @staticmethod
    def vehicle_name(data_object=None, data_dict=None):
        """

        Parameters:
            data_object: object; the data object to be updated.\n
            data_dict: Dictionary, the dictionary to be updated.

        Returns:
            Updates the data_object dictionary or data_dict dictionary with new attributes identifying the vehicle.

        """
        if data_object:
            _dict = data_object._dict.copy()
        else:
            _dict = data_dict.copy()

        for key in _dict.keys():
            vehicle = key[0]
            if len(vehicle) == 3:
                st, rc, ft = vehicle
                sourcetype_name = Vehicle(st).sourcetype_name()
                regclass_name = Vehicle(rc).regclass_name()
                fueltype_name = Vehicle(ft).fueltype_name()
                update_dict = {'sourceTypeName': sourcetype_name,
                               'regClassName': regclass_name,
                               'fuelTypeName': fueltype_name,
                               }
            else:
                rc, ft = vehicle
                regclass_name = Vehicle(rc).regclass_name()
                fueltype_name = Vehicle(ft).fueltype_name()
                update_dict = {'regClassName': regclass_name,
                               'fuelTypeName': fueltype_name,
                               }
            if data_object:
                data_object.update_dict(key, update_dict)
            else:
                data_dict[key].update(update_dict)

    @staticmethod
    def option_name(settings, options, data_object=None, data_dict=None):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            options: object; the options class object.\n
            data_object: object; the data object to be updated.\n
            data_dict: Dictionary, the dictionary to be updated.

        Returns:
            Upates the data object dictionary with new attributes identifying the option name.

        """
        if data_object:
            _dict = data_object._dict.copy()
        else:
            _dict = data_dict.copy()

        no_action_name = options.get_option_name(settings.no_action_alt)
        for key in _dict.keys():
            alt = key[1]
            if alt > len(options._dict):
                action_alt = alt / 10
                action_name = options.get_option_name(action_alt)
                option_name = f'{action_name}_minus_{no_action_name}'
            else:
                option_name = options.get_option_name(alt)

            update_dict = {'OptionName': option_name}
            if data_object:
                data_object.update_dict(key, update_dict)
            else:
                data_dict[key].update(update_dict)
