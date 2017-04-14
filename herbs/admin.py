# coding: utf-8

from ajax_select.admin import AjaxSelectAdmin, AjaxSelectAdminTabularInline
from django.contrib import admin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.conf.urls import url
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from .forms import (FamilyForm, GenusForm, HerbItemForm, SpeciesForm,
                    DetHistoryForm, HerbItemFormSimple, AdditionalsForm)
from .models import (Family, Genus, HerbItem, Species, Country,
                     HerbAcronym, DetHistory, Additionals, Subdivision)
from django.forms import model_to_dict
import random
import string
import json



# ------------------- Actions for publishing HerbItems ----------------------

def publish_herbitem(modeladmin, request, queryset):
    total = queryset.count()
    if request.user.is_superuser or request.user.has_perm('herbs.can_set_code'):
        approved_sp = queryset.exclude(species__status='N').count()
        queryset.exclude(species__status='N').update(public=True)
        messages.success(request, 'Опубликовано %s записей' % (approved_sp,))
        if approved_sp != total:
            messages.error(request, 'У %s записей виды не одобрены куратором' % (total - approved_sp))
    else:
        messages.error(request, 'Вы должны быть куратором гербария, чтобы опубликовать записи')


def unpublish_herbitem(modeladmin, request, queryset):
    total = queryset.count()
    if request.user.is_superuser or request.user.has_perm('herbs.can_set_code'):
        queryset.update(public=False)
        messages.success(request, 'Снято с публикации %s записей' % (total,))
    else:
        messages.error(request, 'Вы должны быть куратором гербария, чтобы снять  записи с публикации')


publish_herbitem.short_description = "Опубликовать записи"
unpublish_herbitem.short_description = "Снять с публикации"
# ---------------------------------------------------------------------------


# --------------- Create Pdf-label action -----------------------------------

def create_pdf(modeladmin, request, queryset):
    c = queryset.count()
    if c == 0 or c > 4:
        messages.error(request, 'Выделите не менее одной и не более 4-х гербарных образцов')
        return
    urlfinal = reverse('herbiteminfo', args=[','.join([str(item.pk) for item in queryset])])
    urlfinal += '?'+''.join([random.choice(string.ascii_letters) for k in range(4)])
    return HttpResponseRedirect(urlfinal)
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


class HerbItemCustomListFilter(SimpleListFilter):
    title = 'Пользователь'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        query = HerbAcronym.objects.filter(allowed_users__icontains=request.user.username)
        res = []
        umodel = get_user_model()
        for item in map(lambda s: s.strip(), query[0].allowed_users.split(',')):
            try:
                uinstance = umodel.objects.get(username__iexact=item)
                res.append((uinstance.id, uinstance.username))
            except umodel.DoesNotExist:
                pass
        return tuple(res)
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__id__exact=self.value())
        else:
            return queryset



# -------------- Common per object permission setter ------------------------
class PermissionMixin:

    def queryset(self, request):
        if request.user.is_superuser:
            return self.model.objects.all()
        query = HerbAcronym.objects.filter(allowed_users__icontains=request.user.username)
        if  request.user.has_perm('herbs.can_set_code'):
            subquery = Subdivision.objects.filter(allowed_users__icontains=request.user.username)
            if query.exists() and subquery.exists():
                if hasattr(self.model, 'acronym'):
                    return self.model.objects.filter(acronym__name__iexact=query[0].name,
                                                     subdivision=subquery[0])
            elif query.exists():
                if hasattr(self.model, 'acronym'):
                    return self.model.objects.filter(acronym__name__iexact=query[0].name)
        return self.model.objects.filter(user=request.user)

    def _common_permission_manager(self, request, obj):
        if request.user.is_superuser: return True
        query = HerbAcronym.objects.filter(allowed_users__icontains=request.user.username)
        subquery = Subdivision.objects.filter(allowed_users__icontains=request.user.username)
        if obj is None: return True
        if obj.user is not None:
            if request.user == obj.user: return True
        if request.user.has_perm('herbs.can_set_code'):
            if query.exists() and subquery.exists():
                if obj.subdivision.pk == subquery[0].pk and obj.acronym.pk == query[0].pk:
                    return True
            elif query.exists():
                if obj.acronym.pk == query[0].pk: return True
            else: return False
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            if obj.public:
                return False
        return self._common_permission_manager(request, obj)

    def has_change_permission(self, request, obj=None):
         return self._common_permission_manager(request, obj)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()

