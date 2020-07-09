Methodology
===========


General
^^^^^^^

The project folder for using the tool should contain and "inputs" folder containing necessary input files and a "project_code" folder containing the Python modules.
Optionally, a virtual environment folder may be desirable. The tool will create an "outputs" folder within the project folder into which all run results will be saved.

The tool first reads inputs and input files, then calculates appropriate technology costs, operating costs and emission costs. Once complete, these are brought together
in a set of BCA (benefit-cost analysis) results with those results saved to a run folder within the outputs folder.

Importantly, monetized values in the tool are treated as costs. Also, for the most part, everything is treated in absolute terms. So absolute costs are calculated
for each scenario/option/alternative and then deltas are calculated as costs in the alternative case less costs in the baseline case. As such, higher technology costs
in an alternative case than those in the baseline case would result in positive delta costs, or increased costs. Likewise, lower emission costs in an alternative case
relative to those in the baseline case would result in negative delta costs, or decreased costs. A decrease in emission costs represents and increase in emission benefits.


Sensitivites
^^^^^^^^^^^^

The BCA_General_Inputs file contains several inputs that can be adjusted as indicated within the file. Input values in other files can also be adjusted. It is suggested
that the structure of the input files not be changed and that the headers and names within the input files not be changed unless the user is willing to modify the Python
code in the event that changes result in errors.


Calculations and Equations
^^^^^^^^^^^^^^^^^^^^^^^^^^

This is not meant to be an exhaustive list of all equations used in the tool, but rather a list of those that are considered to be of most interest. The associated draft Regulatory Impact Analysis (RIA)
also contains explanations of calculations made.

Learning effects applied to direct costs
----------------------------------------

Learning effects are applied to direct costs in "steps" which coincide with MY-based cost input columns in the DirectCostInputs_byRegClass_byFuelType file.
If that input file contains costs for two MY-based steps of implementation, then 2 steps of costs are calculated with step-1 being the first column
of cost data and step-2 being the second column. Step-2 costs must be incremental to the step-1 costs entered in the input file. Note that both steps of costs
are added to arrive at the direct costs for any given MY. Note also that direct costs are calculated for new vehicles only to represent costs
on new vehicle sales.

For step-1 and later direct costs (equations show step-1 occurring in MY2027):

:math:`DirectCost_{optionID;vehicle;MY}\\
=(\frac{CumulativeSales_{MY}+Sales_{MY2027}
\times
SeedVolumeFactor} {Sales_{MY2027}
\times
(1+SeedVolumeFactor)})^{b}
\times
DirectCost_{optionID;vehicle;MY2027}`

where,

- *b* = the learning rate (-0.245 in this analysis but can be changed via the BCA_General_Inputs.csv file)
- *DirectCost* = the direct manufacturing cost absent indirect costs, and where *DirectCost* in step-1 (MY2027) is the sum of individual tech costs for step-1 (MY2027) as input via the
  DirectCostInputs_byRegClass_byFuelType file
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *MY* = the model year being considered
- *vehicle* = a unique regclass-fueltype vehicle within MOVES
- *CumulativeSales* = cumulative sales of MY2027 and later vehicles in year, t, of implementation
- *SeedVolumeFactor* = 0 or greater to represent the number of years of learning already having occurred on a technology

For step-2 and later direct costs (equations show step-2 occurring in MY2030):

:math:`DirectCost_{optionID;vehicle;MY}\\
=(\frac{CumulativeSales_{MY2030+}+Sales_{MY2030}
\times
SeedVolumeFactor} {Sales_{MY2030}
\times
(1+SeedVolumeFactor)})^{b}
\times
DirectCost_{optionID;vehicle;MY2030}`

where,

- *CumulativeSales* = cumulative sales of MY2030 and later vehicles in year, t, of implementation
- *DirectCost* = marginal direct costs above those calculated for step-1 and later vehicles (i.e., the sum of individual tech costs for step-2 as input via the DirectCostInputs_byRegClass_byFuelType file)


Emission repair costs
---------------------

Direct cost scalars
...................

:math:`DirectCostScalar_{optionID;vehicle;MY}=\frac{DirectCost_{optionID;vehicle;MY}} {DirectCost_{Baseline;HHDDE;MY}}`

where,

- *DirectCost* = the direct manufacturing cost absent indirect costs
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *HHDDE* = heavy heavy-duty diesel engine regulatory class
- *MY* = the model year being considered
- *vehicle* = a unique regclass-fueltype vehicle within MOVES\\

Estimated warranty & useful life ages
.....................................

:math:`EstimatedWarrantyAge_{optionID;vehicle;MY} \\
=\min(RequiredWarrantyAge_{optionID;vehicle;MY}, CalculatedWarrantyAge_{optionID;vehicle;MY})`

:math:`EstimatedUsefulLifeAge_{optionID;vehicle;MY} \\
=\min(RequiredUsefulLifeAge_{optionID;vehicle;MY}, CalculatedUsefulLifeAge_{optionID;vehicle;MY})`

where,

- *RequiredWarrantyAge* = the minimum age required by regulation at which the warranty can end
- *RequiredUsefulLifeAge* = the age required by regulation at which the useful life ends
- *CalculatedWarrantyAge* = the minimum mileage required by regulation at which the warranty can end divided by the annual miles driven for the given vehicle
- *CalculatedUsefulLifeAge* = the minimum mileage required by regulation at which the useful life can end divided by the annual miles driven for the given vehicle
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *MY* = the model year being considered
- *vehicle* = a unique sourcetype-regclass-fueltype vehicle within MOVES

