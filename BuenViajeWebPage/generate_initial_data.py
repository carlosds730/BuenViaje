import BuenViajeWebPage.models as models
from autofixture import AutoFixture


def generate_sample_from_model(model, num):
    fixture = AutoFixture(model)
    entries = fixture.create(num)
    return entries


generate_sample_from_model(models.Noticia, 10)