# ---------------------------------------------------------------------------

#class HerbImageAdminInline(PermissionMixin, AdminImageMixin,
#                           admin.TabularInline):
#    extra = 0
#    model = HerbImage
#    exclude=('user',)

class DetHistoryAdminInline(AjaxSelectAdminTabularInline):
    extra = 1
    model = DetHistory
    form = DetHistoryForm

class AdditionalsAdminInline(AjaxSelectAdminTabularInline):
    extra = 1
    model = Additionals
    form = AdditionalsForm

class FamilyAdmin(admin.ModelAdmin):
    form = FamilyForm
    search_fields = ('name',)
    list_display = ('id', 'name', 'authorship', 'countobjs')

    def countobjs(self, obj):
       return  HerbItem.objects.filter(species__genus__family=obj).count()
    countobjs.short_description = 'Количество объектов в БД'


class GenusAdmin(AjaxSelectAdmin):
    form = GenusForm
    search_fields = ('name', )
    list_display = ('id', 'name', 'authorship', 'countobjs')

    def countobjs(self, obj):
       return  HerbItem.objects.filter(species__genus=obj).count()
    countobjs.short_description = 'Количество объектов в БД'


class HerbItemAdmin(PermissionMixin, AjaxSelectAdmin):
    model = HerbItem
    search_fields = ('id', 'itemcode', 'fieldid', 'collectedby', 'identifiedby',
                     'species__genus__name', 'species__name')
    actions = (publish_herbitem, unpublish_herbitem, create_pdf, 'delete_selected')
    exclude = ('ecodescr',)

    def delete_selected(self, request, obj):
        nquery = obj.filter(public=False)
        if nquery.exists():
            n = nquery.count()
            nquery.delete()
            messages.success(request, 'Удалено %s гербарных объектов' % n)
        else:
            messages.error(request, 'Нечего удалять. Гербарные образцы должны быть сняты с публикации перед удалением.')
    delete_selected.short_description = 'Удалить гербарные образцы'

    def get_list_display_links(self, request, list_display):
        return ('id', 'get_full_name')


    def get_list_display(self, request):
        if not request.user.has_perm('herbs.can_see_additionals'):
            list_display = ('id', 'get_full_name', 'itemcode', 'public',
                        'collectedby', 'updated', 'collected_s')
        else:
            list_display = ('id', 'get_full_name', 'itemcode', 'fieldid', 'public',
                        'collectedby', 'updated', 'collected_s')
        if request.user.has_perm('herbs.can_set_code') or request.user.is_superuser:
           list_display += ('user',)
        return list_display

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            query = HerbAcronym.objects.filter(allowed_users__icontains=request.user.username)
            if query.exists():
               acronym = query[0]
            else:
                acronym = None
            if not obj.acronym:
                obj.acronym = acronym
            subdquery = Subdivision.objects.filter(allowed_users__icontains=request.user.username)
            if subdquery.exists():
                subd = subdquery[0]
            else:
                subd = None
            if not obj.subdivision:
                obj.subdivision = subd
        if not obj.user:
            obj.user = request.user
        if not obj.createdby:
            obj.createdby = request.user
        if not obj.updatedby or change:
            obj.updatedby = request.user
        obj.save()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(HerbItemAdmin, self).get_readonly_fields(request, obj)
        readonly_fields = list(readonly_fields)
        if 'acronym' not in readonly_fields:
            readonly_fields.append('acronym')
        if 'subdivision' not in readonly_fields:
            readonly_fields.append('subdivision')
        if obj:
            if obj.public:
                readonly_fields = [field.name for field in obj.__class__._meta.fields]
                readonly_fields.remove('ecodescr')
                if request.user.has_perm('herbs.can_set_code'):
                    readonly_fields.remove('public')
                return readonly_fields
        if request.user.has_perm('herbs.can_set_code'):
            if 'public' in readonly_fields:
                readonly_fields.remove('public')
            if 'itemcode' in readonly_fields:
                readonly_fields.remove('itemcode')
        else:
            if 'public' not in readonly_fields:
                readonly_fields.append('public')
            if 'itemcode' not in readonly_fields:
                readonly_fields.append('itemcode')
        if request.user.is_superuser:
            readonly_fields.remove('acronym')
            readonly_fields.remove('subdivision')
        return readonly_fields

    def get_inline_instances(self, request, obj=None):
        inlines = [DetHistoryAdminInline, AdditionalsAdminInline]
        inline_instances = []
        if obj:
            if obj.public:
                return []
        for inl_cl in inlines:
            cur_inline = inl_cl(self.model, self.admin_site)
            if not request.user.has_perm('herbs.can_see_additionals'):
                if not isinstance(cur_inline, AdditionalsAdminInline):
                    inline_instances.append(cur_inline)
            else:
                inline_instances.append(cur_inline)
        return inline_instances

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            if obj.public and HerbItem.objects.filter(id=obj.pk).exists():
                kwargs['form'] = HerbItemFormSimple
                return  super(HerbItemAdmin, self).get_form(request, obj, **kwargs)

        kwargs['form'] = HerbItemForm
        ExtendedForm = super(HerbItemAdmin, self).get_form(request, obj, **kwargs)
        class NewModelForm(ExtendedForm):
            def __new__(self, *args, **kwargs):
                kwargs['request'] = request
                return ExtendedForm(*args, **kwargs)
        return NewModelForm

    def get_list_filter(self, request):
        list_filter = ('public',)
        if request.user.has_perm('herbs.can_set_code'):
            list_filter += (HerbItemCustomListFilter,)
            list_filter += ('acronym',)
        if request.user.is_superuser:
            list_filter = ('user','public', 'acronym')
        return list_filter


