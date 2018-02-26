# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 16:34:29 2018

@author: Yidi Gu
"""
# Get the package
import flask
# bokeh for plotting
from bokeh.embed import components
from flask import Flask, render_template, request
from gevent.wsgi import WSGIServer

import util
from util import get_formdata
from search import request_data
from getfigure import request_figure

# call the mongo database
cl, cl_full, field_description, cl_currency = util.call_mongoDB()

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
    form_data = util.create_dataframe_with_currency(cl, cl_currency, form_data)
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
    lookup, emptykey = request_data(cl, form_data)
    env = {
        'tablename': 'Searching',
        'columns': list(cl.find_one())[1:],
        'data': lookup,
        'requests': util.remove_empty(form_data, emptykey),
        'requests_len': lookup.count()
    }
    return render_template('search.html', **env)


@app.route("/exchange", methods=['POST'])
def exchange():
    form_data = get_formdata(request.form)
    (lookup, target_currency, required_data_lenth) = (
      util.excange_with_target_currency(cl_currency, cl, form_data)
    )
    # set up parameter
    env = {
        'tablename': 'Searching',
        'columns': lookup[:1][0].keys(),
        'data': lookup,
        'requests': form_data,
        'selected_currency': target_currency,
        'requests_len': required_data_lenth
    }
    return render_template('exchange.html', **env)


@app.route("/getfigure", methods=['POST'])
def prepare_figure():
    form_data = get_formdata(request.form)
    axis = util.get_form(form_data)
    p = request_figure(cl_full, axis, field_description)
    script, div = components(p)
    env = {
        'script': script,
        'div': div}

    return render_template('get_figure.html', **env)


@app.route("/addfigure", methods=['POST'])
def plot_figure():
    form_data = get_formdata(request.form)
    (lookup, target_currency, required_data_lenth) = (
       util.aggregate_avg_exchage_with_target_currency(
                cl_currency, cl, form_data)
    )
    p = util.add_figure(lookup)
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
