from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin
from django.utils.translation import ugettext
# from forms import ImageForm, EventsForm
import BuenViajeWebPage.models as models


class AdminBanner(AdminImageMixin, admin.ModelAdmin):
    pass


admin.site.register(models.Banner, AdminBanner)
