.. image:: https://www.epa.gov/sites/production/files/2013-06/epa_seal_verysmall.gif


Introduction
============


EPA Heavy-duty Benefit-Cost Analysis (BCA) calculation tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What is the BCA tool?
---------------------

The heavy-duty BCA tool was developed by EPA to estimate costs and benefits (only those based on a dollar-per-ton accounting) of proposed rulemaking options.
The tool is written in Python (version 3.8) and makes use of several input files that specify, for example, costs for technology expected to be added to vehicles to facilitate compliance,
vehicle populations and sales, fuel consumption, vehicle miles traveled, etc.

What are the input files?
-------------------------

The list of necessary input files contained in the "inputs" folder is:
    - BCA_General_Inputs.csv which specifies which AEO fuel prices to use, what calendar year to which to discount costs, among other parameters.
    - Input_Files.csv which specifies the specific filenames from which to read-in the necessary runtime data. A user can use different input files/filenames provided they are in the same format as the default files.
    - options.csv which specifies the number of options to be run along with an Option Name for each optionID. Note that "option" and "alternative" and "scenario" tend to be used interchangeably.
    - A MOVES or fleet file which provides inventories and VMT, etc., to support the analysis.
    - MOVES_Adjustments.csv which provides adjustments to data in the MOVES data file that might be necessary within the BCA tool. Currently, this adjusts regclass 41 diesel data to reflect engine-certs only.
    - DirectCostInputs_byRegClass_byFuelType.csv which provides the direct technology costs by Regulatory Class.
    - TechCostInputs_bySourceType_byFuelType.csv which provides the tech costs (direct plus indirect) by SourceType.
    - LearningRateScalars_byRegClass.csv which provides scalars to be applied in estimating learning effects on direct costs.
    - LearningRateScalars_bySourceType.csv which provides scalars to be applied in estimating learning effects on direct costs.
    - IndirectCostInputs_RegClass.csv which provides indirect cost markup factors applied to reg class direct costs to estimate indirect costs.
    - IndirectCostInputs_SourceType.csv which provides indirect cost markup factors applied to sourcetype direct costs to estimate indirect costs.
    - ORVR_FuelChangeInputs.csv which provides the fuel consumption impacts expected from adding onboard refueling vapor recovery systems to HD gasoline vehicles.
    - DEF_DoseRateInputs.csv which provides the diesel exhaust fluid (DEF) dosing rates expected in the baseline scenario.
    - DEF_Prices.csv which provides DEFs prices by calendar year.
    - CriteriaCostFactors.csv which provides the cost per ton of criteria emissions in the inventory (not used for the NPRM analysis).
    - Repair_and_Maintenance_Curve_Inputs.csv which provides inputs used in estimating emission repair costs.
    - UsefulLife_Inputs.csv which provides useful life miles and ages under each alternative.
    - Warranty_Inputs.csv which provides warranty miles and ages under each alternative.
    - UnitConversions.csv which provides conversion factors as needed by the tool.
    - Components_of_Selected_Petroleum_Product_Prices.csv which provides fuel prices.
    - Table_1.1.9_ImplicitPriceDeflators.csv which provides price deflators used by the tool to convert all monetary values to a consistent basis.

Runtime settings set within the BCA_General_Inputs.csv input file
-----------------------------------------------------------------

The user can specify what to run and what AEO fuel prices to use. Runtime settings consist of:
    - calculate_cap_costs where 'cap' refers to Criteria Air Pollutant and can be set to 'Y' or 'N'.
    - calculate_cap_pollution_effects which can be set to 'Y' or 'N' (the default is 'N').
    - calculate_ghg_costs where 'ghg' refers to Greenhouse Gas and can be set ot 'Y' or 'N'.
    - calculate_ghg_pollution_effects which can be set to 'Y' or 'N' (this should not be set to 'Y' since necessary inputs are not included).
    - no_action_alt which specifies the 'No action' alternative against which any delta calculation will be made (the default is 0).
    - aeo_fuel_price_case which specifies the AEO fuel price case to use and can be set to 'Reference', 'High oil price' or 'Low oil price' (the default is 'Reference').

What are the output files?
--------------------------
The output files are pretty self-explanatory by their file names.

Output files generated if calculating CAP costs are:
    - CAP_bca_tool_preamble_ria_tables.xlsx which contains pivot tables that should correspond roughly to many of the tables presented in regulatory documents (tech and operating cost tables only, not pollution costs or benefits). This file also has annualized results.
    - CAP_bca_tool_estimated_ages.csv which contains the required, calculated and estimated warranty and useful life ages.
    - CAP_bca_tool_vmt_weighted_emission_repair_cpm.csv which contains weighted cost per mile emission repair results by sourcetype/regclass/fueltype.
    - CAP_bca_tool_vmt_weighted_fuel_cpm.csv which contains weighted cost per mile fuel costs results by sourcetype/regclass/fueltype.
    - CAP_bca_tool_vmt_weighted_def_cpm.csv which contains weighted cost per mile diesel exhaust fluid costs results by sourcetype/regclass/fueltype.
    - CAP_bca_tool_repair_cpm_details.csv which contains details of calculations used to estimate repair costs per mile.
    - CAP_bca_tool_fleet_averages.csv which contains average results for all vehicles by calendar year/model year/age.
    - CAP_bca_tool_fleet_totals.csv which contains total results for all vehicles by calendar year/model year/age.

Output files generated if calculating GHG costs are:
    - GHG_bca_tool_preamble_ria_tables.xlsx which contains pivot tables that should correspond roughly to many of the tables presented in regulatory documents (tech and operating cost tables only, not pollution costs or benefits). This file also has annualized results.
    - GHG_bca_tool_vmt_weighted_fuel_cpm.csv which contains weighted cost per mile fuel costs results by sourcetype/regclass/fueltype.
    - GHG_bca_tool_fleet_averages.csv which contains average results for all vehicles by calendar year/model year/age.
    - GHG_bca_tool_fleet_totals.csv which contains total results for all vehicles by calendar year/model year/age.

A summary_log.csv is also created which contains the version number of the tool, date and time statistics for the run and input file data specific to the run.

A folder called "run_results" will be created within the specific run's output folder that contains the output files described above. A subfolder called "figures" will be created where figures are saved.
A folder called "modified_inputs" is also created which holds modified versions of the input files. Those modifications include reshaping of the input files along with conversions of the
dollar-based inputs into a consistent dollar basis.
A folder called "run_inputs" is also created which holds a direct copy/paste of all input files used for the given run (those specified in Input_Files.csv).
A folder called "code" is also created which holds a direct copy/paste of all files in the bca_tool_code package folder (i.e., the python code).

Note that outputs are saved to an outputs folder that will be created (if it does not already exist) in the parent directory of the directory in which the code resides.