from bca_tool_code.costs import Costs


def calc_ghg_costs(settings):

    ghg_costs = Costs()
    ghg_costs.create_costs_dict(settings, 'GHG', settings.ghg_vehicles_list)
