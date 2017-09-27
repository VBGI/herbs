# coding: utf-8

from ajax_select.admin import AjaxSelectAdmin, AjaxSelectAdminTabularInline
from django.contrib import admin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.conf.urls import url
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from .forms import (FamilyForm, GenusForm, HerbItemForm, SpeciesForm,
                    DetHistoryForm, HerbItemFormSimple, AdditionalsForm)
from .models import (Family, Genus, HerbItem, Species, Country,
                     HerbAcronym, DetHistory, Additionals, Subdivision,
                     SpeciesSynonym)
from django.forms import model_to_dict
from django.utils.text import capfirst
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import random
import string
import json


# ------------------- Actions for publishing HerbItems ----------------------

def publish_herbitem(modeladmin, request, queryset):
    total = queryset.count()
    if request.user.has_perm('herbs.can_set_publish'):
        approved_sp = queryset.exclude(species__status='N').exclude(species__status='D').count()
        queryset.exclude(species__status='N').exclude(species__status='D').update(public=True, updatedby=request.user)
        messages.success(request, _(u'Опубликовано %s записей') % (approved_sp,))
        if approved_sp != total:
            messages.error(request, _(u'У %s записей виды не одобрены куратором') % (total - approved_sp))
    else:
        messages.error(request, _(u'Вы должны быть куратором гербария, чтобы опубликовать записи'))


def unpublish_herbitem(modeladmin, request, queryset):
    total = queryset.count()
    if request.user.has_perm('herbs.can_set_publish'):
        queryset.update(public=False, updatedby=request.user)
        messages.success(request, _(u'Снято с публикации %s записей') % (total,))
    else:
        messages.error(request, _(u'Вы должны быть куратором гербария, чтобы снять  записи с публикации'))


publish_herbitem.short_description = _(u"Опубликовать записи")
unpublish_herbitem.short_description = _(u"Снять с публикации")
# ---------------------------------------------------------------------------


# --------------- Create Pdf actions ----------------------------------------

def create_pdf(modeladmin, request, queryset):
    c = queryset.count()
    if c == 0 or c > 100:
        messages.error(request, _(u'Выделите не менее одной и не более 100 гербарных образцов'))
        return
    urlfinal = reverse('herbiteminfo', args=[','.join([str(item.pk) for item in queryset])])
    urlfinal += '?'+''.join([random.choice(string.ascii_letters) for k in range(4)])
    return HttpResponseRedirect(urlfinal)
create_pdf.short_description = _(u"Создать этикетки")


def create_pdf_envelope(modeladmin, request, queryset):
    c = queryset.count()
    if c == 0 or c > 100:
        messages.error(request, _(u'Выделите не менее одной и не более 100 гербарных образцов'))
        return
    urlfinal = reverse('herbitembryo', args=[','.join([str(item.pk) for item in queryset])])
    urlfinal += '?'+''.join([random.choice(string.ascii_letters) for k in range(4)])
    return HttpResponseRedirect(urlfinal)
create_pdf_envelope.short_description = _(u"Создать этикетки-конверты")


def create_barcodes(modeladmin, request, queryset):
    c = queryset.count()
    if c == 0 or c > 100:
        messages.error(request, _(u'Выделите не менее одной и не более 100 гербарных образцов'))
        return
    urlfinal = reverse('herbitembarcodes', args=[','.join([str(item.pk) for item in queryset])])
    urlfinal += '?'+''.join([random.choice(string.ascii_letters) for k in range(4)])
    return HttpResponseRedirect(urlfinal)
create_barcodes.short_description = _(u"Создать штрихкоды")

# ---------------------------------------------------------------------------

class HerbItemCustomListFilter(SimpleListFilter):
    title = _('Пользователь')
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
        if  request.user.has_perm('herbs.can_set_publish'):
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
        if request.user.has_perm('herbs.can_set_publish'):
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

# ---------------------------------------------------------------------------

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
    countobjs.short_description = _('Количество объектов в БД')


class GenusAdmin(AjaxSelectAdmin):
    form = GenusForm
    search_fields = ('name', )
    list_display = ('id', 'name', 'authorship', 'countobjs')

    def countobjs(self, obj):
       return  HerbItem.objects.filter(species__genus=obj).count()
    countobjs.short_description = _('Количество объектов в БД')


