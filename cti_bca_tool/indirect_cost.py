"""
indirect_cost.py

Contains the IndirectCost class and the IndirectCostScalers class.

"""

import pandas as pd


class IndirectCost:
    """

    The IndirectCost class takes a DataFrame of direct costs and applies markups as provided by the merge_markups_and_directcosts method
    and provided in the markup_factors list.

    :param directcosts_df: A DataFrame of all direct manufacturing costs, year-over-year for all vehicles and alternatives.
    :param markups: A DataFrame of the indirect cost markup factors by fuelTypeID.
    """
    def __init__(self, directcosts_df, markups):
        self.directcosts_df = directcosts_df
        self.markups = markups

    def markup_factors(self):
        """

        :return: A list of the markup factors included in the indirect cost input file (excluding "IndirectCost").
        """
        return [item for item in self.markups['Markup_Factor'].unique() if 'Indirect' not in item]

    def markup_factors_with_scalers(self):
        """

        :return: A list of the markup factors that are to be scaled according to the BCA Inputs scale_indirect_costs_by entry.
        """
        df = pd.DataFrame(self.markups.loc[self.markups['Scaler'] == 'Y', 'Markup_Factor'])
        return [item for item in df['Markup_Factor'].unique() if 'Indirect' not in item]

    def merge_markups_and_directcosts(self, markups, *args):
        """

        :param markups: A DataFrame of indirect cost markup factors.
        :param args: Metrics for merging.
        :return: A DataFrame of markup factors merged on the identifier columns of the direct costs DataFrame.
        """
        merge_metrics = [arg for arg in args]
        for markup_factor in self.markup_factors():
            temp = pd.DataFrame(markups.loc[markups['Markup_Factor'] == markup_factor])
            self.directcosts_df = self.directcosts_df.merge(temp, on=merge_metrics, how='left')
            self.directcosts_df.rename(columns={'Value': markup_factor}, inplace=True)
            self.directcosts_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return self.directcosts_df

    def get_markups(self, fueltype_markups):
        """

        :param markups: A DataFrame of indirect cost markup factors.
        :param args: Metrics for merging.
        :return: A DataFrame of markup factors merged on the identifier columns of the direct costs DataFrame.
        """
        for markup_factor in self.markup_factors():
            temp = pd.DataFrame(fueltype_markups.loc[fueltype_markups['Markup_Factor'] == markup_factor])
            temp.reset_index(drop=True, inplace=True)
            self.directcosts_df.insert(len(self.directcosts_df.columns), markup_factor, temp.at[0, 'Value'])
        return self.directcosts_df

    def merge_markup_scalers(self, alt_rc_ft_scalers, *args):
        """

        :param alt_rc_ft_scalers:
        :param args:
        :return: The passed DataFrame into which the markup scaling factors (for those markups with scaling factors) have been merged.
        """
        merge_metrics = [arg for arg in args]
        for markup_factor in self.markup_factors_with_scalers():
            temp = pd.DataFrame(alt_rc_ft_scalers.loc[alt_rc_ft_scalers['Markup_Factor'] == markup_factor])
            self.directcosts_df = self.directcosts_df.merge(temp[['yearID', 'Value']], on=merge_metrics, how='left')
            self.directcosts_df.rename(columns={'Value': f'{markup_factor}_scaler'}, inplace=True)
            # self.directcosts_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return self.directcosts_df

    # def get_markup_scalers(self, alt_rc_ft_scalers):
    #     """
    #
    #     :param alt_rc_ft_scalers:
    #     :return:
    #     """
    #     for markup_factor in self.markup_factors_with_scalers():
    #         temp = pd.DataFrame(alt_rc_ft_scalers.loc[alt_rc_ft_scalers['Markup_Factor'] == markup_factor])
    #         temp.reset_index(drop=True, inplace=True)
    #         self.directcosts_df.insert(len(self.directcosts_df.columns), f'{markup_factor}_scaler', temp.at[0, 'Value'])
    #     return self.directcosts_df

    def indirect_cost_unscaled(self, markups_and_scalers):
        """

        :param markups_and_scalers: A DataFrame of indirect cost markup factors & scalers in the shape of the direct cost DataFrame.
        :return: A DataFrame of indirect costs per vehicle and total costs for those indirect costs that do not scale with VMT.
        """
        temp = [item for item in self.markup_factors() if item not in self.markup_factors_with_scalers()]
        for factor in temp:
            self.directcosts_df.insert(len(self.directcosts_df.columns),
                                       f'{factor}Cost_AvgPerVeh',
                                       self.directcosts_df['DirectCost_AvgPerVeh'] * markups_and_scalers[factor])
        return self.directcosts_df

    def indirect_cost_scaled(self, merged_df, factor, vmt_share):
        """

        :param merged_df: A DataFrame of indirect cost markup factors & scalers in the shape of the direct cost DataFrame.
        :param factor: A given indirect cost factor, e.g., warranty or R&D.
        :param vmt_share: A factor established in the main inputs file to represent the percentage of warranty costs that scale with VMT (vs. age or other metric).
        :return: A DataFrame of indirect costs per vehicle and total costs with VMT scalers applied.
        """
        self.directcosts_df.insert(len(self.directcosts_df.columns),
                                   f'{factor}Cost_AvgPerVeh',
                                   self.directcosts_df['DirectCost_AvgPerVeh']
                                   * (merged_df[factor] * (1 - vmt_share) + merged_df[factor] * vmt_share * merged_df[f'{factor}_scaler']))
        return self.directcosts_df

    def indirect_cost_sum(self):
        """

        :return: A DataFrame of full tech costs with direct and indirect costs per vehicle and in total.
        """
        self.directcosts_df.insert(len(self.directcosts_df.columns),
                                   'IndirectCost_AvgPerVeh',
                                   self.directcosts_df[[f'{item}Cost_AvgPerVeh' for item in self.markup_factors()]].sum(axis=1))
        return self.directcosts_df