Required warranty and useful life miles and ages by optionID/MY/RegClass/FuelType are controlled via input files to the tool (Warranty_Inputs.csv and
UsefulLife_Inputs.csv, respectively). “Estimated” and “Calculated” ages are calculated by the tool in-code where “Calculated” age uses MOVES sourcetype
mileage accumulations.

Cost per mile by age (for emission-related repairs)
...................................................

:math:`InWarrantyCPM_{optionID;vehicle;MY}\\
=FleetAdvantageCPM_{Year1}
\times
EmissionRepairShare
\times
DirectCostScalar_{optionID;vehicle;MY}`

:math:`AtUsefulLifeCPM_{optionID;vehicle;MY}\\
=FleetAdvantageCPM_{Year6}
\times
EmissionRepairShare
\times
DirectCostScalar_{optionID;vehicle;MY}`

:math:`MaxCPM_{optionID;vehicle;MY}\\
=FleetAdvantageCPM_{Year7}
\times
EmissionRepairShare
\times
DirectCostScalar_{optionID;vehicle;MY}`

where,

- *InWarrantyCPM* = in-warranty emission repair cost per mile
- *AtUsefulLifeCPM* = at-usefule-life emission repair cost per mile
- *MaxCPM* = the maximum emission repair cost per mile
- *optionID* = the option considered (i.e, baseline or one of the action alternatives)
- *FleetAdvantageCPMYear1* = first year cost per mile from the Fleet Advantage white paper (2.07 cents/mile in 2018 dollars)
- *FleetAdvantageCPMYear6* = year six cost per mile from the Fleet Advantage white paper (14.56 cents/mile in 2018 dollars)
- *FleetAdvantageCPMYear7* = year seven cost per mile from the Fleet Advantage white paper (19.82 cents/mile in 2018 dollars)
- *EmissionRepairShare* = EPA developed share of Fleet Advantage Maintenance and Repair costs that are emission-related (10.8%)
- *vehicle* = a unique regclass-fueltype vehicle within MOVES

Repair and maintenance cost per mile values—currently based on the Fleet Advantage whitepaper—are controlled via the “Repair_and_Maintenance_Curve_Inputs.csv”
input file to the tool.

:math:`SlopeCPM_{optionID;vehicle;MY}\\
=\frac{(AtUsefulLifeCPM_{optionID;vehicle;MY}-InWarrantyCPM_{optionID;vehicle;MY})} {(EstimatedUsefulLifeAge_{optionID;vehicle;MY}-EstimatedWarrantyAge_{optionID;vehicle;MY})}`

where,

- *SlopeCPM* = the cost per mile slope between the estimated warranty age and the estimated useful life age for a given sourcetype-regclass-fueltype vehicle
- *InWarrantyCPM* = in-warranty emission repair cost per mile
- *AtUsefulLifeCPM* = at-usefule-life emission repair cost per mile

For any given optionID/vehicle/MY where vehicle is a unique sourcetype-regclass-fueltype within MOVES, the emission-repair cost per mile (EmissionRepairCPM) at any given age would be calculated as:

When Age<=EstimatedWarrantyAge:

:math:`EmissionRepairCPM_{optionID;vehicle;MY;age}=InWarrantyCPM_{optionID;vehicle;MY}`

When EstimatedWarrantyAge<Age<=EstimatedUsefulLifeAge:

:math:`EmissionRepairCPM_{optionID;vehicle;MY;age}\\
=SlopeCPM_{optionID;vehicle;MY}
\times
(Age_{optionID;vehicle;MY}-EstimatedWarrantyAge_{optionID;vehicle;MY})\\
+InWarrantyCPM_{optionID;vehicle;MY}`

When Age>EstimatedUsefulLifeAge:

:math:`EmissionRepairCPM_{optionID;vehicle;MY;age}=MaxCPM_{optionID;vehicle;MY}`

Discounting
-----------

Present value
.............

:math:`PV=\frac{AnnualValue_{0}} {(1+rate)^{(0+offset)}}+\frac{AnnualValue_{1}} {(1+rate)^{(1+offset)}} +⋯+\frac{AnnualValue_{n}} {(1+rate)^{(n+offset)}}`

where,

- *PV* = present value
- *AnnualValue* = annual costs or annual benefits or annual net of costs and benefits
- *rate* = discount rate
- *0, 1, …, n* = the period or years of discounting
- *offset* = controller to set the discounting approach (0 means first costs occur at time=0; 1 means costs occur at time=1)

Annualized value
................

When the present value offset (above) equals 0:

:math:`AV=PV\times\frac{rate\times(1+rate)^{n}} {(1+rate)^{(n+1)}-1}`

When the present value offset (above) equals 1:

:math:`AV=PV\times\frac{rate\times(1+rate)^{n}} {(1+rate)^{n}-1}`

where,

- *AV* = annualized value of costs or benefits or net of costs and benefits
- *PV* = present value of costs or benefits or net of costs and benefits
- *rate* = discount rate
- *n* = the number of periods over which to annualize the present value
