Getting started
===============
Required files for using the tool can be found in the docket associated with the CTI rulemaking.

In addition, the code repository can be found at https://github.com/USEPA/EPA_HD_CTI_BCA.
Navigate to the above link and select "Clone or download" to either clone the repository to your local machine or download it as a ZIP file. Alternatively, you may wish to Fork the repo to your
local machine if you intend to suggest changes to the code via a pull request.

Setting up a Python environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Once you have the tool installed locally and have set up your python environment, you can install the packages needed to use the tool by typing the command (in a terminal window within your python environment):

::

    pip install -r requirements.txt

or,

::

    python -m pip install -r requirements.txt

Running the tool
^^^^^^^^^^^^^^^^
With the requirements installed, you should be able to run the tool by typing the command (in a terminal window within your python environment):

::

    python -m cti_bca_tool

This should create an outputs folder in your project folder (i.e., where you have placed the tool and repository), unless one has already been created, where the results of the run can be found.

Note that the tool was written in a Python 3.8 environment.

For help or questions, contact
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sherwood.todd@epa.gov
