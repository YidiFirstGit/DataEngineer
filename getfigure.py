def figure_setting(title, tool, axis, x_axis_type, x_range):
    return figure(title=title, plot_width=1000, plot_height=700,
                  tools=tool, x_axis_label=axis.x_label,
                  y_axis_label=axis.y_label, x_axis_type=x_axis_type,
                  x_rang=x_range)


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
