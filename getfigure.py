from bokeh.plotting import figure, ColumnDataSource
from datetime import date as dt
import pandas as pd
from bokeh.models import HoverTool
from util import NumToMonth
from util import get_date_related_fields_name
from util import get_categorical_fields_name


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


def figure_setting(title, axis, x_axis_type='linear', x_range=None):
    return figure(title=title, plot_width=1000, plot_height=700,
                  tools='pan,wheel_zoom,box_zoom,reset,previewsave,hover',
                  x_axis_label=axis.x_label,
                  y_axis_label=axis.y_label, x_axis_type=x_axis_type,
                  x_range=x_range)


def hovertools_settings(fig, x_type='linear', x='date', tip_col='@tooltip'):
    '''
    fig : figure
    x_type : 'linear'(default) or 'datetime'
    '''
    hover = fig.select(dict(type=HoverTool))
    tips = [(x, tip_col), ('AvgPrice', '@y{($ 0.00 a)}')]
    hover.tooltips = tips
    return


def figure_moyr(cl_full, axis):
    tmp = aggregate_merge_month_year(cl_full, axis)
    title = 'Sold time vs '+axis.y_label
    x_axis_type = 'datetime'
    axis.x_label = 'Month and Year Sold'
    date = ['year', 'month']
    df = prepare_df_time(tmp, axis, date)
    p = figure_setting(title=title, axis=axis, x_axis_type=x_axis_type)
    p.line('x', 'y', source=ColumnDataSource(df))
    hovertools_settings(fig=p, x_type=x_axis_type)
    return p


def figure_date(cl_full, axis):
    tmp = aggregate_avg_sale(cl_full, axis)
    x_axis_type = 'datetime'
    title = axis.x_label+' vs '+axis.y_label
    date = ['_id']
    df = prepare_df_time(tmp, axis, date)
    p = figure_setting(title=title, axis=axis, x_axis_type=x_axis_type)
    p.line('x', 'y', source=ColumnDataSource(df))
    hovertools_settings(fig=p, x_type=x_axis_type)
    return p


def figure_categorical(cl_full, axis):
    tmp = aggregate_avg_sale(cl_full, axis)
    title = axis.x_label+' vs '+axis.y_label
    factor = []
    y = []
    for i in tmp:
        factor.append(i['_id'])
        y.append(i[axis.y_title])
    # replace MoSold with month name
    if axis.x_label == 'MoSold':
        factor = [NumToMonth(i) for i in factor]
    p = figure_setting(title=title, axis=axis,
                       x_range=factor, x_axis_type='auto')
    p.circle(factor, y, size=15,
             source=ColumnDataSource(pd.DataFrame(
                     dict(factor=factor, y=y))))
    hovertools_settings(fig=p, x=axis.x_label, tip_col='@factor')
    return p


def figure_numerical(cl_full, axis):
    tmp = aggregate_avg_sale(cl_full, axis)
    x = []
    y = []
    for i in tmp:
        x.append(i['_id'])
        y.append(i[axis.y_title])
    title = axis.x_label+' vs '+axis.y_label
    p = figure_setting(title, axis)
    p.line(x, y, line_width=2, source=ColumnDataSource(
            pd.DataFrame(dict(x=x, y=y))))
    hovertools_settings(fig=p, x=axis.x_label, tip_col='@x')
    return p


def request_figure(cl_full, axis, field_description):
    # use regular expression to find the field correlated to the date
    field_date = get_date_related_fields_name(field_description)
    # find the field is categorical data, $type is str
    field_categorical = get_categorical_fields_name(cl_full)
    if axis.x_label == 'MoYrSold':
        p = figure_moyr(cl_full, axis)
    elif axis.x_label in field_date:
        p = figure_date(cl_full, axis)
    elif axis.x_label in field_categorical:
        p = figure_categorical(cl_full, axis)
    # else:
    else:
        p = figure_numerical(cl_full, axis)
    return p
