# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 16:34:29 2018

@author: Yidi Gu
"""
# Get the package
import flask  # web interface
import pymongo  # mongodb database
import pandas as pd
# bokeh for plotting
from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import components
from bokeh.models import HoverTool
from flask import Flask, render_template, request
from gevent.wsgi import WSGIServer
import util


def get_formdata(formdata):
    form_data = dict(formdata)
    form_data = zip([i for i in form_data.keys()], sum(form_data.values(), []))
    form_data = dict(form_data)
    return form_data


# call the mongo database
util.call_mongoDB()

# build web interface

app = Flask(__name__)


@app.route("/")
def main():
    env = {
        'tablename': 'House Prices',
        'columns': list(cl.find_one())[1:],
        'data': cl.find().limit(20),
        'saletype_option': cl.distinct('SaleType'),
        'salecondition_option': cl.distinct('SaleCondition'),
        'currency_option': cl_currency.distinct('currency'),
        'field_description': list(field_description.find())
    }
    return render_template('index.html', **env)


@app.route("/new_data", methods=['POST'])
def new_data():
    form_data = get_formdata(request.form)
    form_data = util.create_dataframe_with_currency(form_data)
    # insert data into database
    cl.insert_one(form_data)
    # set variable
    env = {
        'tablename': 'New inserted data',
        'columns': list(cl.find_one())[1:],
        'data': form_data,
        'saletype_option': cl.distinct('SaleType'),
        'salecondition_option': cl.distinct('SaleCondition')
    }
    return render_template('new_data.html', **env)


@app.route("/search", methods=['POST'])
def search():
    form_data = get_formdata(request.form)
    # transform data type
    form_data = {k: int(v) if str(v).isdigit() else v
                 for k, v in form_data.items()}
    # print(form_data)
    # set lower and upper bounds
    year_s0 = form_data['Year Sold from']
    year_e0 = form_data['Year Sold until']
    price_s0 = form_data['SalePrice from']
    price_e0 = form_data['SalePrice until']
    salecondition = form_data['SaleCondition']
    # JSON logical expression preparing
    g1 = {"YrSold": {"$gte": year_s0}}
    l1 = {"YrSold": {"$lte": year_e0}}
    g2 = {"SalePrice": {"$gte": price_s0}}
    l2 = {"SalePrice": {"$lte": price_e0}}
    if form_data['SaleCondition'] == 'All':
        sc = {'SaleCondition': {'$in': cl.distinct('SaleCondition')}}
    else:
        sc = {'SaleCondition': salecondition}
    # Get logical relation
    ek = util.empty_keys(form_data)
    N = len(ek)
    log1 = log2 = log3 = log4 = "$and"
    if N == 1:
        if 'Year Sold from' in ek or 'Year Sold until' in ek:
            log1 = "$or"
        else:
            log2 = "$or"
    elif N == 2:
        if 'Year Sold from' in ek and 'Year Sold until' in ek:
            log1 = log3 = "$or"
        elif 'SalePrice from' in ek and 'SalePrice until' in ek:
            log2 = log3 = "$or"
        else:
            log1 = log2 = "$or"
    elif N == 3 or N == 4:
        log1 = log2 = log3 = "$or"

    if 'SaleCondition' in ek:
        log4 = "$or"
    elif N == 4 and 'SaleCondition' not in ek:
        log4 = "$or"

    # request data from database
    lookup = cl.find({
            log4: [{
                    log3: [{log1: [g1, l1]}, {log2: [g2, l2]}]}, sc]})
    env = {
        'tablename': 'Searching',
        'columns': list(cl.find_one())[1:],
        'data': lookup,
        'requests': util.remove_empty(form_data, ek),
        'requests_len': lookup.count()
    }
    return render_template('search.html', **env)


@app.route("/exchange", methods=['POST'])
def exchange():
    form_data = get_formdata(request.form)
    # print(form_data)
    target_currency = form_data['currency']
    # get the exchange rate from database
    exchange_rate = list(cl_currency.find({
            'currency': target_currency}))[0]['rate']
    lookup = list(cl.aggregate(util.exchange_pipeline(exchange_rate)))
    required_data_lenth = len(lookup)
    # set up parameter
    env = {
        'tablename': 'Searching',
        'columns': lookup[:1][0].keys(),
        'data': lookup,
        'requests': form_data,
        'selected_currency': target_currency,
        'requests_len': required_data_lenth
    }
    return render_template('search.html', **env)


def figure_setting(title, tool, axis, x_axis_type, x_range):
    return figure(title=title, plot_width=1000, plot_height=700,
                  tools=tool, x_axis_label=axis.x_label,
                  y_axis_label=axis.y_label, x_axis_type=x_axis_type,
                  x_rang=x_range)


@app.route("/getfigure", methods=['POST'])
def prepare_figure():
    form_data = get_formdata(request.form)
    print(form_data)
    axis = util.get_form(form_data)
    from datetime import date as dt
    # use regular expression to find the field correlated to the date
    regex = ".*" + 'year|month|date' + ".*"
    field_date = [x['field'] for x in list(
            field_description.find({
                    'description': {'$regex': regex, "$options": 'i'}}))]
    field_date.remove('MoSold')
    # find the field is categorical data, $type is str
    example = cl_full.find_one({}, {'_id': False, 'Id': False})
    field_categorical = [i for i in example if type(example[i]) == str]
    field_categorical.append('MoSold')
    # Some general set up

    tool = 'pan,wheel_zoom,box_zoom,reset,previewsave,hover'
    title = axis.x_label+' vs '+axis.y_label
    x_axis_type = 'linear'
    x_range = None

    def prepare_df_time(tmp, axis, date):
        """this is called a docstring"""
        x = []
        y = []

        def get_ymd(i, date):
            '''
            get yEAR, mONTH, dAY information from merge list date
            refill m, d = 1 if the value is missing
            '''
            if len(date) == 3:
                y, m, d = i[date]
            elif len(date) == 2:
                y, m = i[date]
                d = 1
            elif len(date) == 1:
                y = i[date[0]]
                m = d = 1
            return y, m, d
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
    # prepare for the figure
    # if axis.x_label in 'MoYrSold':
    if axis.x_label == 'MoYrSold':
        # merge month and year
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
        title = 'Sold time vs '+axis.y_label
        x_axis_type = 'datetime'
        axis.x_label = 'Month and Year Sold'
        date = ['year', 'month']
        df = prepare_df_time(tmp, axis, date)
        p = figure_setting(title, tool, axis, x_axis_type, x_range)
        p.line('x', 'y', source=ColumnDataSource(df))
        hover = p.select(dict(type=HoverTool))
        tips = [('date', '@tooltip'), ('AvgPrice', '@y{($ 0.00 a)}')]
        hover.tooltips = tips
    # elif form in field_date:
    elif axis.x_label in field_date:
        # transfer the int to date
        tmp = cl_full.aggregate([{
                '$group': {'_id': axis.x, axis.y_title: {'$avg': axis.y}}
                }, {'$sort': {'_id': 1}}])
        x_axis_type = 'datetime'
        date = ['_id']
        df = prepare_df_time(tmp, axis, date)
        p = figure_setting(title, tool, axis, x_axis_type, x_range)
        p.line('x', 'y', source=ColumnDataSource(df))
        hover = p.select(dict(type=HoverTool))
        tips = [('date', '@tooltip'), ('AvgPrice', '@y{($ 0.00 a)}')]
        hover.tooltips = tips

    # elif form in field_categorical:
    elif axis.x_label in field_categorical:
        # 1. categorcial axis 2. boxplot(later)
        tmp = cl_full.aggregate([{
                '$group': {'_id': axis.x, axis.y_title: {'$avg': axis.y}}
                }, {'$sort': {'_id': 1}}])
        factor = []
        y = []
        for i in tmp:
            factor.append(i['_id'])
            y.append(i[axis.y_title])
        # replace MoSold with month name
        if axis.x_label == 'MoSold':
            factor = [util.NumToMonth(i) for i in factor]
        p = figure(tools=tool, x_range=factor, title=title)
        p.xaxis.axis_label = axis.x_label
        p.yaxis.axis_label = axis.y_label
        # p = prepare_figure(title,tool,axis,x_axis_type,x_range)
        p.circle(factor, y, size=15,
                 source=ColumnDataSource(pd.DataFrame(
                         dict(factor=factor, y=y))))
        hover = p.select(dict(type=HoverTool))
        tips = [(axis.x_label, '@factor'), ('AvgPrice', '@y{($ 0.00 a)}')]
        hover.tooltips = tips
    # else:
    else:
        # simple calculate the averge:
        tmp = cl_full.aggregate([{
                '$group': {'_id': axis.x, axis.y_title: {'$avg': axis.y}}
                }, {'$sort': {'_id': 1}}])
        x = []
        y = []
        for i in tmp:
            x.append(i['_id'])
            y.append(i[axis.y_title])
        title = axis.x_label+' vs '+axis.y_label
        p = figure_setting(title, tool, axis, x_axis_type, x_range)
        p.line(x, y, line_width=2, source=ColumnDataSource(
                pd.DataFrame(dict(x=x, y=y))))
        hover = p.select(dict(type=HoverTool))
        tips = [(axis.x_label, '@x'), ('AvgPrice', '@y{($ 0.00 a)}')]
        hover.tooltips = tips

    # get html components
    script, div = components(p)
    env = {
        'script': script,
        'div': div}

    return render_template('get_figure.html', **env)


@app.route("/addfigure", methods=['POST'])
def plot_figure():
    form_data = get_formdata(request.form)
    print(form_data)
    target_currency = form_data['currency']
    exchange_rate = list(cl_currency.find({
            'currency': target_currency}))[0]['rate']
    lookup = list(cl.aggregate(util.exchange_pipeline(exchange_rate)))
    required_data_lenth = len(lookup)
    tmp = cl.aggregate([{
            '$group': {'_id': '$YrSold', 'avgPrice': {'$avg': '$SalePrice'}}
            }, {'$sort': {'_id': 1}}])
    x = []
    y = []
    for i in tmp:
        x.append(i['_id'])
        y.append(i['avgPrice'])
    # create a new plot with a title and axis labels
    p = figure(title="YrSold vs SalePrice",
               x_axis_label='Year Sold',
               y_axis_type='log',
               y_axis_label='Sale Price')
    # add a line renderer with legend and line thickness
    p.line(x, y, legend="Sale Price", line_width=2)
    script, div = components(p)
    env = {
        'tablename': 'Searching',
        'columns': lookup[:1][0].keys(),
        'data': lookup,
        'requests': form_data,
        'selected_currency': target_currency,
        'requests_len': required_data_lenth,
        'script': script,
        'div': div}
    return render_template('add_figure.html', **env)


@app.route("/requestfile", methods=['POST'])
def save_excel():
    form_data = dict(request.form)
    # print(form_data)
    target_currency = form_data['currency'][0]
    exchange_rate = list(cl_currency.find({
            'currency': target_currency}))[0]['rate']
    data = list(cl.aggregate(util.exchange_pipeline(exchange_rate)))
    title = 'House Pirce in ' + target_currency
    mimetype = 'application/vnd.openxmlformats-officedocument.\
    spreadsheetml.sheet'
    response = flask.Response(util.prepareExcel(data, title),
                              mimetype=mimetype)
    response.headers['Content-Type'] = mimetype
    filename = 'attachment; filename=House Price ( '+target_currency+' ).xlsx'
    response.headers['Content-Disposition'] = filename
    return response


if __name__ == "__main__":

    wsgiserverX = WSGIServer(('0.0.0.0', 8080), app)
    print("Started")
    wsgiserverX.serve_forever()
