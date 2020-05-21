import pandas as pd

# create a list of markup factors to be included
markup_factors = ['Warranty', 'RnD', 'Other', 'Profit']
markup_factors_with_vmt_scalars = ['Warranty', 'RnD']


class IndirectCost:
    """
    The IndirectCost class takes a DataFrame of direct costs and applies markups as provided by the merge_markups_and_directcosts method and provided in the markup_factors list.
    """

    def __init__(self, pkg_directcost):
        self.pkg_directcost = pkg_directcost

    def merge_markups_and_directcosts(self, markups, column_list_for_merge):
        """

        :param markups: A DataFrame of indirect cost markup factors.
        :param column_list_for_merge: The identifier columns in the direct cost DataFrame.
        :return: A DataFrame of markup factors merged on the identifier columns of the direct costs DataFrame.
        """
        merged_df = pd.DataFrame(self.pkg_directcost, columns=column_list_for_merge)
        for markup_factor in markup_factors:
            temp = pd.DataFrame(markups.loc[markups['Markup_Factor'] == markup_factor])
            merged_df = merged_df.merge(temp, on='fuelTypeID', how='left')
            merged_df.rename(columns={'Value': markup_factor}, inplace=True)
            merged_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return merged_df

    def merge_vmt_scalars(self, vmt_scalars, column_list_for_merge):
        """

        :param vmt_scalars: A DataFrame of VMT scalars used for adjusting indirect cost markup factors based on the given alternative.
        :param column_list_for_merge: The identifier columns in the direct cost DataFrame.
        :return: A DataFrame of markup factor scalars merged on the identifier columns of the direct costs DataFrame.
        """
        merged_df = pd.DataFrame(self.pkg_directcost, columns=column_list_for_merge + markup_factors)
        for markup_factor in markup_factors_with_vmt_scalars:
            temp = pd.DataFrame(vmt_scalars.loc[vmt_scalars['Markup_Factor'] == markup_factor])
            merged_df = merged_df.merge(temp, on=column_list_for_merge, how='left')
            merged_df.rename(columns={'Value': markup_factor + '_scalar'}, inplace=True)
            merged_df.drop(labels='Markup_Factor', axis=1, inplace=True)
        return merged_df

    def indirect_cost(self, merged_df):
        """
        This method is not currently being used.

        :param merged_df: A DataFrame of indirect cost markup factors in the shape of the direct cost DataFrame
        :return: A DataFrame of indirect costs per vehicle and total costs.
        """
        techcost_df = self.pkg_directcost.copy()
        for markup_factor in markup_factors:
            techcost_df.insert(len(techcost_df.columns), markup_factor + 'Cost_AvgPerVeh', techcost_df['DirectCost_AvgPerVeh'] * merged_df[markup_factor])
            techcost_df.insert(len(techcost_df.columns), markup_factor + 'Cost_TotalCost', techcost_df[markup_factor + 'Cost_AvgPerVeh'] * techcost_df['VPOP'])
        return techcost_df

    def indirect_cost_unscaled(self, merged_df):
        """

        :param merged_df: A DataFrame of indirect cost markup factors & scalars in the shape of the direct cost DataFrame.
        :return: A DataFrame of indirect costs per vehicle and total costs for those indirect costs that do not scale with VMT.
        """
        techcost_df = self.pkg_directcost.copy()
        temp = [item for item in markup_factors if item not in markup_factors_with_vmt_scalars]
        for factor in temp:
            techcost_df.insert(len(techcost_df.columns), factor + 'Cost_AvgPerVeh', techcost_df['DirectCost_AvgPerVeh'] * merged_df[factor])
            techcost_df.insert(len(techcost_df.columns), factor + 'Cost_TotalCost', techcost_df[factor + 'Cost_AvgPerVeh'] * techcost_df['VPOP'])
        return techcost_df

    def indirect_cost_scaled(self, merged_df, factor, vmt_share):
        """

        :param merged_df: A DataFrame of indirect cost markup factors & scalars in the shape of the direct cost DataFrame.
        :param factor: A given indirect cost factor, e.g., warranty or R&D.
        :param vmt_share: A factor established in the main inputs file to represent the percentage of warranty costs that scale with VMT (vs. age or other metric).
        :return: A DataFrame of indirect costs per vehicle and total costs with VMT scalars applied.
        """
        techcost_df = self.pkg_directcost.copy()
        techcost_df.insert(len(techcost_df.columns), factor + 'Cost_AvgPerVeh', techcost_df['DirectCost_AvgPerVeh'] * (merged_df[factor] * (1 - vmt_share) + merged_df[factor] * vmt_share * merged_df[factor + '_scalar']))
        techcost_df.insert(len(techcost_df.columns), factor + 'Cost_TotalCost', techcost_df[factor + 'Cost_AvgPerVeh'] * techcost_df['VPOP'])
        return techcost_df

    def indirect_cost_sum(self):
        """

        :return: A DataFrame of full tech costs with direct and indirect costs per vehicle and in total.
        """
        techcost_df = self.pkg_directcost.copy()
        techcost_df.insert(len(techcost_df.columns), 'IndirectCost_AvgPerVeh', techcost_df[[item + 'Cost_AvgPerVeh' for item in markup_factors]].sum(axis=1))
        techcost_df.insert(len(techcost_df.columns), 'IndirectCost_TotalCost', techcost_df['IndirectCost_AvgPerVeh'] * techcost_df['VPOP'])
        return techcost_df


class IndirectCostScalars:
    """
    The IndirectCostScalars class calculates the scaling factors to be applied to indirect cost contributors. The scaling factors can be absolute
    or relative to the prior scaling factor.

    :param: input_df: A DataFrame of warranty or useful life miles and ages by optionID.
    :param identifier: String; "Warranty" or "UsefulLife" expected.
    :param period: String; "Miles" or "Ages" expected via input cell in the BCA_Inputs sheet contained in the inputs folder.
    """

    def __init__(self, input_df, identifier, period):
        self.input_df = input_df
        self.identifier = identifier
        self.period = period

    def calc_scalars_absolute(self):
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

    def calc_scalars_relative(self):
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
