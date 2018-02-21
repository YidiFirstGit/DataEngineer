from bokeh.plotting import figure
from datetime import date as dt
import pandas as pd


def figure_setting(title, tool, axis, x_axis_type, x_range):
    return figure(title=title, plot_width=1000, plot_height=700,
                  tools=tool, x_axis_label=axis.x_label,
                  y_axis_label=axis.y_label, x_axis_type=x_axis_type,
                  x_range=x_range)


def get_date_related_fields_name(field_description):
    '''
    field_description is MangoDB collection
    '''
    regex = ".*" + 'year|month|date' + ".*"
    field_date = [x['field'] for x in list(
            field_description.find({
                    'description': {'$regex': regex, "$options": 'i'}}))]
    field_date.remove('MoSold')
    return field_date


def get_categorical_fields_name(cl_full):
    '''
    input is MangoDB collection
    '''
    example = cl_full.find_one({}, {'_id': False, 'Id': False})
    field_categorical = [i for i in example if type(example[i]) == str]
    field_categorical.append('MoSold')
    return field_categorical


def get_multiplevalue(mydict, keys):
    return [mydict[k] for k in keys]


def get_ymd(mydict, date):
    '''
    get yEAR, mONTH, dAY information from merge list date
    refill m, d = 1 if the value is missing
    '''
    if len(date) == 3:
        y, m, d = get_multiplevalue(mydict, date)
    elif len(date) == 2:
        y, m = get_multiplevalue(mydict, date)
        d = 1
    elif len(date) == 1:
        y = get_multiplevalue(mydict, date)[0]
        m = d = 1
    return y, m, d


def prepare_df_time(tmp, axis, date):
    """this is called a docstring"""
    x = []
    y = []
    for i in tmp:
        tmp = get_ymd(i, date)
        if type(tmp[0]) == int:
            x.append(dt(get_ymd(i, date)[0],
                        get_ymd(i, date)[1],
                        get_ymd(i, date)[2]))
            y.append(i[axis.y_title])
    df = pd.DataFrame(dict(x=x, y=y))
    df['tooltip'] = [value.strftime("%Y-%m-%d") for value in df['x']]
    return df


def aggregate_merge_month_year(cl_full, axis):
    '''
    cl_full is MangoDB collection
    axis is figure class
    '''
    tmp = cl_full.aggregate([{
            '$group': {
                    '_id': {'year': '$YrSold', 'month': '$MoSold'},
                    axis.y_title: {
                            '$avg': axis.y}
                    }}, {
                    '$project': {
                            'year': '$_id.year',
                            'month': '$_id.month',
                            axis.y_title: '$'+axis.y_title,
                            '_id': 0}},
                    {'$sort': {'year': 1, 'month': 1}}
                    ])
    return tmp


def aggregate_avg_sale(cl_full, axis):
    tmp = cl_full.aggregate([{
            '$group': {'_id': axis.x, axis.y_title: {'$avg': axis.y}}
            }, {'$sort': {'_id': 1}}])
    return tmp
