from bca_tool_code.general_input_modules.general_functions import read_input_file


class DollarPerTonCAP:

    """

    The DollarPerTonCAP class reads the cost factors input file and provides methods to query its contents.

    """

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        DollarPerTonCAP._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = df['yearID']
        df.set_index(key, inplace=True)

        DollarPerTonCAP._dict = df.to_dict('index')

    @staticmethod
    def get_factors(settings, year_id, *factors):
        """

        Parameters:
            settings: The SetInputs class.\n
            year_id: Numeric; the calendar year for which emission cost factors are needed.
            factors: String(s); the CAP dollar per ton factors of interest.

        Returns:
            A list of dollar per ton factors.

        Note:
            Note that the BCA_General_Inputs file contains a toggle to stipulate whether to estimate emission (pollution)
            costs or not. This function is called only if that toggle is set to 'Y' (yes). The default setting is 'N' (no).

        """
        cap_dr1 = settings.general_inputs.get_attribute_value('criteria_discount_rate_1')
        cap_dr2 = settings.general_inputs.get_attribute_value('criteria_discount_rate_2')
        factor_list = list()

        for factor in factors:
            for dr in [cap_dr1, cap_dr2]:
                factor_list.append(DollarPerTonCAP._dict[year_id][f'{factor}_{str(dr)}_USD_per_uston'])

        return factor_list