class HerbItemAdmin(PermissionMixin, AjaxSelectAdmin):
    model = HerbItem
    search_fields = ('id', 'itemcode', 'fieldid', 'collectedby', 'identifiedby',
                     'species__genus__name', 'species__name')
    actions = (publish_herbitem, unpublish_herbitem, create_pdf, create_barcodes,
               create_pdf_envelope, 'delete_selected')
    exclude = tuple()

    def delete_selected(self, request, obj):
        nquery = obj.filter(public=False)
        if nquery.exists():
            n = nquery.count()
            nquery.delete()
            messages.success(request, _('Удалено %s гербарных объектов') % n)
        else:
            messages.error(request, _('Нечего удалять. Гербарные образцы должны быть сняты с публикации перед удалением.'))
    delete_selected.short_description = _('Удалить гербарные образцы')

    def get_list_display_links(self, request, list_display):
        return ('id', 'get_full_name')

    def edit_related_species(self, obj):
        if obj.species:
            url = reverse('admin:%s_%s_change' %('herbs', 'species'),
                          args=[obj.species.pk])
            resurl = '<a href="%s" title="%s">Edit sp.</a>'  % (url, capfirst(obj.species.get_full_name()))
        else:
            resurl = '--'
        return resurl
    edit_related_species.allow_tags = True
    edit_related_species.short_description = _('Вид')

    def get_list_display(self, request):
        if not request.user.has_perm('herbs.can_see_additionals'):
            list_display = ('id', 'get_full_name', 'itemcode', 'public',
                        'collectedby', 'updated', 'collected_s')
        else:
            list_display = ('id', 'get_full_name', 'itemcode', 'fieldid', 'public',
                        'collectedby', 'updated', 'collected_s')
        if request.user.has_perm('herbs.can_set_publish'):
           list_display += ('user', 'edit_related_species')
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
        obj.updatedby = request.user
        if obj.coordinates:
            lat = obj.coordinates.latitude
            lon = obj.coordinates.longitude
        else:
            lat = None
            lon = None
        try:
            obj.latitude = float(lat)
            obj.longitude = float(lon)
        except (ValueError, TypeError):
            pass
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
                if request.user.has_perm('herbs.can_set_publish'):
                    readonly_fields.remove('public')
                return readonly_fields
        if request.user.has_perm('herbs.can_set_publish'):
            if 'public' in readonly_fields:
                readonly_fields.remove('public')
            if 'itemcode' in readonly_fields:
                readonly_fields.remove('itemcode')
        elif request.user.has_perm('herbs.can_set_code'):
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
        if not request.user.has_perm('herbs.can_see_additionals'):
            if 'short_note' not in self.exclude:
                self.exclude += ('short_note', )
        else:
            if 'short_note' in self.exclude:
                self.exclude = tuple()
        ExtendedForm = super(HerbItemAdmin, self).get_form(request, obj, **kwargs)
        class NewModelForm(ExtendedForm):
            def __new__(self, *args, **kwargs):
                kwargs['request'] = request
                return ExtendedForm(*args, **kwargs)
        return NewModelForm

    def get_list_filter(self, request):
        list_filter = ('public',)
        if request.user.has_perm('herbs.can_set_publish'):
            list_filter += (HerbItemCustomListFilter,)
        if request.user.is_superuser:
            list_filter = ('user','public', 'acronym')
        return list_filter


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


class SpeciesAdmin(AjaxSelectAdmin):
    form = SpeciesForm
    list_filter = ('status',)
    search_fields = ('genus__name', )
    list_display = ('id', 'defaultname', 'countobjs', 'status')

    def defaultname(self, obj):
        return obj.get_full_name()
    defaultname.short_description = _('Название вида')

    def countobjs(self, obj):
        res = _('Основные виды: ') + str(HerbItem.objects.filter(species=obj).count()) +\
             ' | ' + _('Переопределенные: ') + str(DetHistory.objects.filter(species=obj).exclude(herbitem__isnull=True).count()) +\
             ' | ' + _('Дополнительные: ') + str(Additionals.objects.filter(species=obj).exclude(herbitem__isnull=True).count())
        return res
    countobjs.short_description = _('Количество объектов в БД')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(SpeciesAdmin, self).get_readonly_fields(request, obj)
        readonly_fields = list(readonly_fields)

        if request.user.has_perm('herbs.can_set_publish'):
            readonly_fields = list()
        else:
            readonly_fields += ['status',]

        if obj:
            if not request.user.is_superuser:
                if obj.updated and obj.status == 'A':
                    if obj.updated < (timezone.now() - timedelta(days=settings.APPROVED_SPECIES_FREEZE)).date():
                        readonly_fields = obj._meta.get_all_field_names()
        return readonly_fields


admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(HerbAcronym)
admin.site.register(Country)
admin.site.register(Subdivision)
admin.site.register(SpeciesSynonym)
