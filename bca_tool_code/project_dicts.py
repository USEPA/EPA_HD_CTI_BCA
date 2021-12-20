import pandas as pd


class InputFileDict:
    def __init__(self, input_dict):
        self.input_dict = input_dict

    def create_project_dict(self, input_df, *args):
        """

        Parameters:
            input_df: DataFrame; contains data from the applicable input file.\n
            args: String(s); attributes to include in the returned dictionary key.

        Returns:
            The passed DataFrame as a dictionary with keys consisting of the passed args.

        """
        df = input_df.copy()
        cols = [arg for arg in args]
        len_cols = len(cols)
        if len_cols == 1: id = pd.Series(df[cols[0]])
        elif len_cols == 2: id = pd.Series(zip(df[cols[0]], df[cols[1]]))
        elif len_cols == 3: id = pd.Series(zip(zip(df[cols[0]], df[cols[1]]), df[cols[2]]))
        elif len_cols == 4: id = pd.Series(zip(zip(df[cols[0]], df[cols[1]], df[cols[2]]), df[cols[3]]))
        else:
            print('Improper number of args passed to function.')
        df.insert(0, 'id', id)
        # df.drop(columns=cols, inplace=True)
        df.set_index('id', inplace=True)

        return df.to_dict('index')

    def get_attribute_value(self, key, attribute):
        value = self.input_dict[key][attribute]
        return value


# class MilesAndAgesDict:
#     def __init__(self, input_dict):
#         self.input_dict = input_dict
#
#     def create_required_miles_and_ages_dict(self, input_df, arg):
#         """
#
#         Parameters:
#             input_df: DataFrame; provides the warranty inputs.\n
#             arg: String; represents the attribute name providing "Miles" and "Age" data (default is 'period').
#
#         Returns:
#             A single dictionary having keys equal to ((unit), alt, period) where unit is a regclass_fueltype engine
#             and period is "Age" or "Miles" and having values consistent with the passed DataFrames.
#
#         """
#         df = input_df.copy()
#         df.insert(0, 'id', pd.Series(zip(zip(df['regClassID'], df['fuelTypeID'], df[arg]), df['optionID'])))
#         df.set_index('id', inplace=True)
#         dict_return = df.to_dict('index')
#
#         return dict_return
#
#     def get_attribute_value(self, key, attribute):
#         value = self.input_dict[key][attribute]
#         return value

# class MilesAndAgesDict:
#     def __init__(self, input_dict):
#         self.input_dict = input_dict
#
#     def create_required_miles_and_ages_dict(self, warranty_inputs, usefullife_inputs, warranty_id, usefullife_id):
#         """
#
#         Parameters:
#             warranty_inputs: DataFrame; provides the warranty inputs.\n
#             usefullife_inputs: DataFrame; provides the useful life inputs.\n
#             warranty_id: String; represents the id for warranty (e.g., "Warranty.")\n
#             usefullife_id: String; represents the id for useful life (e.g., "Usefullife.")
#
#         Returns:
#             A single dictionary having keys equal to ((unit), alt, identifier, period) where unit is a regclass_fueltype engine,
#             identifier is "Warranty" or "Usefullife" and period is "Age" or "Miles" and having values consistent with the passed DataFrames.
#
#         """
#         df_all = pd.DataFrame()
#         df1 = warranty_inputs.copy()
#         df2 = usefullife_inputs.copy()
#         df1.insert(0, 'identifier', f'{warranty_id}')
#         df2.insert(0, 'identifier', f'{usefullife_id}')
#         for df in [df1, df2]:
#             df.insert(0, 'id', pd.Series(zip(zip(df['regClassID'], df['fuelTypeID']), df['optionID'], df['identifier'], df['period'])))
#             df = df[['id'] + [col for col in df.columns if '20' in col]]
#             df_all = pd.concat([df_all, df], axis=0, ignore_index=True)
#         df_all.set_index('id', inplace=True)
#         dict_return = df_all.to_dict('index')
#
#         return dict_return
#
#     def get_attribute_value(self, key, attribute):
#         value = self.input_dict[key][attribute]
#         return value


# def create_def_prices_dict(input_df):
#     """
#
#     Parameters:
#         input_df: A DataFrame of the DEF prices.
#
#     Returns:
#         A dictionary of the passed DEF prices.
#
#     """
#     df = input_df.copy()
#     df.set_index('yearID', inplace=True)
#     return df.to_dict('index')
#
#
# def create_criteria_cost_factors_dict(input_df):
#     """
#
#     Parameters:
#         input_df: A DataFrame of the criteria cost factor inputs.
#
#     Returns:
#         A dictionary of the passed DataFrame.
#
#     """
#     df = input_df.copy()
#     df.set_index('yearID', inplace=True)
#     return df.to_dict('index')


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
