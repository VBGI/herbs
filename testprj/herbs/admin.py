from django.contrib import admin

# Register your models here.


from .models import (Family, Genus, GenusAuthorship, FamilyAuthorship,
                     SpeciesAuthorship, LoadPendingHerbs,
                     Author, HerbItem, Species, LoadedFiles)
from .forms import (FamilyForm, GenusForm, HerbItemForm,
                    GenusAuthorshipForm, FamilyAuthorshipForm,  AuthorForm,
                    SpeciesForm, SpeciesAuthorshipForm
                    )
from ajax_select.admin import AjaxSelectAdmin, AjaxSelectAdminTabularInline

class AuthorAdmin(admin.ModelAdmin):
    form = AuthorForm 


class FamilyAuthorshipInline(AjaxSelectAdminTabularInline):
    form = FamilyAuthorshipForm
    model = FamilyAuthorship
    extra = 0

class GenusAuthorshipInline(AjaxSelectAdminTabularInline):
    form = GenusAuthorshipForm
    model = GenusAuthorship
    extra = 0

class SpeciesAuthorshipInline(AjaxSelectAdminTabularInline):
    form = SpeciesAuthorshipForm
    model = SpeciesAuthorship
    extra = 0


class FamilyAdmin(admin.ModelAdmin):
    form = FamilyForm
    inlines = (
        FamilyAuthorshipInline,
        )


class GenusAdmin(admin.ModelAdmin):
    form = GenusForm
    inlines = (
        GenusAuthorshipInline,
        )

class HerbItemAdmin(AjaxSelectAdmin):
    form = HerbItemForm
    list_display = ('get_full_name', 'gcode','itemcode','family', 'genus', 'species','collectors','collected_s')
    list_filter = ('public', 'family', 'genus', 'species')
    inlines = (
        SpeciesAuthorshipInline,
        )
    
class LoadPendingHerbsAdmin(admin.ModelAdmin):
    model = LoadPendingHerbs
    list_display = ('get_full_name', 'checked','itemcode','family', 'genus', 'species','collectors','collected_s')
    list_filter = ('public', 'family', 'genus', 'species')


class LoadedFilesAdmin(admin.ModelAdmin):
    model = LoadedFiles
    list_display = ('datafile', 'status','createdby', 'created')
    list_filter = ('status', 'createdby')

class SpeciesAdmin(admin.ModelAdmin): 
    form = SpeciesForm


admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(LoadPendingHerbs, LoadPendingHerbsAdmin)
admin.site.register(LoadedFiles, LoadedFilesAdmin)
