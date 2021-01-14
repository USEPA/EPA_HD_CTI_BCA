
import pandas as pd
import attr


# create a dictionary to store moves adjustments
adj_dict = dict()


def adjust_moves(alt, regclass_id, fueltype_id, moves_adjustments_df):
    """

    :param moves_adjustments_df: A DataFrame of adjustments to be made to MOVES values
    :return: The adjustment value to be applied.
    """
    adj_dict_id = f'{alt}_{regclass_id}_{fueltype_id}'
    if adj_dict_id in adj_dict:
        adjustment = adj_dict[adj_dict_id]
    else:
        try:
            adj_df = pd.DataFrame(moves_adjustments_df.loc[(moves_adjustments_df['optionID'] == alt)
                                      & (moves_adjustments_df['regClassID'] == regclass_id)
                                      & (moves_adjustments_df['fuelTypeID'] == fueltype_id), 'percent']).reset_index(drop=True)
            adjustment = adj_df['percent'][0]
        except:
            adjustment = 1

    adj_dict[adj_dict_id] = adjustment
    return adjustment


@attr.s
class Moves:
    """
    :param: fleet_df: A DataFrame consisting of, at minimum, data consisting of and Alternative ID, souretype ID, regclass ID, fueltype ID,
    model year ID, calendar year ID and consumption metrics associated with those vehicles.
    """
    fleet_df = attr.ib()

    def project_fleet_df(self, moves_adjustments_df):
        project_fleet = self.fleet_df.copy()
        if 'Alternative' in project_fleet.columns.tolist():
            project_fleet.rename(columns={'Alternative': 'optionID'}, inplace=True)

        # add an age identifier
        project_fleet.insert(project_fleet.columns.get_loc('modelYearID'),
                             'ageID',
                             project_fleet['yearID'] - project_fleet['modelYearID'])
        # remove data we don't need to carry for the project
        project_fleet = project_fleet.loc[(project_fleet['regClassID'] != 41) | (project_fleet['fuelTypeID'] != 1), :]  # eliminate (41, 1) keeping (41, 2)
        project_fleet = project_fleet.loc[project_fleet['regClassID'] != 49, :]  # eliminate Gliders
        project_fleet = project_fleet.loc[project_fleet['fuelTypeID'] != 5, :]  # eliminate E85
        project_fleet = project_fleet.loc[project_fleet['regClassID'] >= 41, :]  # eliminate non-project regclasses

        year_min = project_fleet.loc[project_fleet['ageID'] == 0, 'yearID'].min()
        project_fleet = pd.DataFrame(project_fleet.loc[project_fleet['modelYearID'] >= year_min, :]).reset_index(drop=True)

        # add some vehicle identifiers
        project_fleet.insert(0, 'alt_rc_ft',
                             pd.Series(zip(project_fleet['optionID'], project_fleet['regClassID'], project_fleet['fuelTypeID'])))
        project_fleet.insert(0, 'alt_st_rc_ft',
                             pd.Series(zip(project_fleet['optionID'], project_fleet['sourceTypeID'], project_fleet['regClassID'], project_fleet['fuelTypeID'])))

        # sum the PM constituents into a single constituent
        cols = [col for col in project_fleet.columns if 'PM25' in col]
        project_fleet.insert(len(project_fleet.columns), 'PM25_UStons', project_fleet[cols].sum(axis=1))  # sum PM25 metrics

        vehicles = pd.Series(project_fleet['alt_rc_ft'].unique())
        for vehicle in vehicles:
            alt, rc, ft = vehicle
            adjustment = adjust_moves(alt, rc, ft, moves_adjustments_df)
            args_to_adjust = ['VPOP', 'VMT', 'Gallons']
            for arg in args_to_adjust:
                project_fleet.loc[project_fleet['alt_rc_ft'] == vehicle, arg] \
                    = project_fleet.loc[project_fleet['alt_rc_ft'] == vehicle, arg] * adjustment

        return project_fleet

    def project_fleet_dict(self, moves_adjustments_df):
        df = self.project_fleet_df(moves_adjustments_df).copy()
        df.insert(0, 'id', pd.Series(zip(df['alt_st_rc_ft'], df['modelYearID'], df['ageID'])))
        df.set_index('id', inplace=True)
        project_fleet_dict = df.to_dict('index')
        return project_fleet_dict

    def project_regclass_sales_dict(self, moves_adjustments_df):
        df = self.project_fleet_df(moves_adjustments_df).copy()
        df = pd.DataFrame(df.loc[df['ageID'] == 0, ['alt_rc_ft', 'modelYearID', 'VPOP']]).reset_index(drop=True)
        df = df.groupby(by=['alt_rc_ft', 'modelYearID'], as_index=False).sum()
        df.insert(0, 'id', pd.Series(zip(df['alt_rc_ft'], df['modelYearID'])))
        df.drop(columns=['alt_rc_ft', 'modelYearID'], inplace=True)
        df.set_index('id', inplace=True)
        regclass_sales_dict = df.to_dict('index')
        return regclass_sales_dict


