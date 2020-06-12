import matplotlib.pyplot as plt


class CreateFigures:
    def __init__(self, df, options_dict, destination):
        self.df = df
        self.options_dict = options_dict
        self.destination = destination
        
    def line_chart_vs_age(self, dr, options, model_year, vehname, *args):
        for arg in args:
            data = self.df.loc[(self.df['DiscountRate'] == dr)
                               & (self.df['modelYearID'] == model_year)
                               & (self.df['Vehicle_Name_MOVES'] == vehname), :]
            for option in options:
                plt.plot((data.loc[data['optionID'] == option, 'ageID']), (data.loc[data['optionID'] == option, arg]),
                         label=self.options_dict[option]['OptionName'])
            plt.title(f'MY{model_year}, {vehname}, {dr}DR')
            plt.xlabel('ageID (year 1 is ageID=0)')
            plt.ylabel(arg)
            plt.legend()
            plt.grid()
            plt.savefig(self.destination.joinpath(f'MY{model_year}_{vehname}_{dr}DR_{arg}.png'))
            plt.close()
        return

    def line_chart_args_by_option(self, dr, option, year_min, year_max, *args):
        optname = self.options_dict[option]['OptionName']
        data = self.df.loc[(self.df['DiscountRate'] == dr)
                           & (self.df['optionID'] == option)
                           & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
        for arg in args:
            plt.plot((data['yearID']), (data[arg]), label=arg)
        plt.title(f'Annual Costs, {optname}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel('$')
        plt.legend()
        plt.grid()
        plt.savefig(self.destination.joinpath(f'AnnualCosts_{optname}_{dr}DR.png'))
        plt.close()
        return

    def line_chart_arg_by_options(self, dr, options, year_min, year_max, arg):
        for option in options:
            data = self.df.loc[(self.df['DiscountRate'] == dr)
                               & (self.df['optionID'] == option)
                               & ((self.df['yearID'] >= year_min) & (self.df['yearID'] <= year_max)), :]
            plt.plot((data.loc[data['optionID'] == option, 'yearID']), (data.loc[data['optionID'] == option, arg]),
                     label=self.options_dict[option]['OptionName'])
        plt.title(f'Annual Costs, {arg}, {dr}DR')
        plt.xlabel('calendar year')
        plt.ylabel('$')
        plt.legend(loc=5)
        plt.grid()
        plt.savefig(self.destination.joinpath(f'AnnualCosts_{arg}_{dr}DR.png'))
        plt.close()
        return
