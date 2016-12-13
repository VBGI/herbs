# coding: utf-8

from ajax_select.admin import AjaxSelectAdmin, AjaxSelectAdminTabularInline
from django.contrib import admin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from .forms import FamilyForm, GenusForm, HerbItemForm, SpeciesForm
from .models import (Family, Genus, HerbItem, Species,
                     HerbImage, HerbAcronym)

from sorl.thumbnail.admin import AdminImageMixin


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


# --------------- Create Pdf-label action -----------------------------------

def create_pdf(modeladmin, request, queryset):
    c = queryset.count()
    if c == 0 or c > 4:
        messages.error(request, 'Выделите не менее одной и не более 4-х гербарных образцов')
        return
    return HttpResponseRedirect(reverse('herbiteminfo', args=[','.join([str(item.pk) for item in queryset])]))
create_pdf.short_description = "Создать этикетки"

# ---------------------------------------------------------------------------


# Temporarily removed functionality
# ------------------- Herbitem creation -------------------------------------
#def move_pending_herbs(modeladmin, request, queryset):
#    total = queryset.count()
#    count = 0
#    for obj in queryset:
#        if not obj.err_msg and obj.checked:
#            kwargs = {key: getattr(obj, key) for key in _fields_to_copy}
#            HerbItem.objects.create(public=False, **kwargs)
#            obj.delete()
#            count += 1
#    messages.success(request, 'Перемещено %s из %s выбранных' % (count, total))
#
#move_pending_herbs.short_description = "Переместить в базу гербария"
#
#
#def force_move_pending_herbs(modeladmin, request, queryset):
#    total = queryset.count()
#    count = 0
#    for obj in queryset:
#        kwargs = {key: getattr(obj, key) for key in _fields_to_copy}
#        HerbItem.objects.create(public=False, **kwargs)
#        obj.delete
#        count += 1
#    messages.success(request, 'Перемещено %s из %s выбранных' % (count, total))
#force_move_pending_herbs.short_description = "Переместить в базу игнорируя ошибки"
## ---------------------------------------------------------------------------



# -------------- Common per object permission setter ------------------------
class PermissionMixin:

    def queryset(self, request):
        if request.user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.filter(user=request.user)

    def _common_permission_manager(self, request, obj):
        if obj is None: return True
        if obj.user is not None:
            if request.user == obj.user: return True
        if request.user.is_superuser:
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        return self._common_permission_manager(request, obj)

    def has_change_permission(self, request, obj=None):
         return self._common_permission_manager(request, obj)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.user = request.user
        obj.save()

# ---------------------------------------------------------------------------

class HerbImageAdminInline(PermissionMixin, AdminImageMixin,
                           admin.TabularInline):
    extra = 0
    model = HerbImage
    exclude=('user',)


class FamilyAdmin(admin.ModelAdmin):
    form = FamilyForm


class GenusAdmin(AjaxSelectAdmin):
    form = GenusForm


class HerbItemAdmin(PermissionMixin, AjaxSelectAdmin):
    model = HerbItem
    form = HerbItemForm
    list_display = ('get_full_name', 'itemcode', 'public',
                    'collectedby', 'collected_s')
    list_filter = ('public', 'species__genus__family__name',
                   'species__genus__name', 'species__name')
    search_fields = ('itemcode', 'collectedby', 'identifiedby',
                     'species__genus__family__name', 'species__genus__name',
                     'species__name')
    list_display_links = ('get_full_name', 'species__genus__family__name')
    actions = (publish_herbitem, unpublish_herbitem, create_pdf)
    inlines = (HerbImageAdminInline, )

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            query = HerbAcronym.objects.filter(allowed_users__icontains=request.user.username)
            if query.exists():
               acronym = query[0]
            else:
                acronym = None
            if not obj.acronym:
                obj.acronym = acronym
            if not obj.user:
                obj.user = request.user
            else:
                if request.user != obj.user:
                    return
        obj.save()

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            if 'acronym' not in self.readonly_fields:
                self.readonly_fields += ('acronym',)
        else:
            self.readonly_fields = ()
        return super(HerbItemAdmin, self).get_form(request, obj, **kwargs)


    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, HerbImage):
                if not request.user.is_superuser:
                    instance.user = request.user
                instance.save()


#class PendingHerbsAdmin(admin.ModelAdmin):
#    model = PendingHerbs
#    list_display = ('get_full_name', 'itemcode', 'checked', 'err_msg')
#    list_filter = ('public', 'family', 'genus', 'species')
#    list_display_links = ('get_full_name',)
#    actions = (force_move_pending_herbs, move_pending_herbs)
#
#
#class LoadedFilesAdmin(admin.ModelAdmin):
#    model = LoadedFiles
#    list_display = ('datafile', 'status', 'createdby', 'created')
#    list_filter = ('status', 'createdby')
#

class SpeciesAdmin(AjaxSelectAdmin):
    form = SpeciesForm
    inlines = (
        SpeciesAuthorshipInline,
        )


#class ErrorLogAdmin(admin.ModelAdmin):
#    list_display = ('message', 'created', 'who')
#    readonly_fields = ('message', 'created', 'who')


admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(HerbAcronym)
