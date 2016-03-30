from django.db import models
from sorl.thumbnail import ImageField
from sorl.thumbnail import get_thumbnail
# from django.core.validators import email_re
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from tinymce import models as tinymce_models
from django.conf import settings


# from date_utils import edit_fecha, edit_fecha_evento

class Banner(models.Model):
    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'

    titulo = models.CharField(max_length=200, verbose_name='Titulo')

    en_title = models.CharField(max_length=200, verbose_name='Title')

    url = models.URLField(verbose_name='Url', name='url', blank=True, null=True)

    imagen = ImageField(verbose_name='Imagen', upload_to='own')

    def get_small_thumbnail(self, size):
        return get_thumbnail(self.imagen, size, upscale=False)

    def __str__(self):

        return self.titulo
