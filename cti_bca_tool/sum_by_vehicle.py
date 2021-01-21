

def calc_sum_of_costs(dict_to_sum, name_of_sum, *args):
    for key in dict_to_sum.keys():
        vehicle, model_year, age_id, discount_rate = key[0], key[1], key[2], key[3]
        print(f'Calculating sum of {name_of_sum} for {vehicle}, MY {model_year}, age {age_id}, DR {discount_rate}')
        sum_of_costs = 0
        # note that some key, value pairs lack some data (e.g., ft=1 has no DEF cost) so the try/except addresses that
        for arg in args:
            try:
                sum_of_costs += dict_to_sum[key][arg]
            except:
                pass
        dict_to_sum[key].update({f'{name_of_sum}': sum_of_costs})
    return dict_to_sum
