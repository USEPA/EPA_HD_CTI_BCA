import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file


class DefDoseRates:
    """

    The DefDoseRates class reads the DEF dose rates file and provides methods to query its contents.

    """

    _data = dict()

    @staticmethod
    def init_from_file(filepath):

        DefDoseRates._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['regClassID'], df['fuelTypeID']))
        df.set_index(key, inplace=True)

        DefDoseRates._data = df.to_dict('index')

    @staticmethod
    def get_curve_coefficients(engine):

        slope, intercept = DefDoseRates._data[engine]['slope_DEFdoserate'], \
                           DefDoseRates._data[engine]['intercept_DEFdoserate']

        return slope, intercept
