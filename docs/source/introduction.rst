.. image:: https://www.epa.gov/sites/production/files/2013-06/epa_seal_verysmall.gif


Introduction
============


EPA Heavy-duty Clean Truck Initiative (CTI) Benefit-Cost Analysis (BCA) calculation tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What is the CTI BCA tool?
-------------------------

The CTI BCA tool was developed by EPA to estimate costs and benefits (only those based on a dollar-per-ton accounting) of the proposed CTI rulemaking options.
The tool is written in Python (version 3.8) and makes use of several input files that specify, for example, costs for technology expected to be added to vehicles to facilitate compliance,
vehicle populations and sales, fuel consumption, vehicle miles traveled, etc.

What are the input files?
-------------------------

The list of necessary input files contained in the "inputs" folder is:
    - BCA_General_Inputs.csv which specifies which AEO fuel prices to use, what calendar year to which to discount costs, the dollar basis year for all monetized values in the analysis, among other parameters.
    - Input_Files.csv which specifies the specific filenames from which to read-in the necessary runtime data. A user can use different input files/filenames provided they are in the same format as the default files.
    - options.csv which specifies the number of options to be run along with an Option Name for each optionID. Note that "option" and "alternative" and "scenario" tend to be used interchangeably.
    - A MOVES or fleet file which provides inventories and VMT, etc., to support the analysis.
    - MOVES_Adjustments.csv which provides adjustments to data in the MOVES data file that might be necessary within the BCA tool. Currently, this adjusts regclass 41 diesel data to reflect engine-certs only
    - DirectCostInputs_byRegClass_byFuelType.csv which provides the direct technology costs by Regulatory Class.
    - LearningRateScalars_byRegClass.csv which provides scalars to be applied in estimating learning effects on direct costs.
    - IndirectCostInputs_byFuelType.csv which provides indirect cost markup factors applied to direct costs to estimate indirect costs.
    - ORVR_FuelChangeInputs.csv which provides the fuel consumption impacts expected from adding onboard refueling vapor recovery systems to HD gasoline vehicles.
    - DEF_DoseRateInputs.csv which provides the diesel exhaust fluid (DEF) dosing rates expected in the baseline scenario.
    - DEF_Prices.csv which provides DEFs prices by calendar year.
    - CriteriaCostFactors.csv which provides the cost per ton of criteria emissions in the inventory (not used for the NPRM analysis).
    - Repair_and_Maintenance_Curve_Inputs.csv which provides inputs used in estimating emission repair costs.
    - UsefulLife_Inputs.csv which provides useful life miles and ages under each alternative.
    - Warranty_Inputs.csv which provides warranty miles and ages under each alternative.

Context files
-------------

The "context files" describe the context of a given run of the tool. There are two primary elements of the context: The fuel prices to use and the dollar basis of those fuel prices. The dollar basis
subsequently establishes the dollar basis for all other monetized values within a given run. This is done in-code using Implicit Price Deflators reported by the Bureau of Economic Analysis. The user
can specify a different fuel price context (e.g., high oil price) via the BCA_General_Inputs file. However, if a different set of AEO fuel prices is desired (a more recent AEO publication), then a more
recent BEA price deflator file may also be required to ensure that sufficient data are available to make all dollar basis adjustments. Note that the dollar basis of the criteria cost factors are not
adjusted by the tool.

What are the output files?
--------------------------
The output files are pretty self-explanatory by their file names.

Output files generated are:
    - cti_bca_preamble_ria_tables.xlsx which contains pivot tables that should correspond roughly to many of the tables presented in regulatory documents (tech and operating cost tables only, not pollution costs or benefits). This file also has annualized results.
    - cti_bca_estimated_ages.csv which contains the required, calculated and estimated warranty and useful life ages.
    - cti_bca_vmt_weighted_emission_repair_cpm.csv which contains weighted cost per mile emission repair results by sourcetype/regclass/fueltype.
    - cti_bca_vmt_weighted_fuel_cpm.csv which contains weighted cost per mile fuel costs results by sourcetype/regclass/fueltype.
    - cti_bca_vmt_weighted_def_cpm.csv which contains weighted cost per mile diesel exhaust fluid costs results by sourcetype/regclass/fueltype.
    - cti_bca_repair_cpm_details.csv which contains details of calculations used to estimate repair costs per mile.
    - cti_bca_fleet_averages.csv which contains average results for all vehicles by calendar year/model year/age.
    - cti_bca_fleet_totals.csv which contains total results for all vehicles by calendar year/model year/age.
    - summary_log.csv which contains the version number of the tool, date and time statistics for the run and input file data specific to the run.

A folder called "run_results" will be created within the outputs folder that contains the output files described above. A subfolder called "figures" will be created where figures are saved.
A folder called "modified_inputs" is also created which holds modified versions of the input files. Those modifications include reshaping of the input files along with conversions of the
dollar-based inputs into a consistent dollar basis.
A folder called "run_inputs" is also created which holds a direct copy/paste of all input files used for the given run.
A folder called "code" is also created which holds a direct copy/paste of all files in the cti_bca_tool package folder (i.e., the python code).

Note that outputs are saved to an outputs folder that will be created (if it does not already exist) in the parent directory of the directory in which the code resides.