class IndirectCostScalers:
    """
    The IndirectCostScalers class calculates the scaling factors to be applied to indirect cost contributors. The scaling factors can be absolute
    or relative to the prior scaling factor.

    :param: input_df: A DataFrame of warranty or useful life miles and ages by optionID.
    :param identifier: String; "Warranty" or "UsefulLife" expected.
    :param period: String; "Miles" or "Ages" expected via input cell in the BCA_Inputs sheet contained in the inputs folder.
    """

    def __init__(self, input_df, identifier, period):
        """

        :param input_df: A DataFrame of warranty or useful life miles and ages by optionID.
        :param identifier: String; "Warranty" or "UsefulLife" expected.
        :param period: String; "Miles" or "Age" expected via input cell in the BCA_Inputs sheet contained in the inputs folder; this
        specifies scaling by Miles or by Age.
        """
        self.input_df = input_df
        self.identifier = identifier
        self.period = period

    def calc_scalers_absolute(self):
        """

        :return: DatFrame of scaling factors.
        """
        scaling_inputs = pd.DataFrame(self.input_df.loc[self.input_df['period'] == self.period])
        return_df = scaling_inputs.copy()
        cols = [col for col in return_df.columns if '20' in col]
        for col in cols[1:]:
            return_df[col] = return_df[col] / return_df[cols[0]]
        return_df[cols[0]] = 1.0
        return_df.insert(1, 'Markup_Factor', self.identifier)
        return return_df

    def calc_scalers_relative(self):
        """

        :return: DatFrame of scaling factors.
        """
        scaling_inputs = pd.DataFrame(self.input_df.loc[self.input_df['period'] == self.period])
        return_df = scaling_inputs.copy()
        cols = [col for col in return_df.columns if '20' in col]
        for col_number in range(1, len(cols)):
            return_df[cols[col_number]] = return_df[cols[col_number]] / scaling_inputs[cols[col_number - 1]]
        return_df[cols[0]] = 1.0
        return_df.insert(1, 'Markup_Factor', self.identifier)
        return return_df
