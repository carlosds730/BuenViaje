import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'BuenViaje.settings'
django.setup()

import BuenViajeWebPage.models as models
from autofixture import AutoFixture


def generate_sample_from_model(model, num):
    """
    Generate num instances of model
    """
    fixture = AutoFixture(model)
    entries = fixture.create(num)
    return entries

