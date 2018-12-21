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
from django.db import models
from .forms import (FamilyForm, GenusForm, HerbItemForm, SpeciesForm,
                    DetHistoryForm, HerbItemFormSimple, AdditionalsForm)
from .models import (Family, Genus, HerbItem, Species, Country,
                     HerbAcronym, DetHistory, Additionals, Subdivision,
                     SpeciesSynonym, HerbReply, Notification)
from django.forms import model_to_dict
from django.utils.text import capfirst
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from six import string_types
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
        messages.error(request, _(u'Вы должны быть куратором гербария, чтобы снять записи с публикации'))


publish_herbitem.short_description = _(u"Опубликовать записи")
unpublish_herbitem.short_description = _(u"Снять с публикации")
# ---------------------------------------------------------------------------

# --------------- Auxiliary getting functions -------------------------------

def get_subdivision_or_none(request):
    subquery = Subdivision.objects.filter(allowed_users__icontains=request.user.username)
    if not subquery.exists():
        return None
    else:
        return subquery[0]

def get_acronym_or_none(request):
    query = HerbAcronym.objects.filter(allowed_users__icontains=request.user.username)
    if not query.exists():
        return None
    else:
        return query[0]

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
        res = []
        acronym = get_acronym_or_none(request)
        if acronym:
            umodel = get_user_model()
            for item in map(lambda s: s.strip(), acronym.allowed_users.split(',')):
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


# ------------ Notification base bahavior --------------
class NotificationMixin:
    '''
    Creates notifications according to changes in predefined model fields
    '''

    def make_notification(self, request, obj):
        if not obj:
            return
        acronym = obj.acronym.name if obj.acronym else ''
        username = request.user.username

        if username in settings.HERBS_EXCLUDED_FROM_NOTIFICATION:
            return

        for field_name in settings.HERBS_TRACKED_FIELDS:
            field_value = getattr(obj, field_name, '')
            friendly_value = ''
            if isinstance(field_value, models.Model):
                field_name = field_name + '__pk'
                friendly_value = str(field_value)
                field_value = getattr(field_value, 'pk')
                friendly_value += ' ({})'.format(field_value)
                if field_value is None:
                    field_value = ''
            elif isinstance(field_value, string_types):
                field_value = field_value.strip()
                friendly_value = field_value
            else:
                field_value = ''

            if self._notification_condition(obj.__class__,
                                            field_name, field_value,
                                            acronym):
                emails = self._get_mails(obj, acronym)
                if emails:
                    Notification.objects.filter(tracked_field=field_name,
                                                hitem=obj,
                                                status='Q').delete()
                    Notification.objects.get_or_create(
                                                   tracked_field=field_name,
                                                   field_value=friendly_value,
                                                   username=username,
                                                   hitem=obj,
                                                   emails=emails)

            else:
                Notification.objects.filter(tracked_field=field_name,
                                            status='Q',
                                            hitem=obj).delete()


    @staticmethod
    def _notification_condition(model, field_name, field_value, acronym):
        return model.objects.filter(**{'%s__iexact' % field_name: field_value,
                                  'acronym__name__iexact': acronym}).count() == 1

    def _get_mails(self, obj, acronym):
        if acronym:
            users_to_be_removed = []
            for subd in Subdivision.objects.all():
                users_to_be_removed.append(subd.allowed_users.split(','))
            try:
                usernames = HerbAcronym.objects.get(
                    name__iexact=acronym).allowed_users.split(',')
            except HerbAcronym.DoesNotExist:
                usernames = []
            # remove users belonging to subdivisions
            users_to_be_removed = sum(users_to_be_removed, [])
            usernames = list(set(usernames) - set(users_to_be_removed))
        else:
            usernames = []

        if obj.subdivision:
            subd = obj.subdivision
            while True:
                usernames += subd.allowed_users.split(',')
                if subd.parent:
                    subd = subd.parent
                else:
                    break

        target_users = list(set(settings.HERBS_NOTIFICATION_USERS).intersection(set(usernames)))
        final_users = []
        if target_users:
            umodel = get_user_model()
            for username in target_users:
                try:
                    user = umodel.objects.get(username=username)
                except umodel.DoesNotExist:
                    continue
                if user.has_perm('herbs.can_set_publish') and\
                                user.email in settings.HERBS_NOTIFICATION_MAILS:
                    final_users.append(user)
        return ','.join([user.email for user in final_users])



