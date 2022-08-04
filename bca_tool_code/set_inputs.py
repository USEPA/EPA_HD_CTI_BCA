import pandas as pd
from time import time
from datetime import datetime

from bca_tool_code.set_paths import SetPaths
from bca_tool_code.general_input_modules.input_files import InputFiles
from bca_tool_code.general_input_modules.runtime_options import RuntimeOptions
from bca_tool_code.general_input_modules.general_inputs import GeneralInputs
from bca_tool_code.general_input_modules.deflators import Deflators
from bca_tool_code.general_input_modules.fuel_prices import FuelPrices
from bca_tool_code.general_input_modules.def_prices import DefPrices
from bca_tool_code.general_input_modules.markups import Markups
from bca_tool_code.general_input_modules.warranty import Warranty
from bca_tool_code.general_input_modules.warranty_extended import WarrantyExtended
from bca_tool_code.general_input_modules.warranty_base_costs import BaseWarrantyCosts
from bca_tool_code.general_input_modules.warranty_new_tech_adj_factor import WarrantyNewTechAdj
from bca_tool_code.general_input_modules.useful_life import UsefulLife
from bca_tool_code.general_input_modules.average_speed import AverageSpeed
from bca_tool_code.general_input_modules.cost_factors import CostFactors
# from bca_tool_code.general_input_modules.dollar_per_ton_cap import DollarPerTonCAP
from bca_tool_code.general_input_modules.options import Options
from bca_tool_code.general_input_modules.moves_adjustments import MovesAdjustments

from bca_tool_code.general_modules.vehicle import Vehicle
from bca_tool_code.general_modules.fleet import Fleet
from bca_tool_code.general_modules.estimated_age_at_event import EstimatedAge
from bca_tool_code.general_modules.annual_summary import AnnualSummary

from bca_tool_code.general_input_modules.piece_costs import PieceCosts
from bca_tool_code.general_input_modules.tech_penetrations import TechPenetrations

from bca_tool_code.engine_input_modules.engine_learning_scalers import EngineLearningScalers
from bca_tool_code.vehicle_input_modules.vehicle_learning_scalers import VehicleLearningScalers

from bca_tool_code.operation_input_modules.def_doserates import DefDoseRates
from bca_tool_code.operation_input_modules.orvr_fuelchanges import OrvrFuelChanges
from bca_tool_code.operation_input_modules.repair_and_maintenance import RepairAndMaintenance
from bca_tool_code.operation_input_modules.repair_calc_attribute import RepairCalcAttribute
from bca_tool_code.operation_modules.repair_cost import EmissionRepairCost

from bca_tool_code.cap_costs import CapCosts
from bca_tool_code.ghg_costs import GhgCosts


