import pandas as pd

# create a list of markup factors to be included
# markup_factors = ['Warranty', 'R_and_D', 'Other', 'Profit', 'IndirectCost']
markup_factors = ['Warranty', 'R_and_D', 'Other', 'Profit']
markup_factors_with_vmt_scalars = ['Warranty', 'R_and_D']


class IndirectCost:
    """The IndirectCost class takes a dataframe of direct costs and applies markups as provided by the merge_markups_and_directcosts method and provided in the markups_factors list."""

    def __init__(self, _pkg_directcost):
        self._pkg_directcost = _pkg_directcost

    def merge_markups_and_directcosts(self, _markups, _column_list_for_merge):
        """This method reshapes the indirect cost inputs from wide format to long format."""
        merged_df = pd.DataFrame(self._pkg_directcost, columns=_column_list_for_merge)
        for markup_factor in markup_factors:
            temp = pd.DataFrame(_markups.loc[_markups['Markup_Factor'] == markup_factor])
            merged_df = merged_df.merge(temp, on='fuelTypeID', how='left')
            merged_df.rename(columns={'Value': markup_factor}, inplace=True)
            merged_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return merged_df

    def merge_vmt_scalars(self, _vmt_scalars, _column_list_for_merge):
        merged_df = pd.DataFrame(self._pkg_directcost, columns=_column_list_for_merge + markup_factors)
        for markup_factor in markup_factors_with_vmt_scalars:
            temp = pd.DataFrame(_vmt_scalars.loc[_vmt_scalars['Markup_Factor'] == markup_factor])
            merged_df = merged_df.merge(temp, on=_column_list_for_merge, how='left')
            merged_df.rename(columns={'Value': markup_factor + '_scalar'}, inplace=True)
            merged_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return merged_df

    def indirect_cost(self, merged_df):
        _techcost = self._pkg_directcost.copy()
        for markup_factor in markup_factors:
            _techcost.insert(len(_techcost.columns), markup_factor + '_AvgPerVeh', _techcost['DirectCost_AvgPerVeh'] * merged_df[markup_factor])
            _techcost.insert(len(_techcost.columns), markup_factor + '_TotalCost', _techcost[markup_factor + '_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost

    def indirect_cost_unscaled(self, merged_df):
        _techcost = self._pkg_directcost.copy()
        temp = [item for item in markup_factors if item not in markup_factors_with_vmt_scalars]
        for factor in temp:
            _techcost.insert(len(_techcost.columns), factor + '_AvgPerVeh', _techcost['DirectCost_AvgPerVeh'] * merged_df[factor])
            _techcost.insert(len(_techcost.columns), factor + '_TotalCost', _techcost[factor + '_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost

    def indirect_cost_scaled(self, merged_df, factor, vmt_share):
        _techcost = self._pkg_directcost.copy()
        _techcost.insert(len(_techcost.columns), factor + '_AvgPerVeh', _techcost['DirectCost_AvgPerVeh'] * (merged_df[factor] * (1 - vmt_share) + merged_df[factor] * vmt_share * merged_df[factor + '_scalar']))
        _techcost.insert(len(_techcost.columns), factor + '_TotalCost', _techcost[factor + '_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost

    def indirect_cost_sum(self):
        _techcost = self._pkg_directcost.copy()
        _techcost.insert(len(_techcost.columns), 'IndirectCost_AvgPerVeh', _techcost[[item + '_AvgPerVeh' for item in markup_factors]].sum(axis=1))
        _techcost.insert(len(_techcost.columns), 'IndirectCost_TotalCost', _techcost['IndirectCost_AvgPerVeh'] * _techcost['VPOP'])
        return _techcost