#    def save_formset(self, request, form, formset, change):
#        instances = formset.save(commit=False)
#        for instance in instances:
#            if isinstance(instance, HerbImage):
#                if not request.user.is_superuser:
#                    instance.user = request.user
#                instance.save()
#

    def get_urls(self):
        urls = super(HerbItemAdmin, self).get_urls()
        new_urls = [
           url(r'^sfn/(\d{0,15})/(\d?)$',
               self.admin_site.admin_view(self.save_for_next),
               name="save_for_next")
                   ]
        return new_urls + urls

    def save_for_next(self, request, pk, action):
        if action == '1':
            if pk:
                request.session['sfn'] = pk[:10]
                status = True
            else:
                status = False
        elif action == '0':
            try:
                del request.session['sfn']
            except:
                pass
            finally:
                status = False
        else:
            if request.session.get('sfn', False):
                status = True
            else:
                status = False
        return HttpResponse(json.dumps({'status': status}), content_type="application/json;charset=utf-8")


    def add_view(self, request, form_url='', extra_context=None):
            source_id = request.session.get('sfn',None)
            if source_id != None:
                source = HerbItem.objects.get(id=source_id)
                newdict = model_to_dict(source, exclude=['id', 'pk',
                                'itemcode', 'public', 'user'])
                g = request.GET.copy()
                g.update(newdict)
                request.GET = g
            return super(HerbItemAdmin, self).add_view(request, form_url, extra_context)


# PendingHerbsAdmin(admin.ModelAdmin):
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
    list_filter = ('status',)
    search_fields = ('genus__name', )
    list_display = ('id', 'defaultname', 'countobjs')

    def defaultname(self, obj):
        return obj.get_full_name()
    defaultname.short_description = 'Название вида'

    def countobjs(self, obj):
       return  HerbItem.objects.filter(species=obj).count()
    countobjs.short_description = 'Количество объектов в БД'

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            if not request.user.has_perm('herbs.can_change_status'):
                if 'status' not in self.readonly_fields:
                    self.readonly_fields += ('status',)
        else:
            self.readonly_fields = ()
        return super(SpeciesAdmin, self).get_form(request, obj, **kwargs)



#class ErrorLogAdmin(admin.ModelAdmin):
#    list_display = ('message', 'created', 'who')
#    readonly_fields = ('message', 'created', 'who')


admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(HerbAcronym)
admin.site.register(Country)
admin.site.register(Subdivision)
