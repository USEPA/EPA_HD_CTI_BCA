"""
This test module tests the discounting and annualizing methods to ensure that things are working properly.
The annualized values in the two created DataFrames should be 100.
"""
import pandas as pd

from project_code.group_metrics import GroupMetrics
from project_code.discounting import DiscountValues


df = pd.DataFrame({'yearID': [2027, 2028, 2029, 2030, 2031, 2032],
                   'cost': [100, 100, 100, 100, 100, 100]})
df.insert(0, 'option', 0)
discrate = 0.03
discount_to_cy = 2027

costs_start = 'start-year'
df_startyear = DiscountValues(df, ['cost'], discount_to_cy, costs_start).discount(discrate)
df_startyear = df_startyear.join(GroupMetrics(df_startyear, ['option']).group_cumsum(['cost']))
DiscountValues(df_startyear, ['cost'], discount_to_cy, costs_start).annualize()
print(df_startyear)

costs_start = 'end-year'
df_endyear = DiscountValues(df, ['cost'], discount_to_cy, costs_start).discount(discrate)
df_endyear = df_endyear.join(GroupMetrics(df_endyear, ['option']).group_cumsum(['cost']))
DiscountValues(df_endyear, ['cost'], discount_to_cy, costs_start).annualize()
print(df_endyear)
