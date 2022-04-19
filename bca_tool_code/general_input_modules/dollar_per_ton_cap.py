from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class DollarPerTonCAP:

    """

    The DollarPerTonCAP class reads the cost factors input file and provides methods to query contents.

    """
    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath):
        """

        Parameters:
            filepath: Path to the specified file.

        Returns:
            Reads file at filepath, creates a dictionary and other attributes specified in the class __init__.

        """
        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = df['yearID']
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.update_pathlist(filepath)

    def get_factors(self, settings, year_id, *factors):
        """

        Parameters:
            settings: object; the SetInputs class object.\n
            year_id: int; the calendar year for which emission cost factors are needed.
            factors: str(s); the CAP dollar per ton factors of interest.

        Returns:
            A list of dollar per ton factors for the passed year_id.

        Note:
            Note that the BCA_General_Inputs file contains a toggle to stipulate whether to estimate emission (pollution)
            costs or not. This function is called only if that toggle is set to 'Y' (yes). The default setting is 'N' (no).

        """
        cap_dr1 = settings.general_inputs.get_attribute_value('criteria_discount_rate_1')
        cap_dr2 = settings.general_inputs.get_attribute_value('criteria_discount_rate_2')
        factor_list = list()

        for factor in factors:
            for dr in [cap_dr1, cap_dr2]:
                factor_list.append(self._dict[year_id][f'{factor}_{str(dr)}_USD_per_uston'])

        return factor_list
