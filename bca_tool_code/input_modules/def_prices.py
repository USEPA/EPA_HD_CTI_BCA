import pandas as pd

from bca_tool_code.input_modules.general_functions import read_input_file
from bca_tool_code.input_modules.deflators import Deflators


class DefPrices:
    """

    The DefPrices class reads the DEF prices file and provides methods to query its contents.

    """

    _dict = dict()
    def_prices_in_analysis_dollars = pd.DataFrame()

    @staticmethod
    def init_from_file(filepath, general_inputs):

        DefPrices._dict.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = Deflators.convert_dollars_to_analysis_basis(general_inputs, df, 'DEF_USDperGal')

        DefPrices.def_prices_in_analysis_dollars = df.copy()

        DefPrices._dict = df.to_dict('index')

    @staticmethod
    def get_price(year_id):

        return DefPrices._dict[year_id]['DEF_USDperGal']
