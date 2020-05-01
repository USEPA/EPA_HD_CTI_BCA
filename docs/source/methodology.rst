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
