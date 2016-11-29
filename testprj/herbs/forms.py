#coding: utf-8

import re

from ajax_select.fields import (AutoCompleteSelectField,
                               AutoCompleteField)
from django import forms
from django.utils.translation import gettext as _

from .models import (Family, Genus, HerbItem,
                     FamilyAuthorship, GenusAuthorship,
                     Author, Species,
                     SpeciesAuthorship)
from django.contrib.admin.widgets import AdminDateWidget

taxon_name_pat = re.compile(r'[a-z]+')
itemcode_pat = re.compile(r'\d+')

class TaxonCleanerMixin(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name']
        data = data.lower().strip()
        if self.Meta.model.objects.filter(name=data).exists():
            raise forms.ValidationError(_("имя должно быть уникально"))
        if len(data.split()) > 1:
            raise forms.ValidationError(_("название таксона не должно содержать пробелов"))
        if not taxon_name_pat.match(data):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))
        return data


class HerbItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # fill initial values for all data
        if 'initial' in kwargs.keys():
            try:
                initial = kwargs['initial']

                # ---------- Getting the current user -------------
                current_user = None
                request = kwargs.get('request', None)
                try:
                    current_user = request['user']
                except (AttributeError, TypeError):
                    current_user = None
                if current_user:
                    if current_user.is_superuser:
                        latest = HerbItem.objects.latest('created')
                    else:
                        latest = HerbItem.objects.filter(user=current_user).latest('created')
                else:
                    latest = HerbItem.objects.latest('created')
                # -------------------------------------------------
                initial['family'] = latest.family.pk
                initial['genus'] = latest.genus.pk
                initial['species'] = latest.species.pk if latest.species else None
                initial['itemcode'] = ''
                initial['country'] = latest.country
                initial['region'] = latest.region
                initial['district'] = latest.district
                initial['ecodescr'] = latest.ecodescr
                initial['collectedby'] = latest.collectedby
                initial['collected_s'] = latest.collected_s
                initial['collected_e'] = latest.collected_e
                initial['identifiedby'] = latest.identifiedby
                initial['identified_s'] = latest.identified_s
                initial['identified_e'] = latest.identified_e
                initial['detailed'] = latest.detailed
                initial['altitude'] = latest.altitude
                initial['note'] = latest.note
                initial['coordinates'] = latest.coordinates
                kwargs['initial'] = initial
            except HerbItem.DoesNotExist:
                pass
        super(HerbItemForm, self).__init__(*args, **kwargs)

    def clean_itemcode(self):
        data = self.cleaned_data['itemcode']
        data = data.strip()
        mainquery = HerbItem.objects.filter(itemcode=data)
        if self.instance:
            mainquery = mainquery.exclude(id=self.instance.id)
        if mainquery.exists():
            raise forms.ValidationError(_("запись с таким кодом уже существует"))
        if data:
            if not itemcode_pat.match(data):
                raise forms.ValidationError(_("уникальный код должен либо отсутствовать, либо быть числовым"))
        return data

    def clean(self):
        '''Change the genus of the species on-the-fly, if possible'''
        formdata = self.cleaned_data
        sp = formdata.get('species', None)
        g = formdata.get('genus', None)
        if sp:
            spo = Species.objects.filter(genus=g, name__exact=sp.name)
            if isinstance(sp, Species):
                if sp.genus != g:
                    if spo.exists():
                        formdata['species'] = spo[0]
                    else:
                        raise forms.ValidationError(_("Для данного рода такого вида не существует. Создайте при необходимости."))
        return formdata


    class Meta:
        model = HerbItem

    family = AutoCompleteSelectField('family', required=True, help_text=None, label=_("Семейство"))
    genus = AutoCompleteSelectField('genus', required=True, help_text=None, label=_("Род"))
    species = AutoCompleteSelectField('species', required=False, help_text=None, label=_("Вид"))
    ecodescr = forms.CharField(widget=forms.Textarea, required=False, label=_('Экоусловия'))
    detailed = forms.CharField(widget=forms.Textarea, required=False, label=_('Дополнительно'))
    note = forms.CharField(widget=forms.Textarea, required=False, label=_('Заметки'))
    country =  AutoCompleteField('country', required=False, help_text=None, label=_("Страна"))
    region =  AutoCompleteField('region', required=False, help_text=None, label=_("Регион"))
    district =  AutoCompleteField('district', required=False, help_text=None, label=_("Район"))
    collectedby =  AutoCompleteField('collectedby', required=False, help_text=None, label=_("Собрали"))
    identifiedby =  AutoCompleteField('identifiedby', required=False, help_text=None, label=_("Определили"))


class SearchForm(forms.Form):
    '''Common search form for ajax requests
    '''
    family = forms.CharField(required=False, label=_('Семейство'), max_length=30)
    genus = forms.CharField(required=False, label=_('Род'), max_length=30)
    species = forms.CharField(required=False, label=_('Вид'), max_length=30)
    itemcode = forms.CharField(required=False, label=_('Код1'), max_length=15)
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


class FamilyAuthorshipForm(forms.ModelForm):
    class Meta:
        model = FamilyAuthorship
    author = AutoCompleteSelectField('authorlookup',
                                     required=False,
                                     help_text=None,
                                     label=_("Автор"))

class SpeciesAuthorshipForm(forms.ModelForm):
    class Meta:
        model = SpeciesAuthorship
    author = AutoCompleteSelectField('authorlookup',
                                     required=False,
                                     help_text=None,
                                     label=_("Автор"))

class GenusAuthorshipForm(forms.ModelForm):
    class Meta:
        model = GenusAuthorship
    author = AutoCompleteSelectField('authorlookup',
                                     required=False,
                                     help_text=None,
                                     label=_("Автор"))

class AuthorForm(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name'].lower().strip()
        if self.Meta.model.objects.filter(name=data).exists():
             raise forms.ValidationError(_("имя уже существует"))
        if not data:
             raise forms.ValidationError(_("Имя не может быть пустым"))
        return data
    class Meta:
        model = Author

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species

    genus = AutoCompleteSelectField('genus',
                                    required=True,
                                    help_text=None,
                                    label=_("Род"))

    def clean(self):
        form_data = self.cleaned_data
        name = form_data.get('name', None)
        genus = form_data.get('genus', None)
        if name and genus:
            if Species.objects.filter(name__exact=name, genus=genus).exists():
                raise forms.ValidationError(_('Такая пара (род, вид) уже существует'))
        return form_data
