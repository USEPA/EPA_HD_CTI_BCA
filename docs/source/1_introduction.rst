.. image:: https://www.epa.gov/sites/production/files/2013-06/epa_seal_verysmall.gif


Introduction
============


EPA Heavy-duty Benefit-Cost Analysis (BCA) calculation tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What is the BCA tool?
---------------------

The heavy-duty BCA tool was developed by EPA to estimate costs and benefits (only those based on a dollar-per-ton accounting) of rulemaking options.
The tool is written in Python (tested in version 3.9) and makes use of several input files that specify, for example, costs for technology expected to be added to vehicles to facilitate compliance,
vehicle populations and sales, fuel consumption, vehicle miles traveled, etc.

What are the input files?
-------------------------

There are three primary input files that should reside in the "inputs" folder:
    - BCA_General_Inputs.csv which specifies which AEO fuel prices to use, what calendar year to which to discount costs, among other parameters.
    - Input_Files.csv which specifies the specific filenames from which to read-in the necessary input data. A user can use different input files/filenames provided they are in CSV format and structured the same way as the default files.
    - Runtime_Options.csv which specifies what to run; for example, discounting of values and calculating deltas can be turned off if not needed.

Runtime settings set within the Runtime_Options.csv input file
-----------------------------------------------------------------

The user can specify what to run via the Runtime_Options.csv file. Runtime settings consist of:
    - calculate_cap_costs where 'cap' refers to Criteria Air Pollutant and can be set to '0' or '1' (no or yes, respectively).
    - calculate_cap_pollution_effects which can be set to '0' or '1' (no or yes, respectively).
    - discount_values which can be set to '0' or '1' (no or yes, respectively).
    - calc_deltas which can be set to '0' or '1' (no or yes, respectively).

What are the output files?
--------------------------
The output files are pretty self-explanatory by their file names and vary by settings in the Runtime_Options.csv file.

Output files generated if calculating CAP costs are:
    - 'all_costs' which contains results for all vehicles by calendar year/model year/age.
    - 'annual_summary' which contains annual sums, present values and annualized values using the 'all_costs' data.
    - 'package_costs_by_implementation_year' which contains package costs year-over-year associated with each standard implementation step.
    - 'sales_by_implementation_year' which contains sales year-over-year associated with each standard implementation step.
    - 'required_and_estimated_ages' which contains the required, calculated and estimated warranty and useful life ages.
    - 'indirect_cost_details' which contains details surrounding indirect cost estimates.
    - 'repair_cost_details' which contains details of calculations used to estimate repair costs and warranty costs.
    - 'summary_log' which contains the version number of the tool, date and time statistics for the run and input file data specific to the run.

A folder called "run_results" will be created within the specific run's output folder that contains the output files described above. A subfolder called "figures" will be created where figures are saved.
A folder called "modified_inputs" is also created which holds modified versions of the input files. Those modifications include reshaping of the input files along with conversions of the
dollar-based inputs into a consistent dollar basis.
A folder called "run_inputs" is also created which holds a direct copy/paste of all input files used for the given run (those specified in Input_Files.csv).
A folder called "code" is also created which holds a direct copy/paste of all files in the bca_tool_code package folder (i.e., the python code).

Note that outputs are saved to an outputs folder that will be created (if it does not already exist) in the parent directory of the directory in which the code resides.