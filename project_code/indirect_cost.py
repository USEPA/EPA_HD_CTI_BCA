import pandas as pd

# create a list of markup factors to be included
# markup_factors = ['Warranty', 'RnD', 'Other', 'Profit', 'IndirectCost']
markup_factors = ['Warranty', 'RnD', 'Other', 'Profit']
markup_factors_with_vmt_scalars = ['Warranty', 'RnD']


class IndirectCost:
    """The IndirectCost class takes a DataFrame of direct costs and applies markups as provided by the merge_markups_and_directcosts method and provided in the markups_factors list."""

    def __init__(self, _pkg_directcost):
        self._pkg_directcost = _pkg_directcost

    def merge_markups_and_directcosts(self, _markups, _column_list_for_merge):
        """

        :param _markups: A DataFrame of indirect cost markup factors.
        :param _column_list_for_merge: The identifier columns in the direct cost DataFrame.
        :return: A DataFrame of markup factors merged on the identifier columns of the direct costs DataFrame.
        """
        merged_df = pd.DataFrame(self._pkg_directcost, columns=_column_list_for_merge)
        for markup_factor in markup_factors:
            temp = pd.DataFrame(_markups.loc[_markups['Markup_Factor'] == markup_factor])
            merged_df = merged_df.merge(temp, on='fuelTypeID', how='left')
            merged_df.rename(columns={'Value': markup_factor}, inplace=True)
            merged_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return merged_df

    def merge_vmt_scalars(self, _vmt_scalars, _column_list_for_merge):
        """

        :param _vmt_scalars: A DataFrame of VMT scalars used for adjusting indirect cost markup factors based on the given alternative.
        :param _column_list_for_merge: The identifier columns in the direct cost DataFrame.
        :return: A DataFrame of markup factor scalars merged on the identifier columns of the direct costs DataFrame.
        """
        merged_df = pd.DataFrame(self._pkg_directcost, columns=_column_list_for_merge + markup_factors)
        for markup_factor in markup_factors_with_vmt_scalars:
            temp = pd.DataFrame(_vmt_scalars.loc[_vmt_scalars['Markup_Factor'] == markup_factor])
            merged_df = merged_df.merge(temp, on=_column_list_for_merge, how='left')
            merged_df.rename(columns={'Value': markup_factor + '_scalar'}, inplace=True)
            merged_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return merged_df

    def indirect_cost(self, merged_df):
        """
        This method is not currently being used.

        :param merged_df: A DataFrame of indirect cost markup factors in the shape of the direct cost DataFrame
        :return: A DataFrame of indirect costs per vehicle and total costs.
        """
        _techcost = self._pkg_directcost.copy()
        for markup_factor in markup_factors:
            _techcost.insert(len(_techcost.columns), markup_factor + 'Cost_AvgPerVeh', _techcost['DirectCost_AvgPerVeh'] * merged_df[markup_factor])
            _techcost.insert(len(_techcost.columns), markup_factor + 'Cost_TotalCost', _techcost[markup_factor + 'Cost_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost

    def indirect_cost_unscaled(self, merged_df):
        """

        :param merged_df: A DataFrame of indirect cost markup factors & scalars in the shape of the direct cost DataFrame.
        :return: A DataFrame of indirect costs per vehicle and total costs for those indirect costs that do not scale with VMT.
        """
        _techcost = self._pkg_directcost.copy()
        temp = [item for item in markup_factors if item not in markup_factors_with_vmt_scalars]
        for factor in temp:
            _techcost.insert(len(_techcost.columns), factor + 'Cost_AvgPerVeh', _techcost['DirectCost_AvgPerVeh'] * merged_df[factor])
            _techcost.insert(len(_techcost.columns), factor + 'Cost_TotalCost', _techcost[factor + 'Cost_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost

    def indirect_cost_scaled(self, merged_df, factor, vmt_share):
        """

        :param merged_df: A DataFrame of indirect cost markup factors & scalars in the shape of the direct cost DataFrame.
        :param factor: A given indirect cost factor, e.g., warranty or R&D.
        :param vmt_share: A factor established in the main inputs file to represent the percentage of warranty costs that scale with VMT (vs. age or other metric).
        :return: A DataFrame of indirect costs per vehicle and total costs with VMT scalars applied.
        """
        _techcost = self._pkg_directcost.copy()
        _techcost.insert(len(_techcost.columns), factor + 'Cost_AvgPerVeh', _techcost['DirectCost_AvgPerVeh'] * (merged_df[factor] * (1 - vmt_share) + merged_df[factor] * vmt_share * merged_df[factor + '_scalar']))
        _techcost.insert(len(_techcost.columns), factor + 'Cost_TotalCost', _techcost[factor + 'Cost_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost

    def indirect_cost_sum(self):
        """

        :return: A DataFrame of full tech costs with direct and indirect costs per vehicle and in total.
        """
        _techcost = self._pkg_directcost.copy()
        _techcost.insert(len(_techcost.columns), 'IndirectCost_AvgPerVeh', _techcost[[item + 'Cost_AvgPerVeh' for item in markup_factors]].sum(axis=1))
        _techcost.insert(len(_techcost.columns), 'IndirectCost_TotalCost', _techcost['IndirectCost_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost


class IndirectCostScalars:

    def __init__(self, input_df):
        self.input_df = input_df

    def calc_scalars_absolute(self, identifier, period):
        scaling_inputs = pd.DataFrame(self.input_df.loc[self.input_df['period'] == period])
        return_df = scaling_inputs.copy()
        cols = [col for col in return_df.columns if '20' in col]
        for col in cols[1:]:
            return_df[col] = return_df[col] / return_df[cols[0]]
        return_df[cols[0]] = 1.0
        return_df.insert(1, 'Markup_Factor', identifier)
        return return_df

    def calc_scalars_relative(self, identifier, period):
        scaling_inputs = pd.DataFrame(self.input_df.loc[self.input_df['period'] == period])
        return_df = scaling_inputs.copy()
        cols = [col for col in return_df.columns if '20' in col]
        for col_number in range(1, len(cols)):
            return_df[cols[col_number]] = return_df[cols[col_number]] / scaling_inputs[cols[col_number - 1]]
        return_df[cols[0]] = 1.0
        return_df.insert(1, 'Markup_Factor', identifier)
        return return_df
