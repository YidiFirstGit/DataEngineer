from util import empty_keys


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


def get_logical_expression(form_data, cl):
    year_s0, year_e0, price_s0, price_e0 = (
      generate_lower_upper_bounds(form_data)
    )
    salecondition = form_data['SaleCondition']
    g1 = {"YrSold": {"$gte": year_s0}}
    l1 = {"YrSold": {"$lte": year_e0}}
    g2 = {"SalePrice": {"$gte": price_s0}}
    l2 = {"SalePrice": {"$lte": price_e0}}
    if form_data['SaleCondition'] == 'All':
        sc = {'SaleCondition': {'$in': cl.distinct('SaleCondition')}}
    else:
        sc = {'SaleCondition': salecondition}
    return g1, l1, g2, l2, sc


def get_logical_relation(emptykey):
    number_of_requests = len(emptykey)
    log1 = log2 = log3 = log4 = "$and"
    if number_of_requests == 1:
        if 'Year Sold from' in emptykey or 'Year Sold until' in emptykey:
            log1 = "$or"
        else:
            log2 = "$or"
    elif number_of_requests == 2:
        if 'Year Sold from' in emptykey and 'Year Sold until' in emptykey:
            log1 = log3 = "$or"
        elif 'SalePrice from' in emptykey and 'SalePrice until' in emptykey:
            log2 = log3 = "$or"
        else:
            log1 = log2 = "$or"
    elif number_of_requests == 3 or number_of_requests == 4:
        log1 = log2 = log3 = "$or"

    if 'SaleCondition' in emptykey:
        log4 = "$or"
    elif number_of_requests == 4 and 'SaleCondition' not in emptykey:
        log4 = "$or"

    return log1, log2, log3, log4


def request_data(cl, form_data):
        # transform data type
        form_data = transform_datatype(form_data)
        # JSON logical expression preparing with lower and upper bounds
        g1, l1, g2, l2, sc = get_logical_expression(form_data, cl)
        # Get logical relation
        emptykey = empty_keys(form_data)
        log1, log2, log3, log4 = get_logical_relation(emptykey)
        # request data from database
        lookup = cl.find({
                log4: [{
                        log3: [{log1: [g1, l1]}, {log2: [g2, l2]}]}, sc]})
        return lookup, emptykey