@attr.s
class Vehicle:
    vehicle = attr.ib()

    def vehicle_identifiers(self):
        if len(self.vehicle) == 3:
            alt, rc, ft = self.vehicle
            return alt, rc, ft
        else:
            alt, st, rc, ft = self.vehicle
            return alt, st, rc, ft

    def df_identifier(self):
        if len(self.vehicle) == 3:
            return 'alt_rc_ft'
        else:
            return 'alt_st_rc_ft '

    def vehicle_vpop(self, fleet_dict):
        return fleet_dict[((self.vehicle), self.model_year_id, self.age_id)]['VPOP']

    def vehicle_vmt(self, fleet_dict):
        return fleet_dict[((self.vehicle), self.model_year_id, self.age_id)]['VMT']

    def vehicle_gallons(self, fleet_dict):
        return fleet_dict[((self.vehicle), self.model_year_id, self.age_id)]['VPOP']

    # def regclass_sales_following_given_my(self, fleet_df, moves_adj, year):
    #     obj_df = pd.DataFrame(fleet_df.loc[(fleet_df[self.df_identifier()] == self.vehicle)
    #                                        & (fleet_df['modelYearID'] >= year)
    #                                        & (fleet_df['ageID'] == 0),
    #                                        ['optionID', 'modelYearID', 'ageID', 'regClassID', 'fuelTypeID', 'VPOP']]) \
    #         .reset_index(drop=True)
    #
    #     # adjust if necessary
    #     alt, rc, ft = self.vehicle
    #     adjustment = adjust_moves(alt, rc, ft, moves_adj)
    #     args_to_adjust = ['VPOP']
    #     for arg in args_to_adjust:
    #         obj_df[arg] = obj_df[arg] * adjustment
    #     obj_df = obj_df.groupby(by=['optionID', 'modelYearID', 'ageID', 'regClassID', 'fuelTypeID'], as_index=False).sum()
    #     return obj_df


if __name__ == '__main__':
    from cti_bca_tool.__main__ import SetInputs as settings
    # from cti_bca_tool.project_fleet import project_fleet, alt_rc_ft_vehicles

    project_fleet_dict = Moves(settings.moves).project_fleet_dict(settings.moves_adjustments)
    project_regclass_sales_dict = Moves(settings.moves).project_regclass_sales_dict(settings.moves_adjustments)
    project_regclass_sales_df = pd.DataFrame(project_regclass_sales_dict)
    project_regclass_sales_df = project_regclass_sales_df.transpose()
    project_regclass_sales_df.to_csv(settings.path_project / f'test/regclass_sales.csv', index=True)


    # project_fleet = project_fleet(settings.moves)
    # vehicles = alt_rc_ft_vehicles(project_fleet)
    # cost_steps = [col for col in settings.regclass_costs.columns if '20' in col]
    # steps = len(cost_steps)
    #
    # for step in range(steps):
    #     regclass_sales_fleet = pd.DataFrame()
    #     for vehicle in vehicles:
    #         regclass_sales_veh = ProjectClass(vehicle=vehicle)\
    #             .regclass_sales_following_given_my(project_fleet, settings.moves_adjustments, int(cost_steps[step]))
    #         regclass_sales_fleet = pd.concat([regclass_sales_fleet, regclass_sales_veh], axis=0, ignore_index=True)
    #     regclass_sales_fleet.to_csv(settings.path_project / f'test/regclass_sales_{cost_steps[step]}.csv', index=False)
