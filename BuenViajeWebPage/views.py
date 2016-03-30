from django.shortcuts import render


# Create your views here.
def fix_coma(value):
    return [x.strip() for x in value.strip().split(',')]


def fix_month(x, trigger=False):
    if trigger:
        if x.lower() == 'enero':
            return 1, 'Enero', 'January'
        elif x.lower() == 'febrero':
            return 2, 'Febrero', 'February'
        elif x.lower() == 'marzo':
            return 3, 'Marzo', 'March'
        elif x.lower() == 'abril':
            return 4, 'Abril', 'April'
        elif x.lower() == 'mayo':
            return 5, 'Mayo', 'May'
        elif x.lower() == 'junio':
            return 6, 'Junio', 'June'
        elif x.lower() == 'julio':
            return 7, 'Julio', 'July'
        elif x.lower() == 'agosto':
            return 8, 'Agosto', 'August'
        elif x.lower() == 'septiembre':
            return 9, 'Septiembre', 'September'
        elif x.lower() == 'octubre':
            return 10, 'Octubre', 'October'
        elif x.lower() == 'noviembre':
            return 11, 'Noviembre', 'November'
        else:
            return 12, 'Diciembre', 'December'
    if x == 1:
        return 1, 'Enero', 'January'
    elif x == 2:
        return 2, 'Febrero', 'February'
    elif x == 3:
        return 3, 'Marzo', 'March'
    elif x == 4:
        return 4, 'Abril', 'April'
    elif x == 5:
        return 5, 'Mayo', 'May'
    elif x == 6:
        return 6, 'Junio', 'June'
    elif x == 7:
        return 7, 'Julio', 'July'
    elif x == 8:
        return 8, 'Agosto', 'August'
    elif x == 9:
        return 9, 'Septiembre', 'September'
    elif x == 10:
        return 10, 'Octubre', 'October'
    elif x == 11:
        return 11, 'Noviembre', 'November'
    else:
        return 12, 'Diciembre', 'December'


def fix_months(collection):
    res = []
    for x in collection:
        res.append(fix_month(x))
    return res
