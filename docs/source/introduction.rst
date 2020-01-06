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
    - BCA_General_Inputs.csv which specifies which AEO fuel prices to use, what calendar year to which to discount costs, GDP price deflators, among other parameters.
    - options.csv which specifies the number of options to be run along with an Option Name for each optionID.
    - A MOVES or WAIT based filename.csv which provides inventories and VMT to support the analysis.
    - DirectCostInputs_byRegClass_byFuelType.csv which provides the direct technology costs by Regulatory Class.
    - DirectCostInputs_bySourcetype.csv which provides the direct technology costs for zero/low gram technologies by MOVES sourcetype.
    - LearningRateScalars_byRegClass.csv which provides scalars to be applied in estimating learning effects on direct costs.
    - IndirectCostInputs_byFuelType.csv which provides indirect cost markup factors applied to direct costs to estimate indirect costs.
    - IndirectCostInputs_VMTscalars_byRegClass_byFuelType.csv which provides scalars for some markup factors used in estimating indirect costs.
    - ORVR_FuelChangeInputs.csv which provides the fuel consumption impacts expected from adding onboard refueling vapor recovery systems to HD gasoline vehicles.
    - DEF_DoseRateInputs.csv which provides the diesel exhaust fluid (DEF) dosing rates expected under each option being run.
    - DEF_Prices.csv which provides DEFs prices by calendar year.
    - CriteriaEmissionCost_Inputs.csv which provides the cost per ton of criteria emissions in the inventory.

The list of necessary input files contained in the "aeo" folder is (must have at least the case selected in the BCA_General_Inputs file):
    - Components_of_Selected_Petroleum_Product_Prices_High.csv which provides AEO fuel price estimates for the High Oil Price case.
    - Components_of_Selected_Petroleum_Product_Prices_Low.csv which provides AEO fuel price estimates for the Low Oil Price case.
    - Components_of_Selected_Petroleum_Product_Prices_Reference.csv which provides AEO fuel price estimates for the Reference Oil Price case.

What are the output files?
--------------------------
The output files are pretty self-explanatory by their file names. They are:
    - bca_costs.csv which contains data for every calendary year (yearID) and vehicle age (ageID) for every MOVES sourcetype considered in the CTI BCA.
    - bca_costs_by_yearID.csv which contains data summarized by yearID.
    - bca_costs_by_regClass.csv which contains data summarized by Regulatory Class and yearID.
    - bca_costs_by_regClass_by_fuelType.csv which contains data summarized by Regulatory Class, Fuel Type and year ID.
    - bca_costs_by_sourcetype.csv which contains data summarized by MOVES sourcetype and yearID.
    - bca_costs_by_sourcetype_by_fueltype.csv which contains data summarized by MOVES sourcetype, fuel type and yearID.
    - techcosts.csv which contains tech costs (direct, indirect and total) for each Regulatory Class and MOVES sourcetype by yearID.
    - summary_log.csv which contains the version number of the tool along with date and time statistics for the run.

    - NEED TO FLESH OUT THIS LIST AS OUTPUT FILES CHANGE.

A folder called "modified inputs" is also created which holds modified versions of the input files. Those modifications include reshaping of the input files along with conversions of the
dollar-based inputs into a consistent dollar basis.






