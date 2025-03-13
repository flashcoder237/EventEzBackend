from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# Personnaliser le titre et l'en-tête
admin.site.site_header = _('Administration EventEz')
admin.site.site_title = _('Eventez - Panneau administrateur')
admin.site.index_title = _('Tableau de bord')