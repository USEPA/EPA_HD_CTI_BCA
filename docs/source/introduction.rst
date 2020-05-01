.. image:: https://www.epa.gov/sites/production/files/2013-06/epa_seal_verysmall.gif


Introduction
============


EPA Heavy-duty Clean Truck Initiative (CTI) Benefit-Cost Analysis (BCA) calculation tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What is the CTI BCA tool?
-------------------------

The CTI BCA tool was developed by EPA to estimate costs and benefits of the proposed CTI rulemaking options. The tool is written in Python (version 3.7) and makes use of several input files that
specify, for example, costs for technology expected to be added to vehicles to facilitate compliance, vehicle populations and sales, fuel consumption, vehicle miles traveled, etc.

What are the input files?
-------------------------

The list of necessary input files contained in the "inputs" folder is:
    - 1_RunSettings.csv which provides a means of identifying specific runs (the user can use this or ignore it, but the tool will expect to find the file)
    - BCA_General_Inputs.csv which specifies which AEO fuel prices to use, what calendar year to which to discount costs, GDP price deflators, among other parameters.
    - options.csv which specifies the number of options to be run along with an Option Name for each optionID. Note that "option" and "alternative" and "scenario" tend to be used interchangeably.
    - A MOVES or fleet file which provides inventories and VMT, etc., to support the analysis.
    - MOVES_Adjustments.csv which provides adjustments to data in the MOVES data file that might be necessary within the BCA tool. Currently, this adjusts regclass 41 diesel data to reflect engine-certs only
    - DirectCostInputs_byRegClass_byFuelType.csv which provides the direct technology costs by Regulatory Class.
    - LearningRateScalars_byRegClass.csv which provides scalars to be applied in estimating learning effects on direct costs.
    - IndirectCostInputs_byFuelType.csv which provides indirect cost markup factors applied to direct costs to estimate indirect costs.
    - ORVR_FuelChangeInputs.csv which provides the fuel consumption impacts expected from adding onboard refueling vapor recovery systems to HD gasoline vehicles.
    - DEF_DoseRateInputs.csv which provides the diesel exhaust fluid (DEF) dosing rates expected in the baseline scenario.
    - DEF_Prices.csv which provides DEFs prices by calendar year.
    - CriteriaEmissionCost_Inputs.csv which provides the cost per ton of criteria emissions in the inventory.
    - Repair_and_Maintenance_Curve_Inputs.csv which provides inputs used in estimating emission repair costs.
    - UsefulLife_Inputs.csv which provides useful life miles and ages under each alternative.
    - Warranty_Inputs.csv which provides warranty miles and ages under each alternative.

The list of optional input files contained in the "inputs" folder is:
    - DirectCostInputs_bySourcetype.csv which provides the direct technology costs for zero/low gram technologies by MOVES sourcetype. Note that this feature is not tested and may not work well.

The list of necessary input files contained in the "aeo" folder is (must have at least the case selected in the BCA_General_Inputs file):
    - Components_of_Selected_Petroleum_Product_Prices_High.csv which provides AEO fuel price estimates for the High Oil Price case.
    - Components_of_Selected_Petroleum_Product_Prices_Low.csv which provides AEO fuel price estimates for the Low Oil Price case.
    - Components_of_Selected_Petroleum_Product_Prices_Reference.csv which provides AEO fuel price estimates for the Reference Oil Price case.

What are the output files?
--------------------------
The output files are pretty self-explanatory by their file names. Some are always generated while some are optional. The BCA_General_Inputs file contains a toggle to control generation of optional files.

Output files always generated are:
    - bca_annual.xlsx which contains benefit and cost summaries for specific calendar years as specified in the BCA_General_Inputs file.
    - bca_annualized.xlsx which contains annualized benefit and cost summaries through specific calendar years as specified in the BCA_General_Inputs file.
    - bca_npv.xlsx which contains net present value benefit and cost summaries for specific calendar years as specified in the BCA_General_Inputs file.
    - inventory_annual_IncludedModelYears.xlsx which contains annual inventory summaries for specific calendar years as specified in the BCA_General_Inputs file (for model years included in the analysis).
    - techcostAvgPerVeh.xlsx which contains average tech costs for specific model years as specified in the BCA_General_Inputs file.
    - summary_log.csv which contains the version number of the tool, date and time statistics for the run and input file data specific to the run.

Optional output files are:
    - bca_costs.csv which contains data for every calendar year (yearID) and vehicle age (ageID) by sourcetype/regclass/fueltype.
    - criteria_emission_costs.csv which contains emission cost data by sourcetype/regclass/fueltype.
    - operating_costs.csv which contains operating cost data by sourcetype/regclass/fueltype.
    - techcosts.csv which contains tech costs (direct, indirect and total) by sourcetype/regclass/fueltype.
    - vmt_weighted_emission_repair_owner_cpm.csv which contains weighted cost per mile emission repair results by sourcetype/regclass/fueltype.
    - vmt_weighted_fuel_cpm.csv which contains weighted cost per mile fuel costs results by sourcetype/regclass/fueltype.
    - vmt_weighted_urea_cpm.csv which contains weighted cost per mile diesel exhaust fluid costs results by sourcetype/regclass/fueltype.

A folder call "run_results" will be created within the outputs folder that contains the output files described above.
A folder called "modified_inputs" is also created which holds modified versions of the input files. Those modifications include reshaping of the input files along with conversions of the
dollar-based inputs into a consistent dollar basis.
A folder called "run_inputs" is also created which holds a direct copy/paste of all input files used for the given run.
