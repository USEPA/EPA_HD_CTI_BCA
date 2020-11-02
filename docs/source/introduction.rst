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

The "aeo" folder should also contain a fuel prices CSV file housing any AEO cases to be run (e.g., Reference case, High oil price, etc.). The case is selected via the BCA_General_Inputs file and the
CSV file in the aeo folder must contain the desired AEO case. The file should remain as downloaded from the AEO webpage without modification. The name of the file should be:
    - Components_of_Selected_Petroleum_Product_Prices.csv

The "bea" folder should also contain a GDP price deflator CSV file. The file should remain as downloaded from the BEA webpage without modification. The name of the file should be:
    - Table_1.1.9_ImplicitPriceDeflators.csv

What are the output files?
--------------------------
The output files are pretty self-explanatory by their file names. Some are always generated while some are optional. The BCA_General_Inputs file contains a toggle to control generation of optional files & figures.

Output files always generated are:
    - preamble_ria_tables.xlsx which contains pivot tables that should correspond roughly to many of the tables presented in regulatory documents (tech and operating cost tables only, not pollution costs or benefits).
    - bca_costs_by_yearID.csv which contains data for every calendar year (yearID).
    - bca_annual.xlsx which contains benefit and cost summaries for specific calendar years as specified in the BCA_General_Inputs file.
    - bca_annualized.xlsx which contains annualized benefit and cost summaries through specific calendar years as specified in the BCA_General_Inputs file.
    - bca_npv.xlsx which contains net present value benefit and cost summaries for specific calendar years as specified in the BCA_General_Inputs file.
    - inventory_annual_IncludedModelYears.xlsx which contains annual inventory summaries for specific calendar years as specified in the BCA_General_Inputs file (for model years included in the analysis).
    - techcostAvgPerVeh.xlsx which contains average tech costs for specific model years as specified in the BCA_General_Inputs file.
    - ages.csv which contains the required, calculated and estimated warranty and useful life ages.
    - vmt_weighted_emission_repair_owner_cpm.csv which contains weighted cost per mile emission repair results by sourcetype/regclass/fueltype.
    - vmt_weighted_fuel_cpm.csv which contains weighted cost per mile fuel costs results by sourcetype/regclass/fueltype.
    - vmt_weighted_def_cpm.csv which contains weighted cost per mile diesel exhaust fluid costs results by sourcetype/regclass/fueltype.
    - summary_log.csv which contains the version number of the tool, date and time statistics for the run and input file data specific to the run.

Optional output files are:
    - bca_all_calcs.csv which contains data for every calendar year (yearID) and vehicle age (ageID) by option/sourcetype/regclass/fueltype. Generation of this file is controlled via user interaction during runtime. It can be a very large file depending on the number of alternatives.

Optional output figures are:
    - the toggle generate_emissionrepair_cpm_figures will generate a figure showing the emission repair cost/mile results for each vehicle for the model years entered. Note that there are ~50 vehicles so entering 2 model years results in ~100 figures.
    - the toggle generate_BCA_ArgsByOption_figures will generate separate high level cost results with one figure for each alternative (4 alternatives results in 4 figures).
    - the toggle generate_BCA_ArgByOptions_figures will generate separate high level cost results with one figure showing all alternatives for each individual cost metric.

A folder called "run_results" will be created within the outputs folder that contains the output files described above. If figures are generated, they will be saved to figures subfolder in run_results.
A folder called "modified_inputs" is also created which holds modified versions of the input files. Those modifications include reshaping of the input files along with conversions of the
dollar-based inputs into a consistent dollar basis.
A folder called "run_inputs" is also created which holds a direct copy/paste of all input files used for the given run.
