#coding: utf-8

from .models import (Family, Genus, HerbItem,
                     FamilyAuthorship, GenusAuthorship,
                     Author, Species,
                     SpeciesAuthorship)
from django.utils.translation import gettext as _
from django import forms
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField

class TaxonCleanerMixin(forms.ModelForm):
    pass
#     def clean_name(self):
#         data = self.cleaned_data['name']
#         if self.Meta.model.objects.filter(name=data.lower()).exists():
#             raise forms.ValidationError("The name should be unique")
#         return data


class HerbItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # fill initial values for all data
        if 'initial' in kwargs.keys():
            try:
                initial = kwargs['initial']
                latest = HerbItem.objects.latest('created')
                initial['family'] = latest.family.pk
                initial['genus'] = latest.genus.pk
                initial['species'] = latest.species.pk
                initial['authorship'] = [k.pk for k in latest.authorship.all()]
                initial['gcode'] =  latest.gcode
                initial['itemcode'] =  latest.itemcode
                initial['country'] = latest.country
                initial['region'] = latest.region
                initial['distric'] = latest.district
                initial['ecodescr'] = latest.ecodescr
                initial['collectors'] = latest.collectors
                initial['collected_s'] = latest.collected_s
                initial['collected_e'] = latest.collected_e
                initial['identifiers'] = latest.identifiers
                initial['identified_s'] = latest.identified_s
                initial['identified_e'] = latest.identified_e
                kwargs['initial'] = initial 
            except HerbItem.DoesNotExist:
                pass 
        super(HerbItemForm, self).__init__(*args, **kwargs)

    class Meta:
        model = HerbItem
    
    family = AutoCompleteSelectField('family', required=False, help_text=None)
    genus = AutoCompleteSelectField('genus', required=False, help_text=None)
    species = AutoCompleteSelectField('species', required=False, help_text=None)
#     authorship = AutoCompleteSelectMultipleField('authorship', required=False, help_text=None)

class SearchForm(forms.Form):
    '''Common search form for ajax requests
    '''
    family = forms.CharField(required=False, label=_('Семейство'), max_length=30)
    genus = forms.CharField(required=False, label=_('Род'), max_length=30)
    species = forms.CharField(required=False, label=_('Вид'), max_length=30)
    itemcode = forms.CharField(required=False, label=_('Код1'), max_length=15)
    gcode = forms.CharField(required=False, label=_('Код2'), max_length=10)
    collectors = forms.CharField(required=False, label=_('Кто собрал'), max_length=100)
    country = forms.CharField(required=False, label=_('Страна'), max_length=30)
    region = forms.CharField(required=False, label=_('Регион'), max_length=30)


class GenusForm(TaxonCleanerMixin):
    class Meta:
        model = Genus


class FamilyForm(TaxonCleanerMixin):
    class Meta:
        model = Family


class FamilyAuthorshipForm(forms.ModelForm):
    class Meta:
        model = FamilyAuthorship
        

class SpeciesAuthorshipForm(forms.ModelForm):
    class Meta:
        model = SpeciesAuthorship        
        
class GenusAuthorshipForm(forms.ModelForm):
    class Meta:
        model = GenusAuthorship


class AuthorForm(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name'].lower()
        if self.Meta.model.objects.filter(name=data.lower()).exists():
             raise forms.ValidationError("The name already exists.")
        return data
    class Meta:
        model = Author
#         fields = '__all__'


class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
#         fields = '__all__'
