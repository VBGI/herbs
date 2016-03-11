
import autocomplete_light 

from .models import Family, Genus, HerbItem, OrderedAuthor, Author, Species

from django import forms


class TaxonCleanerMixin(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name']
        if self.Meta.model.objects.filter(name=data.lower()).exists():
            raise forms.ValidationError("The name should be unique")
        return data


class HerbItemForm(autocomplete_light.modelform_factory(HerbItem, fields=('family','genus','species', 'authorship'))):
    def __init__(self, *args, **kwargs):
        # fill initial values for all data
        if 'initial' in kwargs.keys():
            try:
                latest = HerbItem.objects.latest('created')
                initial['family'] = latest.family.pk
                initial['genus'] = latest.gemus.pk
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
            except HerbItem.DoesNotExist:
                pass 
        super(HerbItemForm, self).__init__(*args, **kwargs)
#     family = autocomplete_light.ModelChoiceField('AutocompleFamilyHerb')
#     genus =  autocomplete_light.ModelChoiceField('AutocompleGenusHerb')
#     species =  autocomplete_light.ModelChoiceField('AutocompleSpeciesHerb')
#     authorship = autocomplete_light.ModelChoiceField('AutocompleAuthorHerb')
    class Meta:
        model = HerbItem
        fields = '__all__'


class GenusForm(TaxonCleanerMixin):
    class Meta:
        model = Genus
        fields = '__all__'


class FamilyForm(TaxonCleanerMixin):
    class Meta:
        model = Family
        fields = '__all__'


class OrderedAuthorForm(forms.ModelForm):
    class Meta:
        model = OrderedAuthor
        fields = '__all__'


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = '__all__'


class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = '__all__'
