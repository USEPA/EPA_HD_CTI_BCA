import pandas as pd

from bca_tool_code.vehicle import Vehicle


class Vehicles:

    def __init__(self):
        self.sales_and_cumulative_sales_by_step = dict() # stores sales and cumulative sales per implementation step
        self.vehicles = list()
        self.vehicles_age0 = list()
        self.vehicles_ft2 = list()

    # @staticmethod
    def create_cap_vehicles(self, options):
        print('Creating CAP vehicle objects...')
        for index, row in Vehicle._vehicle_df.iterrows():
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
            vehicle.nox_ustons = row['nox_ustons']
            vehicle.pm25_exhaust_ustons = row['pm25_exhaust_ustons']
            vehicle.pm25_brakewear_ustons = row['pm25_brakewear_ustons']
            vehicle.pm25_tirewear_ustons = row['pm25_tirewear_ustons']
            vehicle.pm25_ustons = row['pm25_ustons']
            vehicle.voc_ustons = row['voc_ustons']
            vehicle.vmt = row['vmt']
            vehicle.cumulative_vmt = 0
            vehicle.vpop = row['vpop']
            vehicle.gallons = row['gallons']

            self.vehicles.append(vehicle)
            if vehicle.age_id == 0:
                self.vehicles_age0.append(vehicle)
            if vehicle.fueltype_id == 2:
                self.vehicles_ft2.append(vehicle)

    def create_ghg_vehicles(self, options):
        print('Creating GHG vehicle objects...')
        for index, row in Vehicle._vehicle_df.iterrows():
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
            vehicle.co2_ustons = row['co2_ustons']
            vehicle.ch4_ustons = row['ch4_ustons']
            vehicle.n2o_ustons = row['n2o_ustons']
            vehicle.so2_ustons = row['so2_ustons']
            vehicle.energy_kj = row['energy_kj']
            vehicle.vmt = row['vmt']
            vehicle.cumulative_vmt = 0
            vehicle.vpop = row['vpop']
            vehicle.vpop_with_tech = row['vpop_with_tech']
            vehicle.gallons = row['gallons']

            self.vehicles.append(vehicle)
            if vehicle.age_id == 0:
                self.vehicles_age0.append(vehicle)

    def engine_sales(self, vehicle):
        """
        engine sales by model year
        Args:
            vehicle: object; a vehicle object of the Vehicles class.

        Returns:

        """
        sales = 0
        # vehicles = settings.cap_vehicles_list
        key = (vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id)
        if key in self.sales_and_cumulative_sales_by_step:
            sales = self.sales_and_cumulative_sales_by_step[key]['engine_sales']
        else:
            sales = sum([
                v.vpop for v in self.vehicles
                if v.engine_id == vehicle.engine_id
                   and v.option_id == vehicle.option_id
                   and v.modelyear_id == vehicle.modelyear_id
                   and v.age_id == 0
            ])
            update_dict = {'engine_id': vehicle.engine_id,
                           'option_id': vehicle.option_id,
                           'modelyear_id': vehicle.modelyear_id,
                           'engine_sales': sales}
            self.update_object_dict(vehicle, update_dict)

        return sales

    def cumulative_engine_sales(self, vehicle, cost_step):
        """
        cumulative engine sales in modelyear_id by implementation step
        Args:
            vehicle: object; a vehicle object of the Vehicles class.
            cost_step: int or str; the implementation step for which cumulative sales are sought.

        Returns:
            The cumulative sales of engines equipped in vehicle through its model year and for the given implementation
            step.
            Updates the object dictionary with the cumulative sales.

        """
        cost_step = pd.to_numeric(cost_step)
        # sales = 0
        # vehicles = settings.cap_vehicles_list
        # key = (vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id)
        # if key in self.sales_and_cumsales_by_start_year:
        #     if f'cumulative_engine_sales_{cost_step}' in self.sales_and_cumsales_by_start_year:
        #         sales = self.sales_and_cumsales_by_start_year[key][f'cumulative_engine_sales_{cost_step}']
        # else:
        sales = sum([
            v['engine_sales'] for k, v in self.sales_and_cumulative_sales_by_step.items()
            if v['engine_id'] == vehicle.engine_id
               and v['option_id'] == vehicle.option_id
               and (v['modelyear_id'] >= cost_step and v['modelyear_id'] <= vehicle.modelyear_id)
        ])

        update_dict = {f'cumulative_engine_sales_{cost_step}': sales}
        self.update_object_dict(vehicle, update_dict)

        return sales

    def cumulative_vehicle_vmt(self, vehicle):
        """
        cumulative vehicle vmt in modelyear_id by implementation step
        Args:
            vehicle: object; a vehicle object of the Vehicles class.

        Returns:
            The cumulative vmt of vehicle since age_id=0.
            Updates the object dictionary with the cumulative sales.

        """
        sales = 0
        # vehicles = settings.cap_vehicles_list
        # key = (vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id)
        vmt = sum([
            v.vmt for v in self.vehicles
            if v.vehicle_id == vehicle.vehicle_id
               and v.option_id == vehicle.option_id
               and v.modelyear_id == vehicle.modelyear_id
               and v.age_id <= vehicle.age_id
        ])

        vehicle.cumulative_vmt = vmt
        # update_dict = {f'cumulative_vmt': vmt}
        # self.update_object_dict(vehicle, update_dict)
        # self._dict[key][f'cumulative_engine_sales_{cost_step}'] = sales

        return vmt

    # def calc_avg_package_cost_per_step(self, settings, vehicle, cost_step):
    #     """
    #
    #     Parameters:
    #         settings: object; the SetInputs class object.
    #
    #     Returns:
    #         Updates the sales object dictionary to include the year-over-year package costs, including learning
    #         effects, associated with each cost step.
    #
    #     """
    #     learning_rate = pd.to_numeric(settings.general_inputs.get_attribute_value('learning_rate'))
    #     costs_object = settings.regclass_costs
    #     scalers_object = settings.regclass_learning_scalers
    #
    #     engine_id, option_id, modelyear_id = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
    #     key = (engine_id, option_id, modelyear_id)
    #     cost_step = pd.to_numeric(cost_step)
    #
    #     pkg_cost = pkg_cost_learned = 0
    #
    #     if modelyear_id < cost_step:
    #         pass
    #     else:
    #         sales_year1 \
    #             = settings.cap_vehicles.engine_sales(settings, engine_id, option_id, modelyear_id)
    #
    #         cumulative_sales \
    #             = settings.cap_vehicles.cumulative_engine_sales(settings, engine_id, option_id, modelyear_id, cost_step)
    #
    #         pkg_cost = costs_object.get_cost((engine_id, option_id), cost_step)
    #         seedvolume_factor = scalers_object.get_seedvolume_factor(engine_id, option_id)
    #
    #         pkg_cost_learned = pkg_cost \
    #                            * (((cumulative_sales + (sales_year1 * seedvolume_factor))
    #                                / (sales_year1 + (sales_year1 * seedvolume_factor))) ** learning_rate)
    #
    #     update_dict = {f'cost_per_vehicle_{cost_step}': pkg_cost_learned}
    #
    #     settings.cap_vehicles.update_object_dict(key, update_dict)

    def update_object_dict(self, vehicle, update_dict):
        """

        Parameters:
            vehicle: object; a vehicle object of the Vehicles class.\n
            input_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Updates the object dictionary with each attribute updated with the appropriate value.

        Note:
            The method updates an existing key having attribute_name with attribute_value.

        """
        key = vehicle.engine_id, vehicle.option_id, vehicle.modelyear_id
        if key in self.sales_and_cumulative_sales_by_step:
            for attribute_name, attribute_value in update_dict.items():
                self.sales_and_cumulative_sales_by_step[key][attribute_name] = attribute_value

        else:
            self.sales_and_cumulative_sales_by_step.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self.sales_and_cumulative_sales_by_step[key].update({attribute_name: attribute_value})
