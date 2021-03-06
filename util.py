# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 13:49:22 2018

@author: Yidi Gu
"""
import io
import openpyxl  # work with excel file
import random
import pymongo
import six
from flask import Response
from bokeh.plotting import figure


def get_columnsname():
    col = (
      ['Id', 'YrSold', 'SaleType', 'SaleCondition', 'SalePrice', 'currency']
    )
    return col


def get_formdata(formdata):
    form_data = dict(formdata)
    form_data = zip([i for i in form_data.keys()], sum(form_data.values(), []))
    form_data = dict(form_data)
    return form_data


def empty_keys(dic):
    return [k for k, v in dic.items() if v == '']


def remove_empty(dic, empty_key):
    for item in empty_key:
        del dic[item]
    return dic


def exchange_pipeline(exchange_rate):
    '''
    prepare for pipeline for exchange_rate
    '''
    # 1.1 for house prices look up the exchange rate based on EUR
    join = {
            '$lookup': {
                    'from': 'currencyEuroBase',
                    'localField': 'currency',
                    'foreignField': 'currency',
                    'as': 'inventory_docs'
                    }}
    # 1.2 flatten documents
    flat = {'$unwind': '$inventory_docs'}
    # 1.3 choose the fields to show and caculate the exchange rate
    # based on request currency
    project = {
            '$project': {
                    'Id': 1,
                    'SaleCondition': 1,
                    'SalePrice': 1,
                    'SaleType': 1,
                    'YrSold': 1,
                    'currency': 1,
                    '_id': 0,
                    'rate': {
                            '$divide': ["$inventory_docs.rate", exchange_rate]
                            }
                    }}
    # 1.4 calculate and add the new price in request currency
    add_newfield = {
            '$addFields': {
                    "Price(currency)": {
                            '$trunc': {
                                    '$divide': ["$SalePrice", "$rate"]
                                    }
                            }}}
    pipeline = [join, flat, project, add_newfield]
    return pipeline


def prepareExcel(data, title):
    '''
    return excel file
    '''
    my_file = io.BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = title
    columns = (
       ['Id', 'YrSold', 'SaleType', 'SaleCondition', 'SalePrice',
        'currency', 'rate', 'Price(currency)']
    )
    sheet.append(columns)
    for row in data:
        sheet.append([row[i] for i in columns])
    workbook.save(my_file)
    return my_file.getvalue()


def NumToMonth(num):
    """
    Converts between 3-letter month names and their month number  (1 - 12)
    """
    mydict = {
            'Jan': 1,
            'Feb': 2,
            'Mar': 3,
            'Apr': 4,
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Aug': 8,
            'Sep': 9,
            'Oct': 10,
            'Nov': 11,
            'Dec': 12
            }
    for month, number in mydict.items():
        if number == num:
            return month


class get_form:
    def __init__(self, form_data):
        self.x_label = form_data['X axis']
        self.y_label = 'SalePrice'
        self.x = '$'+self.x_label
        self.y = '$'+self.y_label
        self.y_title = 'avg'+self.y_label


def call_mongoDB():
    client = pymongo.MongoClient('localhost', 27017)
    cl = client.test_database.test_houseprices
    cl_full = client.test_database.test
    field_description = client.test_database.data_fields
    cl_currency = client.test_database.currencyEuroBase
    return cl, cl_full, field_description, cl_currency


def remove_list_from_list(list1, remove_list):
    for i in remove_list:
        list1.remove(i)
    return list1


def sort_fields(list_field):
    list_field.sort()
    return list_field


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
    field_categorical = (
        [i for i in example if isinstance(example[i], six.string_types)]
    )
    field_categorical.append('MoSold')
    return field_categorical


def get_figure_selection(field_description, cl_full):
    field_date = get_date_related_fields_name(field_description)
    field_categorical = get_categorical_fields_name(cl_full)
    all_fields = list(field_description.find({}, {'_id': 0, 'description': 0}))
    field_numerical = [x['field'] for x in all_fields]
    field_remove = field_date + field_categorical
    field_remove.remove('currency')
    field_numerical = remove_list_from_list(field_numerical, field_remove)
    field_date = (
       list(field_description.find({
                              'field': {'$in': field_date}
                              }).sort('description'))
       )
    field_categorical = (
       list(field_description.find({
                              'field': {'$in': field_categorical}
                              }).sort('description'))
       )
    field_numerical = (
       list(field_description.find({
                              'field': {'$in': field_numerical}
                              }).sort('description'))
       )
    return field_date, field_categorical, field_numerical


def create_dataframe_with_currency(cl, cl_currency, form_data):
    form_data['YrSold'] = int(form_data['YrSold'])
    form_data['SalePrice'] = int(form_data['SalePrice'])
    ID = list(cl.find())[-1]['Id']+1
    form_data['Id'] = ID
    form_data['currency'] = random.choice(cl_currency.distinct('currency'))
    return form_data


def excange_with_target_currency(cl_currency, cl, form_data):
    target_currency = form_data['currency']
    exchange_rate = list(cl_currency.find({
                        'currency': target_currency}))[0]['rate']
    lookup = list(cl.aggregate(exchange_pipeline(exchange_rate)))
    columns = (
       ['Id', 'YrSold', 'SaleType', 'SaleCondition', 'SalePrice',
        'currency', 'rate', 'Price(currency)']
    )
    required_data_lenth = len(lookup)
    return lookup, columns, target_currency, required_data_lenth


def aggregate_avg_exchage_with_target_currency(cl_currency, cl, form_data):
    target_currency = form_data['currency']
    exchange_rate = list(cl_currency.find({
                        'currency': target_currency}))[0]['rate']
    prepare_avg = {
            '$group': {'_id': '$YrSold', 'avgPrice': {
                    '$avg': '$Price(currency)'}}}
    sort_avg = {'$sort': {'_id': 1}}
    pipeline_avg = exchange_pipeline(exchange_rate)
    pipeline_avg.append(prepare_avg)
    pipeline_avg.append(sort_avg)
    lookup = list(cl.aggregate(pipeline_avg))
    columns = ['_id', 'avgPrice']
    required_data_lenth = len(lookup)
    return lookup, columns, target_currency, required_data_lenth


def prepare_response(cl_currency, cl, form_data):
    (lookup, _, target_currency, _) = (
      excange_with_target_currency(cl_currency, cl, form_data)
    )
    title = 'House Pirce in ' + target_currency
    mimetype = 'application/vnd.openxmlformats-officedocument.\
    spreadsheetml.sheet'
    response = Response(prepareExcel(lookup, title), mimetype=mimetype)
    response.headers['Content-Type'] = mimetype
    filename = 'attachment; filename=House Price ( '+target_currency+' ).xlsx'
    response.headers['Content-Disposition'] = filename
    return response


def add_figure(lookup):
    x = []
    y = []
    for i in lookup:
        x.append(i['_id'])
        y.append(i['avgPrice'])
    # create a new plot with a title and axis labels
    p = figure(title="YrSold vs SalePrice",
               x_axis_label='Year Sold',
               y_axis_type='log',
               y_axis_label='Sale Price')
    # add a line renderer with legend and line thickness
    p.line(x, y, legend="Sale Price", line_width=2)
    return p
