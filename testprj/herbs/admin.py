# coding: utf-8
from ajax_select.admin import AjaxSelectAdmin, AjaxSelectAdminTabularInline
from django.contrib import admin
from django.contrib import messages

from .forms import (FamilyForm, GenusForm, HerbItemForm,
                    GenusAuthorshipForm, FamilyAuthorshipForm, AuthorForm,
                    SpeciesForm, SpeciesAuthorshipForm
                    )
from .models import (Family, Genus, GenusAuthorship, FamilyAuthorship,
                     SpeciesAuthorship, PendingHerbs,
                     Author, HerbItem, Species, LoadedFiles,
                     ErrorLog, _fields_to_copy)

# ------------------- Actions for publishing HerbItems ----------------------


def publish_herbitem(modeladmin, request, queryset):
    total = queryset.count()
    queryset.update(public=True)
    messages.success(request, 'Опубликовано %s записей' % (total,))


def unpublish_herbitem(modeladmin, request, queryset):
    total = queryset.count()
    queryset.update(public=False)
    messages.success(request, 'Снято с публикации %s записей' % (total,))

publish_herbitem.short_description = "Опубликовать записи"
unpublish_herbitem.short_description = "Снять с публикации"
# ---------------------------------------------------------------------------


# ------------------- Herbitem creation -------------------------------------
def move_pending_herbs(modeladmin, request, queryset):
    total = queryset.count()
    count = 0
    for obj in queryset:
        if not obj.err_msg and obj.checked:
            kwargs = {key: getattr(obj, key) for key in _fields_to_copy}
            HerbItem.objects.create(public=False, **kwargs)
            obj.delete()
            count += 1
    messages.success(request, 'Перемещено %s из %s выбранных' % (count, total))

move_pending_herbs.short_description = "Переместить в базу гербария"


def force_move_pending_herbs(modeladmin, request, queryset):
    total = queryset.count()
    count = 0
    for obj in queryset:
        kwargs = {key: getattr(obj, key) for key in _fields_to_copy}
        HerbItem.objects.create(public=False, **kwargs)
        obj.delete
        count += 1
    messages.success(request, 'Перемещено %s из %s выбранных' % (count, total))
force_move_pending_herbs.short_description = "Переместить в базу игнорируя ошибки"
# ---------------------------------------------------------------------------


# Register your models here.
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


class GenusAdmin(AjaxSelectAdmin):
    form = GenusForm
    inlines = (
        GenusAuthorshipInline,
        )


class HerbItemAdmin(AjaxSelectAdmin):
    form = HerbItemForm
    list_display = ('family', 'get_full_name', 'gcode', 'itemcode', 'public', 'collectedby', 'collected_s')
    list_filter = ('public', 'family', 'genus', 'species')
    search_fields = ('itemcode', 'gcode', 'collectedby', 'identifiedby', 'family__name', 'genus__name')
    list_display_links = ('get_full_name',)
    actions = (publish_herbitem, unpublish_herbitem)


class PendingHerbsAdmin(admin.ModelAdmin):
    model = PendingHerbs
    list_display = ('get_full_name', 'itemcode', 'gcode', 'checked', 'err_msg')
    list_filter = ('public', 'family', 'genus', 'species')
    list_display_links = ('get_full_name',)
    actions = (force_move_pending_herbs, move_pending_herbs)


class LoadedFilesAdmin(admin.ModelAdmin):
    model = LoadedFiles
    list_display = ('datafile', 'status', 'createdby', 'created')
    list_filter = ('status', 'createdby')


class SpeciesAdmin(AjaxSelectAdmin):
    form = SpeciesForm
    inlines = (
        SpeciesAuthorshipInline,
        )


class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('message', 'created', 'who')
    readonly_fields = ('message', 'created', 'who')


admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(PendingHerbs, PendingHerbsAdmin)
admin.site.register(LoadedFiles, LoadedFilesAdmin)
admin.site.register(ErrorLog, ErrorLogAdmin)
