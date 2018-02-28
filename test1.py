# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 16:34:29 2018

@author: Yidi Gu
"""

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
    (field_date, field_categorical, field_numerical) = (
      util.get_figure_selection(field_description, cl_full)
    )
    env = {
        'tablename': 'House Prices',
        'columns': util.get_columnsname(),
        'data': cl.find().limit(20),
        'saletype_option': cl.distinct('SaleType'),
        'salecondition_option': cl.distinct('SaleCondition'),
        'currency_option': util.sort_fields(cl_currency.distinct('currency')),
        'field_description_date': field_date,
        'field_description_categorical': field_categorical,
        'field_description_numerical': field_numerical
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
        'columns': util.get_columnsname(),
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
        'columns': util.get_columnsname(),
        'data': lookup,
        'requests': util.remove_empty(form_data, emptykey),
        'requests_len': lookup.count()
    }
    return render_template('search.html', **env)


@app.route("/exchange", methods=['POST'])
def exchange():
    form_data = get_formdata(request.form)
    (lookup, columns, target_currency, required_data_lenth) = (
      util.excange_with_target_currency(cl_currency, cl, form_data)
    )
    # set up parameter
    env = {
        'tablename': 'Searching',
        'columns': columns,
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
    (lookup, columns, target_currency, required_data_lenth) = (
       util.aggregate_avg_exchage_with_target_currency(
                cl_currency, cl, form_data)
    )
    p = util.add_figure(lookup)
    script, div = components(p)
    env = {
        'tablename': 'Searching',
        'columns': columns,
        'data': lookup,
        'requests': form_data,
        'selected_currency': target_currency,
        'requests_len': required_data_lenth,
        'script': script,
        'div': div}
    return render_template('add_figure.html', **env)


@app.route("/requestfile", methods=['POST'])
def save_excel():
    form_data = get_formdata(request.form)
    response = util.prepare_response(cl_currency, cl, form_data)
    return response


if __name__ == "__main__":

    wsgiserverX = WSGIServer(('0.0.0.0', 8080), app)
    print("Started")
    wsgiserverX.serve_forever()
