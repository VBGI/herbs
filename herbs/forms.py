#coding: utf-8

import re

from ajax_select.fields import (AutoCompleteSelectField,
                               AutoCompleteField)
from django import forms
from django.utils.translation import gettext as _

from .models import Family, Genus, HerbItem, Species, DetHistory
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.util import ErrorList

from .conf import settings, HerbsAppConf

CS = getattr(settings,
             '%s_CH_SIZE' % HerbsAppConf.Meta.prefix.upper(), 80)



taxon_name_pat = re.compile(r'[a-z]+')
itemcode_pat = re.compile(r'\d+')

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


class HerbItemForm(forms.ModelForm):

    def clean_itemcode(self):
        data = self.cleaned_data['itemcode']
        data = data.strip()
        if data:
            mainquery = HerbItem.objects.filter(itemcode=data)
            if self.instance:
                mainquery = mainquery.exclude(id=self.instance.id)
            if mainquery.exists():
                raise forms.ValidationError(_("запись с таким кодом уже существует"))
            if not itemcode_pat.match(data):
                raise forms.ValidationError(_("уникальный код должен либо отсутствовать, либо быть числовым"))
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
                self._errors.setdefault('public', ErrorList())
                self._errors['public'].append(_('публиковать можно только при непустом уникальном коде образца'))
            if sp:
                if sp.status not in ['A', 'P']:
                    self._errors.setdefault('species', ErrorList())
                    self._errors['species'].append(_('вид не одобрен куратором; опубликовать можно только одобренные виды'))
        return formdata


    class Meta:
        model = HerbItem

    species = AutoCompleteSelectField('species', required=True, help_text=None, label=_("Вид"))
    detailed = forms.CharField(widget=forms.Textarea, required=False, label=_('Место сбора'))
    detailed.help_text = _("локализация, экоусловия")
    note = forms.CharField(widget=forms.Textarea, required=False, label=_('Заметки'))
    country =  AutoCompleteSelectField('country', required=False, help_text=None, label=_("Страна"))
    region =  AutoCompleteField('region', required=False, help_text=None, label=_("Регион"), attrs={'size': CS})
    district =  AutoCompleteField('district', required=False, help_text=None, label=_("Район"), attrs={'size': CS})
    collectedby =  AutoCompleteField('collectedby', required=False, help_text=None, label=_("Собрали"), attrs={'size': CS})
    identifiedby =  AutoCompleteField('identifiedby', required=False, help_text=None, label=_("Определили"), attrs={'size': CS})


class DetHistoryForm(forms.ModelForm):
    class Meta:
        model = DetHistory
    species = AutoCompleteSelectField('species', required=False, label=_("Вид"))
    identifiedby = AutoCompleteField('identifiedby', required=False,
                                     label=_("Определелил(и)"),
                                     attrs={'size': CS})


class SearchForm(forms.Form):
    '''Common search form for ajax requests
    '''
    family = forms.CharField(required=False, label=_('Семейство'), max_length=30)
    genus = forms.CharField(required=False, label=_('Род'), max_length=30)
    species = forms.CharField(required=False, label=_('Вид'), max_length=30)
    itemcode = forms.CharField(required=False, label=_('Код1'), max_length=15)
    gcode = forms.CharField(required=False, label=_('Da la torre Ind:'), max_length=5)
    collectedby = forms.CharField(required=False, label=_('Кто собрал'), max_length=100)
    identifiedby = forms.CharField(required=False, label=_('Кто собрал'), max_length=100)
    country =  AutoCompleteField('country', required=False, help_text=None, label=_("Страна"))
    country.widget.attrs['id'] = 'country-input'
    place = forms.CharField(required=False, label=_('Место'), max_length=30)
    colstart = forms.DateField(required=False, label=_('Начало сбора'), widget = AdminDateWidget)
    colstart.widget.attrs['id'] = 'colstart-input'
    colend = forms.DateField(required=False, label=_('Конец сбора'), widget = AdminDateWidget)
    colend.widget.attrs['id'] = 'colend-input'

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

    def clean(self):
        form_data = self.cleaned_data
        name = form_data.get('name', None)
        genus = form_data.get('genus', None)
        name = name.strip().lower()
        if name and genus and self.instance:
            if Species.objects.filter(name__exact=name, genus=genus).exclude(id=self.instance.id).exists():
                raise forms.ValidationError(_('Такая пара (род, вид) уже существует'))
#        if len(name.split()) > 1:
#            raise forms.ValidationError(_("название таксона не должно содержать пробелов"))
        if not taxon_name_pat.match(name):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))
        form_data['name'] = name
        return form_data