# -------------- Common per object permission setter ------------------------
class PermissionMixin:

    def queryset(self, request):
        if request.user.is_superuser:
            return self.model.objects.all()
        acronym = get_acronym_or_none(request)
        if request.user.has_perm('herbs.can_set_publish'):
            subdivision = get_subdivision_or_none(request)
            if acronym and subdivision:
                if hasattr(self.model, 'acronym'):
                    return self.model.objects.filter(acronym__name__iexact=acronym.name,
                                                     subdivision=subdivision)
            elif acronym:
                if hasattr(self.model, 'acronym'):
                    return self.model.objects.filter(acronym__name__iexact=acronym.name)
        return self.model.objects.filter(user=request.user)

    def _common_permission_manager(self, request, obj):
        if request.user.is_superuser: return True
        acronym = get_acronym_or_none(request)
        subdivision = get_subdivision_or_none(request)
        if obj is None: return True
        if obj.user is not None:
            if request.user == obj.user: return True
        if request.user.has_perm('herbs.can_set_publish'):
            if acronym and subdivision:
                if obj.subdivision.pk == subdivision.pk and obj.acronym.pk == acronym.pk:
                    return True
            elif acronym:
                if obj.acronym.pk == acronym.pk: return True
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


class HerbItemAdmin(PermissionMixin, AjaxSelectAdmin, NotificationMixin):
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
            acronym = get_acronym_or_none(request)
            if not obj.acronym:
                obj.acronym = acronym
            subd = get_subdivision_or_none(request)
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
        try:
            # try to make a notification, and
            # fail silently if something goes wrong!
            self.make_notification(request, obj)
        except:
             pass


    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(HerbItemAdmin, self).get_readonly_fields(request, obj)
        readonly_fields = set(readonly_fields)
        readonly_fields.update(['acronym', 'subdivision',
                                'public', 'itemcode', 'type_status'])
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
            if 'type_status' in readonly_fields:
                readonly_fields.remove('type_status')

            # check if the user has curator rights for acronym
            if get_subdivision_or_none(request) is None:
                if 'subdivision' in readonly_fields:
                    readonly_fields.remove('subdivision')

        elif request.user.has_perm('herbs.can_set_code'):
            if 'itemcode' in readonly_fields:
                readonly_fields.remove('itemcode')

        if request.user.is_superuser:
            readonly_fields.remove('acronym')
            readonly_fields.remove('subdivision')
        return list(readonly_fields)

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
            if not request.user.is_superuser and obj.status == 'A':
                if obj.updated:
                    if obj.updated < (timezone.now() - timedelta(days=settings.HERBS_APPROVED_SPECIES_FREEZE)).date():
                        readonly_fields = ['status', 'name', 'genus',
                                           'authorship', 'infra_rank',
                                           'infra_epithet', 'infra_authorship',
                                           'synonym']
        return readonly_fields


class HerbReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created', 'status', 'species_edit_link')
    list_filter = ('status', 'created')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(HerbReplyAdmin, self).get_readonly_fields(
            request, obj)
        readonly_fields = set(readonly_fields)

        if request.user.is_superuser:
            return list(readonly_fields)

        elif request.user.has_perm('herbs.can_set_publish'):
            acronym = get_acronym_or_none(request)
            if acronym and obj:
                if obj.herbitem:
                    if acronym == obj.herbitem.acronym:
                        readonly_fields = readonly_fields.union({'email', 'description', 'herbitem'})
                        return list(readonly_fields)
        else:
            if obj:
                if request.user == obj.herbitem.user:
                    readonly_fields = readonly_fields.union({'email', 'description', 'herbitem'})
                    return list(readonly_fields)
        readonly_fields = readonly_fields.union({'email', 'description', 'herbitem', 'status'})
        return list(readonly_fields)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def species_edit_link(self, obj):
        if obj.herbitem:
            url = reverse('admin:%s_%s_change' % ('herbs', 'herbitem'),
                          args=[obj.herbitem.id])
            resurl = '<a href="%s" title="Редактировать запись">Редактировать запись %s</a>'  % (url, obj.herbitem.id)
        else:
            resurl = '--'
        return resurl
    species_edit_link.allow_tags = True
    species_edit_link.short_description = _('Запись')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('created', 'username', 'status',
                    'tracked_field', 'field_value', 'edit_link')
    readonly_fields = ('username', 'emails', 'tracked_field', 'field_value')
    list_filter = ('status', 'username')
    search_fields = ('username', 'tracked_field', 'field_value')

    def edit_link(self, obj):
        resurl = '--'
        if obj:
            if obj.hitem:
                url = reverse('admin:%s_%s_change' % ('herbs', 'herbitem'),
                              args=[obj.hitem.id])
                resurl = '<a href="%s" title="Редактировать запись">Запись %s</a>'  % (url, obj.hitem.id)
        return resurl
    edit_link.allow_tags = True
    edit_link.short_description = _('Ссылка на объект')

    def has_delete_permission(self, request, obj=None):
         return request.user.is_superuser

admin.site.register(Family, FamilyAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(HerbItem, HerbItemAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(HerbAcronym)
admin.site.register(Country)
admin.site.register(Subdivision)
admin.site.register(SpeciesSynonym)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(HerbReply, HerbReplyAdmin)
