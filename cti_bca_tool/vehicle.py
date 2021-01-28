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
