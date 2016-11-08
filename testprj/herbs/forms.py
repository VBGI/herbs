#coding: utf-8

import re

from ajax_select.fields import (AutoCompleteSelectField,
                                AutoCompleteSelectMultipleField,
                               AutoCompleteField)
from django import forms
from django.utils.translation import gettext as _

from .models import (Family, Genus, HerbItem,
                     FamilyAuthorship, GenusAuthorship,
                     Author, Species,
                     SpeciesAuthorship)
from django.contrib.admin.widgets import AdminDateWidget

taxon_name_pat = re.compile(r'[a-z]+')


class TaxonCleanerMixin(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name']
        if self.Meta.model.objects.filter(name=data.lower()).exists():
            raise forms.ValidationError(_("имя должно быть уникально"))
        if len(data.lower().split()) > 1:
            raise forms.ValidationError(_("название таксона не должно содержать пробелов"))
        if not taxon_name_pat.match(data.lower().strip()):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))
        return data

# class HerbItemShowForm(forms.ModelForm):
#     class Meta:
#         model = HerbItem

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
                initial['species'] = latest.species.pk
                initial['gcode'] =  latest.gcode
                initial['itemcode'] =  latest.itemcode
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
                initial['note'] = latest.note
                initial['coordinates'] = latest.coordinates
                kwargs['initial'] = initial
            except HerbItem.DoesNotExist:
                pass
        super(HerbItemForm, self).__init__(*args, **kwargs)


    class Meta:
        model = HerbItem

    family = AutoCompleteSelectField('family', required=False, help_text=None, label=_("Семейство"))
    genus = AutoCompleteSelectField('genus', required=False, help_text=None, label=_("Род"))
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
    gcode = forms.CharField(required=False, label=_('Код2'), max_length=10)
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
    family = AutoCompleteSelectField('family', required=False, help_text=None, label=_("Семейство"))

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
                                    required=False,
                                    help_text=None,
                                    label=_("Род"))
