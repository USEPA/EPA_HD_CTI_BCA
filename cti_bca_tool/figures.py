"""
figures.py

Contains the CreateFigures class.

"""
import pandas as pd
import matplotlib.pyplot as plt


class CreateFigures:
    """
    The CreateFigures class generates charts.
    """
    def __init__(self, df, units, destination):
        """

        Args:
            df: A DataFrame of data to be charted.
            units: Units for use on the y-axis of the created chart.
            destination: The path in which to save the created chart.
        """
        self.df = df
        self.destination = destination
        self.units = units


    def line_chart_args_by_option(self, dr, alt_name, year_min, year_max, *args):
        """

        This method generate a chart showing passed arguments under the given alternative.
        Args:
            dr: The discount rate of the data to be charted.
            alt_name: The OptionName of the data to be charted.
            year_min: The minimum calendar year of data to be charted.
            year_max: The maximum calendar year of data t be charted.
            *args: The data arguments to be charted.

        Returns: A single chart saved to the destination folder.

        """
        data = self.df.loc[(self.df['DiscountRate'] == dr)
                           & (self.df['OptionName'] == alt_name)
                           & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
        for arg in args:
            plt.plot((data['yearID']), (data[arg]), label=arg)
        plt.title(f'Annual Costs, {alt_name}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel(f'{self.units}')
        plt.legend()
        plt.grid()
        plt.savefig(self.destination.joinpath(f'AnnualCosts_{alt_name}_{dr}DR.png'))
        plt.close()
        return

    def line_chart_arg_by_options(self, dr, alt_names, year_min, year_max, arg):
        """

        This method generate a chart showing the passed argument under each of the passed alternatives.
        Args:
            dr: The discount rate of the data to be charted.
            alt_names: The OptionNames for which to chart data.
            year_min: The minimum calendar year of data to be charted.
            year_max: The maximum calendar year of data t be charted.
            arg: The single data argument to be charted.

        Returns: A single chart saved to the destination folder.

        """
        for alt_name in alt_names:
            data = self.df.loc[(self.df['DiscountRate'] == dr)
                               & (self.df['OptionName'] == alt_name)
                               & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
            plt.plot((data.loc[data['OptionName'] == alt_name, 'yearID']), (data.loc[data['OptionName'] == alt_name, arg]),
                     label=alt_name)
        plt.title(f'Annual Costs, {arg}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel(f'{self.units}')
        plt.legend(loc=5)
        plt.grid()
        plt.savefig(self.destination.joinpath(f'AnnualCosts_{arg}_{dr}DR.png'))
        plt.close()
        return


def create_figures(input_df, units, path_for_save):
    """

    This function is called by tool_main and then controls the generation of charts by the ChartFigures class.
    Args:
        input_df: A DataFrame of data.
        units: The units used in the passed input_df.
        path_for_save: The path for saving figures.

    Returns: Charts are saved to the path_for_save folder by the ChartFigures class and this method returns to tool_main.
    """
    yearID_min = int(input_df['yearID'].min())
    yearID_max = int(input_df['yearID'].max())
    path_figures = path_for_save / 'figures'
    path_figures.mkdir(exist_ok=True)
    alt_names = pd.Series(input_df.loc[input_df['optionID'] >= 10, 'OptionName']).unique()
    # units = input_df['Units'].unique()[0]
    args = ['TechCost', 'EmissionRepairCost', 'DEFCost', 'FuelCost_Pretax', 'TechAndOperatingCost']
    for alt_name in alt_names:
        CreateFigures(input_df, units, path_figures) \
            .line_chart_args_by_option(0, alt_name, yearID_min, yearID_max, *args)

    for arg in args:
        CreateFigures(input_df, units, path_figures).line_chart_arg_by_options(0, alt_names, yearID_min, yearID_max, arg)

    return
