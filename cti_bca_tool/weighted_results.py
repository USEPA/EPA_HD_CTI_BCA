"""
weighted_results.py

Contains the WeightedResult class.
"""
import pandas as pd
from cti_bca_tool.fleet import Fleet
from cti_bca_tool.vehicle import sourceTypeID
from cti_bca_tool.calc_deltas import CalcDeltas


class WeightedResult:
    def __init__(self, input_df, weightby_metric, vehs, year_metric, year_list, max_age_included, options_dict):
        """

        :param input_df: DataFrame containing values to be weighted.
        :param weightby_metric:  The metric by which the data is being weighted.
        :param vehs: A list of vehicles for which weighting is requested.
        :param year_metric:  "yearID" or "modelYearID"
        :param year_list: List of years for which weighted results are requested.
        :param max_age_included: The age through which data is to be weighted (i.e., can be less than full life)
        :param options_dict: The options included in the input file.
        """
        self.input_df = input_df
        self.weightby_metric = weightby_metric
        self.vehs = vehs
        self.year_metric = year_metric
        self.year_list = year_list
        self.max_age_included = max_age_included
        self.options_dict = options_dict

    def weighted_results_by_veh(self, veh, metric):
        """

        :param metric: The specific metric (or series) of data to be weighted.
        :return: DataFrame containing weighted results for the passed vehicle.
        """
        # print(f'{veh}, {metric}')
        weighted_results_by_veh = dict()
        for year in self.year_list:
            df_temp = pd.DataFrame(self.input_df.loc[(self.input_df['alt_st_rc_ft'] == veh) &
                                                     (self.input_df[self.year_metric] == year) &
                                                     (self.input_df['ageID'] <= self.max_age_included), :])
            weighted_value = (df_temp[metric] * df_temp[self.weightby_metric]).sum() / df_temp[self.weightby_metric].sum()
            weighted_results_by_veh[year] = weighted_value
        return weighted_results_by_veh

    def weighted_results_all_vehs(self, metric):
        """

        :param metric: The specific metric (or series) of data to be weighted.
        :return: DataFrame containing weighted results for all vehicles.
        """
        weighted_results = dict()
        for veh in self.vehs:
            weighted_results[veh] = self.weighted_results_by_veh(veh, metric)
        return weighted_results

    def weighted_results(self, metric):
        """

        :param metric: The specific metric (or series) of data to be weighted.
        :return: A pivot table of the weighted cost per mile results for all options & all vehicles.
        """
        print(f'\nGetting weighted results of {metric} for model years {self.year_list}')
        weighted_results = pd.DataFrame(self.weighted_results_all_vehs(metric))
        weighted_results = weighted_results.transpose()
        weighted_results.reset_index(drop=False, inplace=True)
        weighted_results.rename(columns={'level_0': 'optionID', 'level_1': 'sourceTypeID',
                                         'level_2': 'regClassID', 'level_3': 'fuelTypeID'}, inplace=True)
        st_list = list()
        for index, row in weighted_results.iterrows():
            st = row['sourceTypeID']
            st_list.append(sourceTypeID[st])
        weighted_results.insert(0, 'sourceType', st_list)
        number_alts = len(weighted_results['optionID'].unique())
        Fleet(weighted_results).insert_option_name(self.options_dict, number_alts)
        for year in self.year_list:
            weighted_results.insert(len(weighted_results.columns), f'{str(year)}_cents_per_mile', weighted_results[year] * 100)
        weighted_results.columns = weighted_results.columns.astype(str)
        weighted_results = pd.concat([weighted_results,
                                      CalcDeltas(weighted_results, number_alts, [col for col in weighted_results.columns if '20' in col])
                                     .calc_delta_and_new_alt_id()], ignore_index=True, axis=0)
        weighted_results = pd.pivot_table(weighted_results,
                                          values=[col for col in weighted_results.columns if 'cents_per_mile' in col],
                                          index=['fuelTypeID', 'regClassID', 'sourceTypeID', 'sourceType', 'optionID'])
        return weighted_results


if __name__ == '__main__':
    import pandas as pd
    from pathlib import Path
    from cti_bca_tool.fleet import Fleet

    path_project = Path.cwd()
    path_inputs = path_project / 'inputs'
    sourcetype_costs_file = path_project / 'dev/sourcetype_costs.csv'
    sourcetype_costs = pd.read_csv(sourcetype_costs_file) # this reads alt_st_rc_ft as a string rather than a tuple, so...
    # convert alt_st_rc_ft to tuple as it would be if generated in main code
    sourcetype_costs.drop(columns=['alt_st_rc_ft', 'st_rc_ft'], inplace=True)
    sourcetype_costs = Fleet(sourcetype_costs).define_bca_sourcetype()
    options = pd.read_csv(path_inputs / 'options.csv', index_col=0)
    options_dict = options.to_dict('index')

    # for testing the WeightedResults class
    alt_st_rc_ft_vehs = pd.Series(sourcetype_costs['alt_st_rc_ft']).unique()
    weighted_repair_owner_cpm = dict()
    weighted_def_cpm = dict()
    weighted_fuel_cpm = dict()
    year_list = [2027, 2030, 2035]
    max_age_included = 9

    def_weighting_obj = WeightedResult(sourcetype_costs, 'VMT_AvgPerVeh', alt_st_rc_ft_vehs, 'modelYearID', year_list, max_age_included, options_dict)
    weighted_results_all_vehs = def_weighting_obj.weighted_results_all_vehs('DEFCost_AvgPerMile')
    weighted_def_cpm_df = def_weighting_obj.weighted_results('DEFCost_AvgPerMile')
    weighted_def_cpm_df.to_csv(path_project / 'dev/vmt_weighted_def_cpm.csv')
    print(weighted_def_cpm_df)
