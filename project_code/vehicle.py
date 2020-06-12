"""The vehicle module contains the Vehicle class along with MOVES definitions of fueltypes,
regclassess and sourcetypes."""

# define elements of the Vehicle class
fuelTypeID = {1: 'Gasoline',
              2: 'Diesel',
              3: 'CNG',
              5: 'E85-Capable',
              9: 'Electric',
              }
regClassID = {10: 'MC',
              20: 'LDV',
              30: 'LDT',
              41: 'LHD',
              42: 'LHD45',
              46: 'MHD67',
              47: 'HHD8',
              48: 'Urban Bus',
              49: 'Gliders',
              }
sourceTypeID = {0:  'NotApplicable',
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
zerogramTechID = {0: 'ICE',
                  1: 'HEV',
                  2: 'PluginHEV',
                  3: 'FuelCell',
                  }


class Vehicle:
    """
    The Vehicle class takes a vehicle tuple object consisting of 3 to 5 integers to uniquely identify
    a vehicle and return names for those vehicles.

    :param _veh: a unique vehicle object
    :type _veh: tuple of 3 to 5 integers, where the first entry is always the optionID

    Tuples of length 3 denote (alternative, regClassID, fuelTypeID).
    Tuples of length 4 denote (alternative, sourcetypeID, regClassID, fuelTypeID).
    Tuples of length 5 denote (alternative, sourcetypeID, regClassID, fuelTypeID, zgtechID).
    """

    def __init__(self, _veh):
        self._veh = _veh

    def name_regclass(self):
        """

        :return: The name of the passed vehicle in terms of regClass_fuelType.
        """
        reg_class_id = self._veh[1]
        fuel_type_id = self._veh[2]
        veh_name = regClassID[reg_class_id] + '_' + fuelTypeID[fuel_type_id]
        return veh_name

    def name_moves(self):
        """

        :return: The name of the passed vehicle in terns of sourcetype_regClass_fuelType.
        """
        source_type_id = self._veh[1]
        reg_class_id = self._veh[2]
        fuel_type_id = self._veh[3]
        veh_name = sourceTypeID[source_type_id] + '_' + regClassID[reg_class_id] + '_' + fuelTypeID[fuel_type_id]
        return veh_name
