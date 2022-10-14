from sys import exit

from bca_tool_code.general_modules.vehicle import Vehicle


class Fleet:

    def __init__(self):
        self.sales_by_start_year = dict() # stores sales and cumulative sales per implementation start year
        self.vehicles = list()
        self.vehicles_age0 = list()
        self.vehicles_ft2 = list()
        self.vehicles_no_action = list()
        self.typical_vmt_dict = dict() # used for estimating ages at certain events (see estimated_age_at_event module)

    def create_vehicles(self, no_action_alt, options):
        """

        Parameters:
            no_action_alt: int; the no-action option_id number.
            options: object; an object of the Options class.

        Returns:
            Nothing but it creates vehicle objects and lists of vehicle objects.

        """
        print('Creating vehicle objects...')
        for index, row in Vehicle.vehicle_df.iterrows():
            vehicle = Vehicle()
            vehicle.year_id = int(row['year_id'])
            vehicle.sourcetype_id = int(row['sourcetype_id'])
            vehicle.sourcetype_name = vehicle.get_sourcetype_name()
            vehicle.regclass_id = int(row['regclass_id'])
            vehicle.regclass_name = vehicle.get_regclass_name()
            vehicle.fueltype_id = int(row['fueltype_id'])
            vehicle.fueltype_name = vehicle.get_fueltype_name()
            vehicle.modelyear_id = int(row['modelyear_id'])
            vehicle.age_id = int(row['age_id'])
            vehicle.option_id = int(row['option_id'])
            vehicle.engine_id = vehicle.set_engine_id()
            vehicle.vehicle_id = vehicle.set_vehicle_id()
            vehicle.option_name = options.get_option_name(vehicle.option_id)
            vehicle.thc_ustons = row['thc_ustons']
            vehicle.co_ustons = row['co_ustons']
            vehicle.nox_ustons = row['nox_ustons']
            vehicle.pm25_exhaust_ustons = row['pm25_exhaust_ustons']
            vehicle.pm25_brakewear_ustons = row['pm25_brakewear_ustons']
            vehicle.pm25_tirewear_ustons = row['pm25_tirewear_ustons']
            vehicle.pm25_ustons = row['pm25_ustons']
            vehicle.voc_ustons = row['voc_ustons']
            vehicle.vpop = row['vpop']
            vehicle.vmt = row['vmt']
            vehicle.vmt_per_veh = row['vmt_per_veh']
            vehicle.odometer = row['odometer']
            vehicle.gallons = row['gallons']

            self.vehicles.append(vehicle)
            if vehicle.age_id == 0:
                self.vehicles_age0.append(vehicle)
            if vehicle.fueltype_id == 2:
                self.vehicles_ft2.append(vehicle)
            if vehicle.option_id == no_action_alt:
                self.vehicles_no_action.append(vehicle)

    def engine_sales(self, vehicle):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class..

        Returns:
            Nothing, but it updates the sales by start year object dictionary with engine sales data.

        """
        if vehicle.age_id != 0:
            print(f'Improper vehicle object passed to fleet.Fleet.engine_sales method.')
            exit()
        sales = 0
        key = (vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id)
        if key in self.sales_by_start_year:
            sales = self.sales_by_start_year[key]['engine_sales']
        else:
            sales = sum([
                v.vpop for v in self.vehicles
                if v.engine_id == vehicle.engine_id
                   and v.option_id == vehicle.option_id
                   and v.modelyear_id == vehicle.modelyear_id
                   and v.age_id == 0
            ])
            update_dict = {
                'optionID': vehicle.option_id,
                'engineID': vehicle.engine_id,
                'regClassID': vehicle.regclass_id,
                'fuelTypeID': vehicle.fueltype_id,
                'modelYearID': vehicle.modelyear_id,
                'optionName': vehicle.option_name,
                'regClassName': vehicle.regclass_name,
                'fuelTypeName': vehicle.fueltype_name,
                'engine_sales': sales,
            }

            self.update_object_dict(vehicle, vehicle.engine_id, update_dict)

    def cumulative_engine_sales(self, vehicle, start_year):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.
            start_year: int; the implementation step for which cumulative sales are sought.

        Returns:
            Nothing, but it updates the sales by start year object dictionary with cumulative engine sales data.

        """
        if vehicle.age_id != 0:
            print(f'Improper vehicle object passed to fleet.Fleet.cumulative_engine_sales method.')
            exit()
        sales = sum([
            v['engine_sales'] for k, v in self.sales_by_start_year.items()
            if v['engineID'] == vehicle.engine_id
               and v['optionID'] == vehicle.option_id
               and (v['modelYearID'] >= start_year and v['modelYearID'] <= vehicle.modelyear_id)
        ])

        update_dict = {f'cumulative_engine_sales_{start_year}_std': sales}
        self.update_object_dict(vehicle, vehicle.engine_id, update_dict)

    def cumulative_vehicle_sales(self, vehicle, start_year):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.
            start_year: int; the implementation step for which cumulative sales are sought.

        Returns:
            Nothing, but it updates the sales by start year object dictionary with cumulative vehicle sales data.

        Note:
            This method is not used so may not work properly.

        """
        if vehicle.age_id != 0:
            print(f'Improper vehicle object passed to fleet.Fleet.cumulative_vehicle_sales method.')
            exit()
        sales = sum([
            v.vpop for v in self.vehicles_age0
            if v.vehicle_id == vehicle.vehicle_id
               and v.option_id == vehicle.option_id
               and (v.modelyear_id >= start_year and v.modelyear_id <= vehicle.modelyear_id)
        ])
        update_dict = {
            'optionID': vehicle.option_id,
            'vehicleID': vehicle.vehicle_id,
            'sourceTypeID': vehicle.sourcetype_id,
            'regClassID': vehicle.regclass_id,
            'fuelTypeID': vehicle.fueltype_id,
            'modelYearID': vehicle.modelyear_id,
            'optionName': vehicle.option_name,
            'sourceTypeName': vehicle.sourcetype_name,
            'regClassName': vehicle.regclass_name,
            'fuelTypeName': vehicle.fueltype_name,
            f'cumulative_vehicle_sales_{start_year}_std': sales,
        }

        self.update_object_dict(vehicle, vehicle.vehicle_id, update_dict)

    def get_typical_vmt_per_year(self, settings, vehicle):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            vehicle: object; an object of the Vehicle class.\n

        Returns:
            A single typical annual VMT/veh value for the given vehicle.

        Note:
            This function calculates a typical annual VMT/vehicle over a set number of year_ids as set via the General
            Inputs workbook. This typical annual VMT/vehicle can then be used to estimate the ages at which warranty and
            useful life will be reached. When insufficient year_ids are available -- e.g., if the typical_vmt_thru_ageID
            is set to >5 year_ids and the given vehicle is a MY2041 vintage vehicle and the fleet input file contains data
            only thru CY2045, then insufficient data exist to calculate the typical VMT for that vehicle -- the typical VMT
            for that vehicle will be set equal to the last prior MY vintage for which sufficient data were present.

        """
        vmt_thru_age_id \
            = int(settings.repair_and_maintenance.get_attribute_value(('typical_vmt_thru', 'age_id')))
        year_max = settings.vehicle.year_id_max
        key = vehicle.vehicle_id, vehicle.option_id, vehicle.modelyear_id

        if key in self.typical_vmt_dict:
            typical_vmt = self.typical_vmt_dict[key]

        elif vehicle.modelyear_id <= year_max and vehicle.age_id == vmt_thru_age_id:
            typical_vmt = vehicle.odometer / (vmt_thru_age_id + 1)
            self.typical_vmt_dict[key] = typical_vmt

        else:
            # Note: can't get appropriate typical VMT if modelyear+vmt_thru_age_id>year_max
            year = min(vehicle.modelyear_id, year_max - vmt_thru_age_id)
            odometer = [v.odometer for v in self.vehicles
                        if v.vehicle_id == vehicle.vehicle_id
                        and v.option_id == vehicle.option_id
                        and v.modelyear_id == year
                        and v.age_id == vmt_thru_age_id][0]
            typical_vmt = odometer / (vmt_thru_age_id + 1)
            self.typical_vmt_dict[key] = typical_vmt

        return typical_vmt

    def update_object_dict(self, vehicle, unit, update_dict):
        """

        Parameters:
            vehicle: object; an object of the Vehicle class.\n
            unit: tuple; the unit to use in the key (e.g., engine_id or vehicle_id).\n
            update_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        Note:
            The method updates an existing key having attribute_name with attribute_value.

        """
        key = unit, vehicle.option_id, vehicle.modelyear_id
        if key in self.sales_by_start_year:
            for attribute_name, attribute_value in update_dict.items():
                self.sales_by_start_year[key][attribute_name] = attribute_value

        else:
            self.sales_by_start_year.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self.sales_by_start_year[key].update({attribute_name: attribute_value})
