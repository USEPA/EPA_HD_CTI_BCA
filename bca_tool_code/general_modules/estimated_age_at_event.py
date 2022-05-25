class EstimatedAge:

    def __init__(self):
        self.estimated_ages_dict = dict()
        self.identifiers = ['Warranty', 'UsefulLife']

    def calc_estimated_age(self, settings, vehicle, typical_vmt):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.\n
            typical_vmt: numeric; the typical annual VMT/vehicle over a set number of year_ids as set via the General
            Inputs file (see calc_typical_vmt_per_year function).

        Returns:
            Updates the estimated ages dictionary with the ages at which an event (e.g., warranty, useful life) will be
            reached for the given vehicle.
            Returns estimated ages for identifiers as a list.

        """
        miles_and_ages_dict = {'Warranty': settings.warranty,
                               'UsefulLife': settings.useful_life,
                               }

        return_list = list()
        for identifier in self.identifiers:
            miles_and_ages = miles_and_ages_dict[identifier]
            estimated_ages_dict_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, identifier

            required_age \
                = miles_and_ages.get_attribute_value((vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id, 'Age'),
                                                     'period_value')
            required_miles \
                = miles_and_ages.get_attribute_value((vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id, 'Miles'),
                                                     'period_value')

            if identifier == 'Warranty' and (vehicle.engine_id, vehicle.option_id) in settings.warranty_extended._dict:
                extended_miles = settings.warranty_extended.get_required_miles_with_share(vehicle)
                required_miles = max(required_miles, extended_miles)

            calculated_age = round(required_miles / typical_vmt)
            estimated_age = min(required_age, calculated_age)
            self.estimated_ages_dict[estimated_ages_dict_key] = ({
                'optionID': vehicle.option_id,
                'sourceTypeID': vehicle.sourcetype_id,
                'regClassID': vehicle.regclass_id,
                'fuelTypeID': vehicle.fueltype_id,
                'modelYearID': vehicle.modelyear_id,
                'optionName': vehicle.option_name,
                'sourceTypeName': vehicle.sourcetype_name,
                'regClassName': vehicle.regclass_name,
                'fuelTypeName': vehicle.fueltype_name,
                'identifier': identifier,
                'typical_vmt': typical_vmt,
                'required_age': required_age,
                'calculated_age': calculated_age,
                'estimated_age': estimated_age,
            })
            return_list.append(estimated_age)

        return return_list
