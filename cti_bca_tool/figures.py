"""
figures.py

Contains the CreateFigures class.

"""
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


class CreateFigures:
    def __init__(self, df, destination):
        self.df = df
        self.destination = destination
    #
    # def line_chart_vs_age(self, dr, options, model_year, vehname, *args):
    #     for arg in args:
    #         data = self.df.loc[(self.df['DiscountRate'] == dr)
    #                            & (self.df['modelYearID'] == model_year)
    #                            & (self.df['sourceTypeName'] == vehname), :]
    #         for option in options:
    #             plt.plot((data.loc[data['optionID'] == option, 'ageID']), (data.loc[data['optionID'] == option, arg]),
    #                      label=self.df['OptionName'])
    #         plt.title(f'MY{model_year}, {vehname}, {dr}DR')
    #         plt.xlabel('ageID (year 1 is ageID=0)')
    #         plt.ylabel(arg)
    #         plt.legend()
    #         plt.grid()
    #         plt.savefig(self.destination.joinpath(f'MY{model_year}_{vehname}_{dr}DR_{arg}.png'))
    #         plt.close()
    #     return

    def line_chart_args_by_option(self, dr, alt_name, year_min, year_max, *args):
        data = self.df.loc[(self.df['DiscountRate'] == dr)
                           & (self.df['OptionName'] == alt_name)
                           & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
        for arg in args:
            plt.plot((data['yearID']), (data[arg]), label=arg)
        plt.title(f'Annual Costs, {alt_name}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel('$')
        plt.legend()
        plt.grid()
        plt.savefig(self.destination.joinpath(f'AnnualCosts_{alt_name}_{dr}DR.png'))
        plt.close()
        return

    def line_chart_arg_by_options(self, dr, alt_names, year_min, year_max, arg):
        for alt_name in alt_names:
            data = self.df.loc[(self.df['DiscountRate'] == dr)
                               & (self.df['OptionName'] == alt_name)
                               & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
            plt.plot((data.loc[data['OptionName'] == alt_name, 'yearID']), (data.loc[data['OptionName'] == alt_name, arg]),
                     label=alt_name)
        plt.title(f'Annual Costs, {arg}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel('$')
        plt.legend(loc=5)
        plt.grid()
        plt.savefig(self.destination.joinpath(f'AnnualCosts_{arg}_{dr}DR.png'))
        plt.close()
        return


def create_figures(input_df, path_for_save):
    """

    Args:
        settings:
        input_df:
        path_for_save:

    Returns:

    """
    yearID_min = int(input_df['yearID'].min())
    yearID_max = int(input_df['yearID'].max())
    path_figures = path_for_save / 'figures'
    path_figures.mkdir(exist_ok=True)
    alt_names = pd.Series(input_df.loc[input_df['optionID'] >= 10, 'OptionName']).unique()
    args = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
    for alt_name in alt_names:
        CreateFigures(input_df, path_figures) \
            .line_chart_args_by_option(0, alt_name, yearID_min, yearID_max, *args)

    for arg in args:
        CreateFigures(input_df, path_figures).line_chart_arg_by_options(0, alt_names, yearID_min, yearID_max, arg)

    return
