Methodology
===========


General
^^^^^^^

The project folder for using the tool should contain an "inputs" folder containing necessary input files and a "bca_tool_code" folder containing the Python modules.
Optionally, a virtual environment folder may be desirable. When running the tool, the user will be asked to provide a run ID. If a run ID is entered, that run ID will be
included in the run-results folder-ID for the given run. Hitting return will use the default run ID. The tool will create an "outputs" folder within the project folder
into which all run results will be saved. A timestamp is included in any run-results folder-ID so that new results never overwrite prior results. The user can enter 'test'
at the run ID prompt. This will send outputs to a 'test' folder in the project folder.

The tool first reads inputs and input files. The specific input files to use (i.e., their filenames) must be specified in the Input_Files.csv file in the "UserEntry.csv" column. The tool then
calculates appropriate technology costs and operating costs. Once complete, these are brought together in a set of cost results
with those results saved to a run folder within the outputs folder.

Importantly, monetized values in the tool are treated as costs throughout. So a negative cost represents a savings. Also, for the most part,
everything is treated in absolute terms. So absolute costs are calculated for each scenario/option/alternative and then deltas are calculated as costs in the action alternative
case less costs in the no action, baseline case. As such, higher technology costs in an alternative case than those in the baseline case would result in positive delta costs, or increased costs.
Likewise, lower operating costs in an alternative case relative to those in the baseline case would result in negative delta costs, or decreased costs. A decrease in operating costs represents
an increase in operating savings.

Calculations and Equations
^^^^^^^^^^^^^^^^^^^^^^^^^^

This is not meant to be an exhaustive list of all equations used in the tool, but rather a list of those that are considered to be of most interest. The associated draft Regulatory Impact Analysis (RIA)
also contains explanations of calculations made.

Learning effects applied to costs
---------------------------------

In the criteria air pollutant program calculations, learning effects are applied to direct costs in "steps" which coincide with MY-based cost input columns in the DirectCostInputs_byRegClass_byFuelType file.
If that input file contains costs for two MY-based steps of implementation, then 2 steps of costs are calculated with step-1 being the first column
of cost data and step-2 being the second column. Step-2 costs must be incremental to the step-1 costs entered in the input file. Note that both steps of costs
are added to arrive at the direct costs for any given MY. Note also that direct costs are calculated for new vehicles only to represent costs
on new vehicle sales.

For step-1 and later direct costs (equations show step-1 occurring in MY2027):

.. math::
    :label: learning_step1_cap

    & DirectCost_{optionID;engine;MY} \\
    & =\small(\frac{CumulativeSales_{2027+}+Sales_{MY2027} \times SeedVolumeFactor} {Sales_{MY2027} \times (1+SeedVolumeFactor)})^{b} \times DirectCost_{optionID;engine;MY2027}

where,

- *b* = the learning rate (-0.245 in this analysis but can be changed via the BCA_General_Inputs.csv file)
- *DirectCost* = the direct manufacturing cost absent indirect costs, and where *DirectCost* in step-1 (MY2027) is the sum of individual tech costs for step-1 (MY2027) as input via the
  DirectCostInputs_byRegClass_byFuelType file
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *MY* = the model year being considered
- *engine* = a unique regclass-fueltype engine within MOVES
- *CumulativeSales* = cumulative sales of MY2027 and later engines in model year, MY, of implementation
- *SeedVolumeFactor* = 0 or greater to represent the number of years of learning already having occurred on a technology

For subsequent steps, e.g., new direct costs implemented in 2030:

.. math::
    :label: learning_step2_cap

    & DirectCost_{optionID;engine;MY} \\
    & =\small(\frac{CumulativeSales_{2030+}+Sales_{MY2030} \times SeedVolumeFactor} {Sales_{MY2030} \times (1+SeedVolumeFactor)})^{b} \times DirectCost_{optionID;engine;MY2030}

where,

- *CumulativeSales* = cumulative sales of MY2030 and later engines in model year, MY, of implementation
- *DirectCost* = marginal direct costs above those calculated for step-1 and later engines (i.e., the sum of individual tech costs for step-2 as input via the DirectCostInputs_byRegClass_byFuelType file)

In the Greenhouse Gas Program calculations, learning effects are applied to the technology costs which include both direct and indirect cost. Other than that, they are calculated
consistent with what is shown above for criteria air pollutant costs.

