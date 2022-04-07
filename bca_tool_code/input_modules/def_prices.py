from bca_tool_code.input_modules.general_functions import read_input_file
from bca_tool_code.input_modules.deflators import Deflators


class DefPrices:
    """

    The DefPrices class reads the DEF prices file and provides methods to query its contents.

    """

    _data = dict()

    @staticmethod
    def init_from_file(filepath, settings):

        DefPrices._data.clear()

        df = read_input_file(filepath, usecols=lambda x: 'Notes' not in x, index_col=0)

        df = Deflators.convert_dollars_to_analysis_basis(settings, df, 'DEF_USDperGal')

        DefPrices._data = df.to_dict('index')

    @staticmethod
    def get_price(year_id):

        return DefPrices._data[year_id]['DEF_USDperGal']
