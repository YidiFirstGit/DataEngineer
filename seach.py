def transform_datatype(form_data):
    form_data = {k: int(v) if str(v).isdigit() else v
                 for k, v in form_data.items()}
    return form_data


def generate_lower_upper_bounds(form_data):
    year_s0 = form_data['Year Sold from']
    year_e0 = form_data['Year Sold until']
    price_s0 = form_data['SalePrice from']
    price_e0 = form_data['SalePrice until']
    return year_s0, year_e0, price_s0, price_e0
