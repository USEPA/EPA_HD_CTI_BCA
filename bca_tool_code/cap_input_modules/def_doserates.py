import pandas as pd

from bca_tool_code.general_input_modules.general_functions import read_input_file
from bca_tool_code.general_input_modules.input_files import InputFiles


class DefDoseRates:
    """

    The DefDoseRates class reads the DEF dose rates file and provides methods to query its contents.

    """

    _dict = dict()

    @staticmethod
    def init_from_file(filepath):

        DefDoseRates._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x)

        key = pd.Series(zip(df['regClassID'], df['fuelTypeID']))
        df.set_index(key, inplace=True)

        DefDoseRates._dict = df.to_dict('index')

        # update input_files_pathlist if this class is used
        InputFiles.input_files_pathlist.append(filepath)

    @staticmethod
    def get_curve_coefficients(engine):

        slope, intercept = DefDoseRates._dict[engine]['slope_DEFdoserate'], \
                           DefDoseRates._dict[engine]['intercept_DEFdoserate']

        return slope, intercept

    @staticmethod
    def get_attribute_value(engine, attribute_name):

        return DefDoseRates._dict[engine][attribute_name]