.. math::
    :label: learning_step1_ghg

    & TechCost_{optionID;vehicle;MY} \\
    & =\small(\frac{CumulativeSales_{2027+}+Sales_{MY2027} \times SeedVolumeFactor} {Sales_{MY2027} \times (1+SeedVolumeFactor)})^{b} \times TechCost_{optionID;vehicle;MY2027}

where,

- *b* = the learning rate (-0.245 in this analysis but can be changed via the BCA_General_Inputs.csv file)
- *TechCost* = the technology cost inclusive of indirect costs, and where *TechCost* in step-1 (MY2027) is from the TechCostInputs_bySourceType_byFuelType file
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *MY* = the model year being considered
- *vehicle* = a unique sourcetype-regclass-fueltype vehicle within MOVES
- *CumulativeSales* = cumulative sales of MY2027 and later vehicles in model year, MY, of implementation
- *SeedVolumeFactor* = 0 or greater to represent the number of years of learning already having occurred

Warranty and emission-related repair costs
------------------------------------------

Estimated warranty & useful life ages
.....................................

The estimated warranty and useful life ages are used to estimate both warranty costs and repair costs for each vehicle based on the estimated age when its warranty period will be reached and when its
useful life will be reached. These ages differ by sourcetype since sourcetypes accumulate miles at such different rates. Therefore, while a long-haul tractor might reach a 100,000 mile warranty
within its first or second year of use, a school bus could take several years to drive that number of miles. If both have a 5 year, 100,000 mile warranty, then the long-haul tractor would have an
estimated warranty age of roughly 1 year, while the school bus would have an estimated warranty age of, perhaps, 5 years. The same concepts are true for estimated useful life ages.

.. math::
    :label: estimated_warranty_age

    & EstimatedWarrantyAge_{optionID;vehicle;MY}\\
    & =\small\min(RequiredWarrantyAge_{optionID;vehicle;MY}, CalculatedWarrantyAge_{optionID;vehicle;MY})


.. math::
    :label: estimated_usefullife_age

    & EstimatedUsefulLifeAge_{optionID;vehicle;MY}\\
    & =\small\min(RequiredUsefulLifeAge_{optionID;vehicle;MY}, CalculatedUsefulLifeAge_{optionID;vehicle;MY})

where,

- *RequiredWarrantyAge* = the minimum age required by regulation at which the warranty can end
- *RequiredUsefulLifeAge* = the age required by regulation at which the useful life ends
- *CalculatedWarrantyAge* = the minimum mileage/hours required by regulation at which the warranty can end divided by the "typical" annual miles/hours driven for the given vehicle
- *CalculatedUsefulLifeAge* = the minimum mileage/hours required by regulation at which the useful life can end divided by the "typical" annual miles/hours driven for the given vehicle
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *MY* = the model year being considered
- *vehicle* = a unique sourcetype-regclass-fueltype vehicle within MOVES

Required warranty and useful life miles and ages by optionID/MY/RegClass/FuelType are controlled via input files to the tool (Warranty_Inputs.csv and
UsefulLife_Inputs.csv, respectively). “Estimated” and “Calculated” ages are calculated by the tool in-code where “Calculated” age uses MOVES sourcetype
mileage accumulations and average speeds. The "typical" annual miles driven is calculated in the tool as the cumulative miles driven divided by the number of years included
in the cumulative miles. Because vehicles tend to be driven fewer miles with age, the "typical" annual miles driven decreases with age. The file designated by the 'repair_and_maintenance' entry of Input_Files.csv should
include a setting for how many years of mileage accumulation to include (typical_vmt_thru_ageID). The default value is 6 which represents 7 years of cumulative miles.
Again, a smaller value would result in more "typical" annual miles driven and a lower calculated age, and a larger value would result in fewer "typical" annual miles driven
and a higher calculated age.

Emission-related warranty costs
...............................

The tool estimates the warranty costs for each sourcetype-regclass-fueltype vehicle in the analysis. These values are unique to each type of vehicle and to any options having
different warranty provisions.

.. math::
    :label: warranty_cost

    & WarrantyCost_{optionID;vehicle;MY}\\
    & = \small WarrantyCostPerYear \times BaseCostScaler_{engine;MY} \times EstimatedWarrantyAge_{optionID;vehicle;MY}

