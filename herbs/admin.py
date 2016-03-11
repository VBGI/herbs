from django.contrib import admin
import autocomplete_light

# Register your models here.


from .models import Family, Genus, OrderedAuthor, Author, HerbItem, Species
from .forms import (FamilyForm, GenusForm, HerbItemForm,
                    OrderedAuthorForm, AuthorForm,
                    SpeciesForm
                    )


class FamilyAdmin(admin.ModelAdmin):
    form = FamilyForm


class GenusAdmin(admin.ModelAdmin):
    form = GenusForm


class HerbItemAdmin(admin.ModelAdmin):
#     form = autocomplete_light.modelform_factory(HerbItem, fields='__all__')
    form = HerbItemForm
    list_display = ('gcode','itemcode','family', 'genus', 'species','collectors','collected_s')
    list_filter = ('family', 'genus', 'species')
    
    

class OrderedAuthorAdmin(admin.ModelAdmin):
    form = OrderedAuthorForm


class AuthorAdmin(admin.ModelAdmin):
    form = AuthorForm 


class SpeciesAdmin(admin.ModelAdmin): 
    form = SpeciesForm


admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(OrderedAuthor, OrderedAuthorAdmin)
admin.site.register(Species, SpeciesAdmin)


