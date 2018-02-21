def transform_datatype(form_data):
    form_data = {k: int(v) if str(v).isdigit() else v
                 for k, v in form_data.items()}
    return tranform
