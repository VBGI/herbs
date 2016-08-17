from django.contrib import admin

# Register your models here.


from .models import (Family, Genus, GenusAuthorship, FamilyAuthorship,
                     SpeciesAuthorship, LoadPendingHerbs,
                     Author, HerbItem, Species, LoadedFiles)
from .forms import (FamilyForm, GenusForm, HerbItemForm,
                    GenusAuthorshipForm, FamilyAuthorshipForm,  AuthorForm,
                    SpeciesForm, SpeciesAuthorshipForm
                    )


class AuthorAdmin(admin.ModelAdmin):
    form = AuthorForm 


class FamilyAuthorshipInline(admin.TabularInline):
    model = FamilyAuthorship
    extra = 0

class GenusAuthorshipInline(admin.TabularInline):
    model = GenusAuthorship
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

class HerbItemAdmin(admin.ModelAdmin):
    form = HerbItemForm
    list_display = ('get_full_name', 'gcode','itemcode','family', 'genus', 'species','collectors','collected_s')
    list_filter = ('public', 'family', 'genus', 'species')
    
    
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
