from django.contrib import admin

# Register your models here.


from .models import Family, Genus
from .forms import FamilyForm, GenusForm, HerbItem


class FamilyAdmin(admin.ModelAdmin):
    form = FamilyForm

class GenusAdmin(admin.ModelAdmin):
    form = GenusForm

admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)