class EstimatedAge:

    def __init__(self):
        self.estimated_ages_dict = dict()
        self.identifiers = ['Warranty', 'UsefulLife']
        self.warranty_basis = None

    def calc_estimated_age(self, settings, vehicle): #, typical_vmt, provisions=None):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.\n
            typical_vmt: numeric; the typical annual VMT/vehicle over a set number of year_ids as set via the General
            Inputs file (see calc_typical_vmt_per_year function).\n
            provisions: int; the option_id for which to estimate ages.

        Returns:
            Updates the estimated ages dictionary with the ages at which an event (e.g., warranty, useful life) will be
            reached for the given vehicle.

        """
        miles_and_ages_dict = {'Warranty': settings.warranty,
                               'UsefulLife': settings.useful_life,
                               }

        # option_id = provisions

        if self.warranty_basis:
            pass
        else:
            self.warranty_basis = settings.general_inputs.get_attribute_value('warranty_cost_basis')

        typical_vmt = settings.fleet.get_typical_vmt_per_year(settings, vehicle)

        avg_speed \
            = settings.average_speed.get_attribute_value(vehicle.sourcetype_id)

        operating_hours_per_year = typical_vmt / avg_speed

        # return_list = list()
        share = 0
        if (vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, 'Warranty') not in self.estimated_ages_dict:

            for identifier in self.identifiers:
                miles_and_ages = miles_and_ages_dict[identifier]
                estimated_ages_dict_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, identifier

                required_hours = calculated_age_hours = None
                required_age = required_miles = 0
                extended_miles = share = 0
                calculated_age_miles = estimated_age = estimated_miles = 0

                engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id

                required_age \
                    = miles_and_ages.get_attribute_value((engine_id, option_id, modelyear_id, 'Age'),
                                                         'period_value')
                required_miles \
                    = miles_and_ages.get_attribute_value((engine_id, option_id, modelyear_id, 'Miles'),
                                                         'period_value')
                required_hours \
                    = miles_and_ages.get_attribute_value((engine_id, option_id, modelyear_id, 'Hours'),
                                                         'period_value')

                # if identifier == 'Warranty' and vehicle.option_id != settings.no_action_alt:
                #     required_hours \
                #         = miles_and_ages.get_attribute_value((engine_id, option_id, modelyear_id, 'Hours'),
                #                                              'period_value')

                if identifier == 'Warranty' \
                        and vehicle.engine_id in settings.warranty_extended._dict \
                        and option_id == settings.no_action_alt:
                    extended_miles, share \
                        = settings.warranty_extended.get_required_miles_with_share(vehicle.engine_id)
                    extended_miles = required_miles * (1 - share) + extended_miles * share
                    required_miles = max(required_miles, extended_miles)

                # calculated_age_miles = round(required_miles / typical_vmt)
                calculated_age_miles = required_miles / typical_vmt
                estimated_age = min(required_age, calculated_age_miles)

                if required_hours:
                    calculated_age_hours = required_hours / operating_hours_per_year
                    estimated_age = min(required_age, calculated_age_miles, calculated_age_hours)

                estimated_miles = typical_vmt * estimated_age
                estimated_hours = operating_hours_per_year * estimated_age

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
                    'average_mph': avg_speed,
                    'typical_operating_hours': operating_hours_per_year,
                    'required_age': required_age,
                    'required_miles': required_miles,
                    'required_hours': required_hours,
                    'calculated_age_miles': calculated_age_miles,
                    'calculated_age_hours': calculated_age_hours,
                    'estimated_age': estimated_age,
                    'estimated_miles': estimated_miles,
                    'estimated_hours': estimated_hours,
                    'share_with_extended_warranty': share,
                })
        #         # append warranty & UL data to return_list
        #         if self.warranty_basis.__contains__('estimated'):
        #             return_list.append(estimated_age)
        #             return_list.append(estimated_miles)
        #         elif self.warranty_basis.__contains__('required'):
        #             return_list.append(required_age)
        #             return_list.append(required_miles)
        #         else:
        #             print(f'{self.warranty_basis} setting in "warranty_basis" entry of General Inputs file is not '
        #                   f'appropriate.')
        # else:
        #     for identifier in self.identifiers:
        #         estimated_ages_dict_key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id, identifier
        #
        #         if self.warranty_basis.__contains__('estimated'):
        #             age = self.estimated_ages_dict[estimated_ages_dict_key]['estimated_age']
        #             miles = self.estimated_ages_dict[estimated_ages_dict_key]['estimated_miles']
        #         else:
        #             age = self.estimated_ages_dict[estimated_ages_dict_key]['required_age']
        #             miles = self.estimated_ages_dict[estimated_ages_dict_key]['required_miles']
        #         return_list.append(age)
        #         return_list.append(miles)
        # return_list.append(share)
        # return return_list

    def get_attribute_value(self, key, attribute_name):

        return self.estimated_ages_dict[key][attribute_name]
