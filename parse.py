import os
from datetime import date
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'BuenViaje.settings'
django.setup()
from BuenViajeWebPage import models
import csv


def fix(string):
    string = string.strip()
    string = ' '.join(string.split())
    return string


def get_month(month):
    try:
        return int(month)
    except ValueError:
        pass
    month = month.lower()
    if '.' not in month:
        month += '.'
    if month == 'ene.':
        return 1
    elif month == 'feb.' or month == '2.':
        return 2
    elif month == 'mar.':
        return 3
    elif month == 'abr.' or month == 'apr.':
        return 4
    elif month == 'may.':
        return 5
    elif month == 'jun.':
        return 6
    elif month == 'jul.':
        return 7
    elif month == 'ago.':
        return 8
    elif month == 'sep.':
        return 9
    elif month == 'oct.':
        return 10
    elif month == 'nov.':
        return 11
    elif month == 'dic.' or month == 'dec.':
        return 12
    else:
        print(month)


# DONE: No event has "sede"
if __name__ == '__main__':
    with open('eventos.csv') as f:
        excel = csv.reader(f)
        count = 1
        for rows in excel:
            name = rows[0].split('/')
            name_es = fix(name[0])
            name_en = None
            if len(name) > 1:
                name_en = fix(name[1])
            if '/' in rows[1]:
                month_f1 = rows[1].split('/')
                month_f1[0], month_f1[1] = month_f1[1], month_f1[0]
            else:
                month_f1 = rows[1].split('-')
            if '/' in rows[2]:
                month_f2 = rows[2].split('/')
                month_f2[0], month_f2[1] = month_f2[1], month_f2[0]
            else:
                month_f2 = rows[2].split('-')
            if len(month_f1) == 1:
                f_inicio = date(2016, get_month(month_f1[0][:3]), 1)
                f_final = date(2016, get_month(month_f1[0][:3]), 29)
            else:
                f_inicio = date(2016, get_month(month_f1[1][:3]), int(month_f1[0]))
                f_final = date(2016, get_month(month_f2[1][:3]), int(month_f2[0]))
            provincia = rows[3].split(',')
            provincia_f = ''
            for x in range(len(provincia)):
                t = fix(provincia[x])
                if len(provincia) - 1 == x:
                    provincia_f += t
                else:
                    provincia_f += t + ', '

            sede = fix(rows[4])
            receptivo = fix(rows[5])
            comite = fix(rows[6])
            tel = fix(rows[7]).replace(';', ',')
            fax = fix(rows[8]).replace(';', ',')
            mail = fix(rows[9])
            web = fix(rows[10])
            tmp = models.Eventos.objects.create(titulo=name_es, en_titulo=name_en or '', fecha_inicio=f_inicio,
                                               fecha_final=f_final, provincia=provincia_f, sede=sede,
                                               receptivo=receptivo, comite=comite, telefono=tel, fax=fax, email=mail,
                                               web=web)
            tmp.save()
            print(name_es)
            print(f_inicio)
            print(f_final)
            print(provincia_f)
            print(sede)
            print(receptivo)
            print(comite)
            print(tel)
            print(fax)
            print(mail)
            print(web)
            print('------------------------------')

            print('This is done!')
