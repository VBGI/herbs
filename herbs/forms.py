#coding: utf-8

import re
from ajax_select.fields import (AutoCompleteSelectField,
                                AutoCompleteField)
from django import forms
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta, date
from .models import (Family, Genus, HerbItem, Species,
                     DetHistory, HerbAcronym, Additionals)
from django.forms.util import ErrorList
from .conf import settings, HerbsAppConf

CS = getattr(settings,
             '%s_CH_SIZE' % HerbsAppConf.Meta.prefix.upper(), 80)


taxon_name_pat = re.compile(r'[a-z]+')
itemcode_pat = re.compile(r'^\d+$')


class TaxonCleanerMixin(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name']
        data = data.lower().strip()
        mainquery = self.Meta.model.objects.filter(name=data)
        if self.instance:
            mainquery = mainquery.exclude(id=self.instance.id)
        if mainquery.exists():
            raise forms.ValidationError(_("имя должно быть уникально"))
        if len(data.split()) > 1:
            raise forms.ValidationError(_("название таксона не должно содержать пробелов"))
        if not taxon_name_pat.match(data):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))
        return data


class HerbItemFormSimple(forms.ModelForm):
    class Meta:
        model = HerbItem


class HerbItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(HerbItemForm, self).__init__(*args, **kwargs)

    def clean_itemcode(self):
        data = self.cleaned_data['itemcode']
        data = data.strip()
        if data:
            mainquery = HerbItem.objects.filter(itemcode=data)
            if self.instance:
                mainquery = mainquery.exclude(id=self.instance.id)
            if self.request:
                query = HerbAcronym.objects.filter(allowed_users__icontains=self.request.user.username)
            else:
                query = None
            if query:
                if mainquery.filter(acronym=query[0]).exists():
                    raise forms.ValidationError(_("запись с таким кодом уже существует"))
            if not itemcode_pat.match(data):
                raise forms.ValidationError(_("уникальный код должен либо отсутствовать, либо быть числовым"))
        return data


    def _verify_dates(self, data):
        if data:
            if data > (timezone.now() + timedelta(days=2)).date():
                raise forms.ValidationError(_("Дата не может быть больше текущей календарной даты"))

            if data < date(year=1700, month=1, day=1):
                raise forms.ValidationError(_("Не ошибка ли это? Слишком древний образец."))

    def clean_identified_s(self):
        data = self.cleaned_data['identified_s']
        self._verify_dates(data)
        return data

    def clean_identified_e(self):
        data = self.cleaned_data['identified_e']
        self._verify_dates(data)
        return data

    def clean_collected_s(self):
        data = self.cleaned_data['collected_s']
        self._verify_dates(data)
        return data

    def clean_collected_e(self):
        data = self.cleaned_data['collected_e']
        self._verify_dates(data)
        return data


    def clean(self):
        '''Checking consistency for dates '''
        formdata = self.cleaned_data
        d1 = formdata.get('identified_s')
        d2 = formdata.get('identified_e')
        if d1 and d2:
            if d2 < d1:
                self._errors.setdefault('identified_e', ErrorList())
                self._errors['identified_e'].append(_('дата окончания определения должна быть не раньше даты начала'))

        dc1 = formdata.get('collected_s')
        dc2 = formdata.get('collected_e')
        if d1 and d2:
            if d2 < d1:
                self._errors.setdefault('collected_e', ErrorList())
                self._errors['collected_e'].append(_('дата окончания определения должна быть не раньше даты начала'))
        if dc1 and d1:
            if d1 < dc1:
                self._errors.setdefault('identified_s', ErrorList())
                self._errors['identified_s'].append(_('дата определения не может быть раньше даты сбора'))
        if dc1 and dc2:
            if dc2 < dc1:
                self._errors.setdefault('collected_e', ErrorList())
                self._errors['collected_e'].append(_('дата окончания сбора должна быть не раньше даты начала'))
        ispub = formdata.get('public')
        icode = formdata.get('itemcode')
        sp = formdata.get('species')
        if icode:
            icode = icode.strip()
        if ispub:
            if not icode:
                forms.ValidationError(_('публиковать можно только при непустом уникальном коде образца'))
            if sp:
                if sp.status not in ['A', 'P']:
                    raise forms.ValidationError(_('вид не одобрен куратором; опубликовать можно только одобренные виды'))
        return formdata

    class Meta:
        model = HerbItem

    species = AutoCompleteSelectField('species', required=True, help_text=None, label=_("Вид"))
    detailed = forms.CharField(widget=forms.Textarea, required=False, label=_('Место сбора'))
    detailed.help_text = _("локализация, экоусловия")
    note = forms.CharField(widget=forms.Textarea, required=False, label=_('Заметки'))
    country = AutoCompleteSelectField('country', required=False, help_text=None, label=_("Страна"))
    region = AutoCompleteField('region', required=False, help_text=None, label=_("Регион"), attrs={'size': CS})
    district = AutoCompleteField('district', required=False, help_text=None, label=_("Район"), attrs={'size': CS})
    collectedby = AutoCompleteField('collectedby', required=False, help_text=None, label=_("Собрали"), attrs={'size': CS})
    identifiedby = AutoCompleteField('identifiedby', required=False, help_text=None, label=_("Определили"), attrs={'size': CS})