.. math::
    :label: base_cost_scaler

    BaseCostScaler_{engine;MY} = \frac{BaselineDMC_{NoActionOption;engine;MY}} {ReferenceDMC_{NoActionOption;HHDDE;MY}}

where,

- *WarrantyCostPerYear* = the warranty cost per engine per year of coverage set via the base_warranty_costs input file
- *DMC* = Direct manufacturing cost
- *BaselineDMC* = No-action DMC for the given engine in the given model year
- *ReferenceDMC* = No-action DMC for a diesel heavy HDE in the given model year
- *EstimatedWarrantyAge* = the estimated warranty age from equation :math:numref:`estimated_warranty_age`
- *engine* = a unique regclass-fueltype engine
- *vehicle* = a unique sourcetype-regclass-fueltype vehicle

Emission-related repair costs
.............................

The tool estimates the emission-related repair costs for each sourcetype-regclass-fueltype vehicle in the analysis. These values are unique to each type of vehicle and to any options having
different warranty and/or useful life provisions.

.. math::
    :label: in_ul_cpm

    & BetweenWarrantyAndUsefulLifeCPM_{optionID;vehicle;MY}\\
    & = \small RepairAndMaintenanceCPM \times EmissionRepairShare \times BaseCostScaler_{engine;MY}

where,

- *BetweenWarrantyAndUsefulLifeCPM* = the emission-related repair cost per mile/hour in the period between warranty and useful life
- *RepairAndMaintenanceCPM* = dollars_per_mile or dollars_per_hour value in the repair_and_maintenance input file
- *EmissionRepairShare* = EPA developed share of Maintenance and Repair costs that are emission-related (10.8%)
- *BaseCostScaler* = the base cost scaler from equation :math:numref:`base_cost_scaler`

.. math::
    :label: beyond_ul_cpm

    & BeyondUsefulLifeCPM_{optionID;vehicle;MY}\\
    & \small RepairAndMaintenance_{input} \times EmissionRepairShare \times BeyondUsefulLifeScaler_{optionID;engine;MY}

.. math::
    :label: beyond_ul_scaler

    BeyondUsefulLifeScaler_{optionID;engine;MY} = \frac{ActionDMC_{optionID;engine;MY}} {BaseDMC_{NoActionOption;engine;MY}}

where,

- *BeyondUsefulLifeCPM* = the emission-related repair cost per mile/hour in the period between beyond useful life
- *RepairAndMaintenance* = dollars_per_mile or dollars_per_hour value in the repair_and_maintenance input file
- *EmissionRepairShare* = EPA developed share of Maintenance and Repair costs that are emission-related (10.8%)
- *ActionDMC* = the given engine's DMC in the given option and model year
- *BaseDMC* = the given engine's DMC in the no-action option and model year

The emission-related repair costs are then calculated as the applicable cost per mile (or hours) multiplied by the applicable miles (or hours) in the given year.

Discounting
-----------

Present value
.............

.. math::
    :label: pv

    PV=\frac{AnnualValue_{0}} {(1+rate)^{(0+offset)}}+\frac{AnnualValue_{1}} {(1+rate)^{(1+offset)}} +⋯+\frac{AnnualValue_{n}} {(1+rate)^{(n+offset)}}

where,

- *PV* = present value
- *AnnualValue* = annual costs or annual benefits or annual net of costs and benefits
- *rate* = discount rate
- *0, 1, …, n* = the period or years of discounting
- *offset* = controller to set the discounting approach (0 means first costs occur at time=0; 1 means costs occur at time=1)

Annualized value
................

When the present value offset in equation :math:numref:`pv` equals 0:

.. math::
    :label:

    AV=PV\times\frac{rate\times(1+rate)^{n}} {(1+rate)^{(n+1)}-1}

When the present value offset in equation :math:numref:`pv` equals 1:

.. math::
    :label:

    AV=PV\times\frac{rate\times(1+rate)^{n}} {(1+rate)^{n}-1}

where,

- *AV* = annualized value of costs or benefits or net of costs and benefits
- *PV* = present value of costs or benefits or net of costs and benefits
- *rate* = discount rate
- *n* = the number of periods over which to annualize the present value


Sensitivites
^^^^^^^^^^^^

The BCA_General_Inputs file contains several inputs that can be adjusted as indicated within the file. Input values in other files can also be adjusted. It is suggested
that the structure of the input files not be changed and that the headers and names within the input files not be changed unless the user is willing to modify the Python
code in the event that changes result in errors.