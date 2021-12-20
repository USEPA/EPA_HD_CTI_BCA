"""
figures.py

Contains the CreateFigures class.

"""
import pandas as pd
import matplotlib.pyplot as plt


class CreateFigures:
    def __init__(self, df, units, destination, program):
        """The CreateFigures class  is used to generate charts.

        Parameters:
            df: DataFrame; contains data to be charted.\n
            units: String; units for use on the y-axis of the created chart.\n
            destination: Path object; provides the path to which to save the created chart. \n
            program: String; th program identifier (i.e., 'CAP' or 'GHG') to include in the saved filename.

        """
        self.df = df
        self.destination = destination / 'figures'
        self.destination.mkdir(exist_ok=True)
        self.units = units
        self.program = program

    def line_chart_args_by_option(self, dr, alt_name, year_min, year_max, *args):
        """This method generates a chart showing passed arguments under the given alternative.

        Parameters:
            dr: Numeric; the discount rate of the data to be charted.\n
            alt_name: String; the OptionName of the data to be charted.\n
            year_min: Numeric; the minimum calendar year of data to be charted.\n
            year_max: Numeric; the maximum calendar year of data t be charted.\n
            args: Strings; the data attributes to be charted.

        Returns:
            A single chart saved to the destination folder.

        """
        data = self.df.loc[(self.df['DiscountRate'] == dr)
                           & (self.df['OptionName'] == alt_name)
                           & (self.df['Series'] == 'AnnualValue')
                           & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
        for arg in args:
            plt.plot((data['yearID']), (data[arg]), label=arg)
        plt.title(f'{self.program}, Annual Costs, {alt_name}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel(f'{self.units}')
        plt.legend()
        plt.grid()
        plt.savefig(self.destination.joinpath(f'{self.program}_AnnualCosts_{alt_name}_{dr}DR.png'))
        plt.close()
        return

    def line_chart_arg_by_options(self, dr, alt_names, year_min, year_max, arg):
        """This method generates a chart showing the passed argument under each of the passed alternatives.

        Parameters:
            dr: Numeric; the discount rate of the data to be charted.\n
            alt_names: List; contains the OptionNames for which to chart data.\n
            year_min: Numeric; the minimum calendar year of data to be charted.\n
            year_max: Numeric; the maximum calendar year of data t be charted.\n
            arg: String; the single data attribute to be charted.

        Returns:
            A single chart saved to the destination folder.

        """
        for alt_name in alt_names:
            data = self.df.loc[(self.df['DiscountRate'] == dr)
                               & (self.df['OptionName'] == alt_name)
                               & (self.df['Series'] == 'AnnualValue')
                               & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
            plt.plot((data.loc[data['OptionName'] == alt_name, 'yearID']), (data.loc[data['OptionName'] == alt_name, arg]),
                     label=alt_name)
        plt.title(f'{self.program}, Annual Costs, {arg}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel(f'{self.units}')
        plt.legend(loc=5)
        plt.grid()
        plt.savefig(self.destination.joinpath(f'{self.program}_AnnualCosts_{arg}_{dr}DR.png'))
        plt.close()
        return

    def create_figures(self, args):
        """This function is called by tool_main and then controls the generation of charts by the ChartFigures class.

        Parameters:
            args: List; attributes to include in figures.

        Returns:
            Charts are saved to the path_for_save folder by the ChartFigures class and this method returns to tool_main.

        """
        yearID_min = int(self.df['yearID'].min())
        yearID_max = int(self.df['yearID'].max())
        alt_names = [arg for arg in pd.Series(self.df['OptionName'].unique()) if '_minus_' in arg]

        for alt_name in alt_names:
            self.line_chart_args_by_option(0, alt_name, yearID_min, yearID_max, *args)

        for arg in args:
            self.line_chart_arg_by_options(0, alt_names, yearID_min, yearID_max, arg)

        return
