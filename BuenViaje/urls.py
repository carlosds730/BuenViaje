"""BuenViaje URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from BuenViajeWebPage import views

urlpatterns = []

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^numeros-anteriores/?$', views.old_revistas),
    url(r'^email_to_send/?$', views.notification),
    url(r'^contactenos/?$',
        views.contactenos),
    url(r'^informacion-de-cuba/?$',
        views.de_cuba),
    url(r'^unsubscribe/?$',
        views.unsubscribe),
    url(
        r'^noticia/(?P<slug>[-\w]+)/?$',
        views.noticia),
    url(r'^noticias/?$',
        views.noticias),
    url(r'^imagen/(?P<id>\d+)/?$',
        views.imagen),
    url(
        r'^ajax_noticias/(?P<id>\d+)/?$',
        views.ajax_noticias),
    url(r'^photo/?$', views.photo),
    url(r'^eventos-proximo-anho/?$',
        views.proximo_anho),
    url(r'^la_revista/?$',
        views.la_revista),
    url(r'^distribucion/?$',
        views.distribucion),
    url(r'^informacion-general/?$',
        views.informacion_general),
    url(r'^informacion-destinos/?$',
        views.informacion_destinos),
    url(r'^imagenes/?$',
        views.imagenes),
    url(r'^propuestas/?$',
        views.tiempo_libre),
    url(
        r'^eventos/(?P<month>[-\w]+)/?$',
        views.eventos_month),
    url(r'^eventos/?$',
        views.eventos),
    url(r'^search/?$',
        views.search),
    url(r'^ajax_photo/?$',
        views.ajax_photo_upload),
    url(r'^subscribe/?$',
        views.subscribe),
    url(r'^change_language/?$',
        views.change_language,
        name='change_language'),
    url(r'^admin/', admin.site.urls),
    url(r'^newsletter/', include('newsletter.urls')),
    url(r'^ tinymce/', include('tinymce.urls')),
    url(r'^$', views.inicio),
    url(r'^', views.error)
]
