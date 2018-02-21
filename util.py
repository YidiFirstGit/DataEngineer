# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 13:49:22 2018

@author: Yidi Gu
"""
import io
import openpyxl  # work with excel file
import numpy as np
import random
import pymongo


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
    columns = [i for i in data[0].keys()]
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


def create_dataframe_with_currency(form_data):
    form_data['YrSold'] = int(form_data['YrSold'])
    form_data['SalePrice'] = int(form_data['SalePrice'])
    ID = list(cl.find())[-1]['Id']+1
    form_data['Id'] = ID
    form_data['currency'] = random.choice(cl_currency.distinct('currency'))
    return form_data
