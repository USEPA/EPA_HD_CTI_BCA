class EstimatedAge:

    def __init__(self):
        self.estimated_ages_dict = dict()

    def calc_estimated_age(self, settings, vehicle, typical_vmt, *identifiers):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.\n
            typical_vmt: numeric; the typical annual VMT/vehicle over a set number of years as set via the General Inputs
            workbook (see calc_typical_vmt_per_year function).
            identifiers: str(s); the event identifier (e.g., warranty, useful life)

        Returns:
            Updates the estimated ages dictionary with the ages at which an event (e.g., warranty, useful life) will be
            reached for the given vehicle.
            Returns estimated ages for passed identifiers as a list.

        """
        miles_and_ages_dict = {'Warranty': settings.warranty,
                               'UsefulLife': settings.useful_life,
                               }

        return_list = list()
        for identifier in identifiers:
            miles_and_ages = miles_and_ages_dict[identifier]
            estimated_ages_dict_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, identifier

            required_age \
                = miles_and_ages.get_attribute_value((vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id, 'Age'),
                                                     'period_value')
            required_miles \
                = miles_and_ages.get_attribute_value((vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id, 'Miles'),
                                                     'period_value')

            calculated_age = round(required_miles / typical_vmt)
            estimated_age = min(required_age, calculated_age)
            self.estimated_ages_dict[estimated_ages_dict_key] = ({'vehicle': vehicle.vehicle_id,
                                                                  'optionID': vehicle.option_id,
                                                                  'modelYearID': vehicle.modelyear_id,
                                                                  'identifier': identifier,
                                                                  'typical_vmt': typical_vmt,
                                                                  'required_age': required_age,
                                                                  'calculated_age': calculated_age,
                                                                  'estimated_age': estimated_age,
                                                                  })
            return_list.append(estimated_age)

        return return_list
