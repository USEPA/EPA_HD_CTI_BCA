from bca_tool_code.general_functions import read_input_file


class DollarPerTonCAP:

    """

    The DollarPerTonCAP class reads the cost factors input file and provides methods to query its contents.

    """

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        DollarPerTonCAP._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = df['yearID']
        df.set_index(key, inplace=True)

        DollarPerTonCAP._data = df.to_dict('index')

    @staticmethod
    def get_factors(settings, year_id, *factors):
        """

        Parameters:
            settings: The GeneralInputs class.\n
            year_id: Numeric; the calendar year for which emission cost factors are needed.

        Returns:
            Six values - the PM25, NOx and SO2 emission cost factors (dollars/ton) for each of two different mortality estimates and each of two
            different discount rates.

        Note:
            Note that the BCA_General_Inputs file contains a toggle to stipulate whether to estimate emission (pollution)
            costs or not. This function is called only if that toggle is set to 'Y' (yes). The default setting is 'N' (no).

        """
        cap_dr1 = settings.get_attribute('criteria_discount_rate_1')
        cap_dr2 = settings.get_attribute('criteria_discount_rate_2')
        factor_list = list()

        for factor in factors:
            for dr in [cap_dr1, cap_dr2]:
                factor_list.append(DollarPerTonCAP._data[year_id][f'{factor}_{str(dr)}_USD_per_uston'])

        return factor_list