class DetHistoryForm(forms.ModelForm):
    class Meta:
        model = DetHistory
    species = AutoCompleteSelectField('species', required=False, label=_("Вид"))
    identifiedby = AutoCompleteField('identifiedby', required=False,
                                     label=_("Переопределелил(и)"),
                                     attrs={'size': CS})


class AdditionalsForm(forms.ModelForm):
    class Meta:
        model = Additionals
    species = AutoCompleteSelectField('species', required=False, label=_("Вид"))
    identifiedby = AutoCompleteField('identifiedby', required=False,
                                     label=_("Определелил(и)"),
                                     attrs={'size': CS})


class RectSelectorForm(forms.Form):
    latl = forms.FloatField(required=False)
    latu = forms.FloatField(required=False)
    lonl = forms.FloatField(required=False)
    lonu = forms.FloatField(required=False)


class SearchForm(forms.Form):
    '''Common search form for ajax requests'''

    family = forms.CharField(required=False, max_length=30)
    genus = forms.CharField(required=False, max_length=30)
    species_epithet = forms.CharField(required=False, max_length=50)
    itemcode = forms.CharField(required=False, max_length=15)
    collectedby = forms.CharField(required=False, max_length=100)
    identifiedby = forms.CharField(required=False, max_length=100)
    country = forms.CharField(required=False, max_length=100)
    place = forms.CharField(required=False, max_length=200)
    colstart = forms.DateField(required=False)
    colend = forms.DateField(required=False)

    # sorting parameters
    sortfield = forms.CharField(required=False, max_length=100)
    sortorder = forms.BooleanField(required=False)

    # extra parameters for validation
    acronym = forms.CharField(required=False, max_length=10)
    subdivision = forms.CharField(required=False, max_length=100)


class GenusForm(TaxonCleanerMixin):
    class Meta:
        model = Genus
    family = AutoCompleteSelectField('family', required=True, help_text=None, label=_("Семейство"))

    def clean_gcode(self):
        data = self.cleaned_data['gcode']
        data = data.strip()
        if data:
            if not itemcode_pat.match(data):
                return forms.ValidationError('уникальный код рода должен быть цифровой')
        return data


class FamilyForm(TaxonCleanerMixin):
    class Meta:
        model = Family


class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species

    genus = AutoCompleteSelectField('genus', required=True, help_text=None,
                                    label=_("Род"))
    synonym = AutoCompleteSelectField('species', label=_("Синоним вида"),
                                      required=False)

    name = forms.CharField(max_length=70, label=_('Название'), required=True,
                           help_text=_('видовой эпитет'))

    def clean(self):
        form_data = self.cleaned_data
        name = form_data.get('name', '')
        genus = form_data.get('genus', None)
        authorship = form_data.get('authorship', '')
        status = form_data.get('status', 'N')
        infra_rank = form_data.get('infra_rank', '')
        infra_epithet = form_data.get('infra_epithet', '')

        if infra_epithet and not infra_rank:
            raise forms.ValidationError(_("нужно определить подвидовой ранг или оставить поле подвидовой эпитет пустым"))

        if infra_epithet:
            infra_epithet = infra_epithet.strip().lower()

        if name:
            name = name.strip().lower()
        if authorship:
            authorship = authorship.strip().lower()
        if name and genus and self.instance and status != 'D':
            if Species.objects.filter(name=name,
                                      genus=genus,
                                      authorship=authorship,
                                      infra_rank=infra_rank,
                                      infra_epithet=infra_epithet).exclude(id=self.instance.id).exclude(status='D').exists():
                raise forms.ValidationError(_('Такой набор (род, вид, автор, подвидовой ранг и эптитет) уже существует'))
        if not taxon_name_pat.match(name):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))

        if infra_epithet:
            if not taxon_name_pat.match(infra_epithet):
                raise forms.ValidationError(
                    _("название подвидового эпитета должно состоять только из латинских букв"))

        form_data['name'] = name
        form_data['infra_epithet'] = infra_epithet
        return form_data