class SetInputs:
    def __init__(self):
        """

        The SetInputs class establishes the input files to use and other input settings set in the BCA_Inputs file and
        needed within the tool.

        """
        set_paths = SetPaths()
        self.start_time = time()
        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

        self.runtime_options = RuntimeOptions()
        self.runtime_options.init_from_file(
            set_paths.path_inputs / 'Runtime_Options.csv'
        )
        self.input_files = InputFiles()
        self.input_files.init_from_file(
            set_paths.path_inputs / 'Input_Files.csv'
        )
        # self.input_files.init_from_file(set_paths.path_inputs / 'TEST_Input_Files.csv')

        self.general_inputs = GeneralInputs()
        self.general_inputs.init_from_file(
            set_paths.path_inputs / self.input_files.get_filename('bca_inputs')
        )

        # determine what's being run
        self.no_action_alt = pd.to_numeric(self.general_inputs.get_attribute_value('no_action_alt'))

        self.input_files_pathlist = self.input_files.input_files_pathlist

        self.deflators = Deflators()
        self.deflators.init_from_file(
            set_paths.path_inputs / self.input_files.get_filename('deflators'),
            self.general_inputs
        )
        self.fuel_prices = FuelPrices()
        self.fuel_prices.init_from_file(
            set_paths.path_inputs / self.input_files.get_filename('fuel_prices'),
            self.general_inputs, self.deflators
        )
        self.def_prices = DefPrices()
        self.def_prices.init_from_file(
            set_paths.path_inputs / self.input_files.get_filename('def_prices'),
            self.general_inputs, self.deflators
        )

        if self.runtime_options.calc_cap_costs:
            self.options_cap = Options()
            self.options_cap.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('options_cap')
            )
            self.techpens_cap = TechPenetrations()
            self.techpens_cap.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('techpens_cap'), 'engine_id',
            )
            self.moves_adj_cap = MovesAdjustments()
            self.moves_adj_cap.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('moves_adjustments_cap')
            )
            self.cap_vehicle = Vehicle()
            self.cap_vehicle.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('fleet_cap'),
                self.options_cap, adjustments=self.moves_adj_cap
            )
            self.fleet_cap = Fleet()
            self.fleet_cap.create_cap_vehicles(self.no_action_alt, self.options_cap)

            self.engine_costs = PieceCosts()
            self.engine_costs.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('engine_costs_cap'),
                'engine_id', self.general_inputs, self.deflators
            )
            self.replacement_costs = PieceCosts()
            self.replacement_costs.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('replacement_costs_cap'),
                'engine_id', self.general_inputs, self.deflators
            )
            self.engine_learning_scalers = EngineLearningScalers()
            self.engine_learning_scalers.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('engine_learning_scalers')
            )
            self.markups = Markups()
            self.markups.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('markups')
            )
            self.warranty = Warranty()
            self.warranty.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('warranty')
            )
            self.warranty_extended = WarrantyExtended()
            self.warranty_extended.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('warranty_extended')
            )
            self.warranty_base_costs = BaseWarrantyCosts()
            self.warranty_base_costs.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('base_warranty_costs'),
                self.general_inputs, self.deflators
            )
            self.warranty_new_tech_adj = WarrantyNewTechAdj()
            self.warranty_new_tech_adj.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('warranty_new_tech_adj_factor'),
            )
            self.warranty_cost_approach = self.general_inputs.get_attribute_value('warranty_cost_approach')

            self.useful_life = UsefulLife()
            self.useful_life.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('useful_life')
            )
            self.average_speed = AverageSpeed()
            self.average_speed.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('average_speed')
            )
            self.def_doserates = DefDoseRates()
            self.def_doserates.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('def_doserates')
            )
            self.orvr_fuelchanges_cap = OrvrFuelChanges()
            self.orvr_fuelchanges_cap.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('orvr_fuelchanges_cap')
            )
            self.repair_and_maintenance = RepairAndMaintenance()
            self.repair_and_maintenance.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('repair_and_maintenance'),
                self.general_inputs, self.deflators
            )
            self.repair_calc_attr = RepairCalcAttribute()
            self.repair_calc_attr.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('repair_calc_attribute')
            )
            self.emission_repair_cost = EmissionRepairCost()
            self.estimated_age = EstimatedAge()
            self.wtd_def_cpm_dict = dict()
            self.wtd_repair_cpm_dict = dict()
            self.wtd_cap_fuel_cpm_dict = dict()
            self.annual_summary_cap = AnnualSummary()

        if self.runtime_options.calc_ghg_costs:

            self.options_ghg = Options()
            self.options_ghg.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('options_ghg')
            )
            self.techpens_ghg = TechPenetrations()
            self.techpens_ghg.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('techpens_ghg'), 'vehicle_id',
            )
            self.ghg_vehicle = Vehicle()
            self.ghg_vehicle.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('fleet_ghg'),
                self.options_ghg, adjustments=None
            )
            self.fleet_ghg = Fleet()
            self.fleet_ghg.create_ghg_vehicles(self.no_action_alt, self.options_ghg)

            self.vehicle_costs = PieceCosts()
            self.vehicle_costs.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('vehicle_costs_ghg'),
                'vehicle_id', self.general_inputs, self.deflators
            )
            self.vehicle_learning_scalers = VehicleLearningScalers()
            self.vehicle_learning_scalers.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('vehicle_learning_scalers')
            )
            self.wtd_ghg_fuel_cpm_dict = dict()
            self.annual_summary_ghg = AnnualSummary()

            if self.runtime_options.calc_cap_costs:
                pass
            else:
                self.markups = Markups()
                self.markups.init_from_file(
                    set_paths.path_inputs / self.input_files.get_filename('markups')
                )
                self.warranty = Warranty()
                self.warranty.init_from_file(
                    set_paths.path_inputs / self.input_files.get_filename('warranty')
                )
                self.useful_life = UsefulLife()
                self.useful_life.init_from_file(
                    set_paths.path_inputs / self.input_files.get_filename('useful_life')
                )

        if self.runtime_options.calc_ghg_pollution:
            self.cost_factors_scc = CostFactors()
            self.cost_factors_scc.init_from_file(
                set_paths.path_inputs / self.input_files.get_filename('dollar_per_ton_scc'),
                self.general_inputs, deflators=self.deflators
            )

        if self.runtime_options.calc_cap_costs:

            # calculate year-over-year engine sales
            for vehicle in self.fleet_cap.vehicles_age0:
                self.fleet_cap.engine_sales(vehicle)

            # calculate year-over-year cumulative engine sales (for use in learning effects)
            for vehicle in self.fleet_cap.vehicles_age0:
                for start_year in self.engine_costs.standardyear_ids:
                    self.fleet_cap.cumulative_engine_sales(vehicle, start_year)

            self.cap_costs = CapCosts()

        if self.runtime_options.calc_ghg_costs:

            for vehicle in self.fleet_ghg.vehicles_age0:
                for start_year in self.vehicle_costs.standardyear_ids:
                    self.fleet_ghg.cumulative_vehicle_sales(vehicle, start_year)

            self.ghg_costs = GhgCosts()

        self.end_time_inputs = time()
        self.elapsed_time_inputs = self.end_time_inputs - self.start_time
