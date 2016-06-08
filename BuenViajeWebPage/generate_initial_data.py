import os
import django
from datetime import datetime, date, timedelta
from random import randint

os.environ['DJANGO_SETTINGS_MODULE'] = 'BuenViaje.settings'
django.setup()

from BuenViajeWebPage.models import (Noticia, Blog, Publicidades, Seccion, Secciones_informacion_general,
                                     Seccion_Cuba_Informacion_Destino, Eventos)
from autofixture import AutoFixture, generators


def generate_sample_from_model(model, num):
    """
    Generate num instances of model
    """
    fixture = AutoFixture(model)
    entries = fixture.create(num)
    return entries


# TODO: Generate random date
def generate_random_date(init_date=datetime.now(), end_date=datetime.now()):
    return datetime.now()



# TODO: When blog=False, try to assign the news randomly to a blog or to None
# TODO: Try to generate random positions
def generate_news(position, num_par=False, blog=False, size=False):
    """
    :param num_par: indicates the number of paragraphs per news, if False the number is random betwen 1 an 7
    :type num_par: int
    :param blog: Indicates if the news should be in an specific blog (set blog=None if the news should have no blog)
    :type blog: Blog or False
    :return:
    :rtype: AutoFixture
    """
    if not num_par:
        num_par = randint(1, 7)

    field_values = {
        'titulo': generators.LoremSentenceGenerator(max_length=100),
        'en_titulo': generators.LoremSentenceGenerator(max_length=100),
        'short_text': generators.LoremGenerator(max_length=200),
        'en_short_text': generators.LoremGenerator(max_length=200),
        'texto': generators.LoremHTMLGenerator(count=num_par),
        'en_texto': generators.LoremHTMLGenerator(count=num_par),
        'position': position
    }
    if blog or blog is None:
        field_values.update({'blog': blog})

    if size:
        field_values.update({'imagen': generators.ImageGenerator(sizes=size)})

    return AutoFixture(Noticia, field_values=field_values)


def generate_publicitiy(position, size=False):
    field_values = {
        'position': position,
    }
    if size:
        field_values.update({'imagen': generators.ImageGenerator(sizes=size)})

    return AutoFixture(Publicidades, field_values=field_values)


def generate_section(num_par=False):
    if not num_par:
        num_par = randint(1, 7)

    field_values = {
        'titulo': generators.LoremSentenceGenerator(max_length=10, count=50),
        'en_titulo': generators.LoremSentenceGenerator(max_length=10, count=50),
        'descripcion': generators.LoremHTMLGenerator(count=num_par),
        'en_descripcion': generators.LoremHTMLGenerator(count=num_par),
        'image': generators.ImageGenerator(sizes=((185, 245),))
    }

    return AutoFixture(Seccion, field_values=field_values)


def generate_cuba_info_general():
    num_par = randint(1, 5)
    count = randint(1, 5)
    field_values = {
        'titulo': generators.LoremSentenceGenerator(max_length=30, count=count),
        'en_titulo': generators.LoremSentenceGenerator(max_length=30, count=count),
        'texto': generators.LoremHTMLGenerator(count=num_par),
        'en_texto': generators.LoremHTMLGenerator(count=num_par),
    }

    return AutoFixture(Secciones_informacion_general, field_values=field_values)


def generate_destinos(num_par=False):
    if not num_par:
        num_par = randint(1, 5)

    field_values = {
        'nombre': generators.LoremSentenceGenerator(max_length=50),
        'en_nombre': generators.LoremSentenceGenerator(max_length=50),
        'descripcion_corta': generators.LoremGenerator(max_length=500),
        'en_descripcion_corta': generators.LoremGenerator(max_length=500),
        'texto': generators.LoremHTMLGenerator(count=num_par),
        'en_texto': generators.LoremHTMLGenerator(count=num_par),
        'imagen': generators.ImageGenerator(sizes=((100, 75),))
    }

    return AutoFixture(Seccion_Cuba_Informacion_Destino, field_values=field_values)


def generate_event():
    max_date = date(2016, 12, 31)
    min_date = date(2016, 1, 1)
    diff = max_date - min_date
    days = randint(0, diff.days)
    init_date = min_date + timedelta(days=days)
    end_date = init_date + timedelta(days=randint(0, 15))
    field_values = {
        'imagen': generators.ImageGenerator(sizes=((75, 125),)),
        'fecha_inicio': init_date,
        'fecha_final': end_date,
    }
    return AutoFixture(Eventos, field_values=field_values)


def generate_stuffs():
    # generate_news().create(10)
    generate_news("principal", blog=None, size=((710, 375),)).create(5)
    generate_news("p_bloque", blog=None).create(10)
    generate_news("s_bloque", blog=None, size=((130, 100),)).create(10)
    generate_publicitiy("principal", size=((594, 61),)).create(4)
    generate_publicitiy("p_bloque", size=((272, 140),)).create(9)
    generate_publicitiy("s_bloque", size=((272, 100),)).create(9)


# generate_section(num_par=1).create(10)
# generate_cuba_info_general().create(20)
# generate_destinos().create(15)
# for k in range(0, 50):
#     generate_event().create(1)
generate_stuffs()
