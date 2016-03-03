
import autocomplete 

from .models import Family, Genus, HerbItem

from django import forms



class TaxonCleanerMixin(forms.ModelForm):

    def clean_name(self):
        data = self.cleaned_data['name']
        if self.Meta.model.objects.filter(name=data.lower()).exists():
            raise forms.ValidationError("The name should be unique")
        return data





class HerbItemForm(autocomplete.ModelForm):
    def __init__(self, *args, **kwargs):
        # fill initial values for all data
        if 'initial' in kwargs.keys():
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
        super(ArtefactForm, self).__init__(*args, **kwargs)

    class Meta:
        model = HerbItem
        fields = ('__all__')


class GenusForm(forms.ModelForm, TaxonCleanerMixin):
    class Meta:
        model = Genus
        fields = ('__all__')


class FamilyForm(forms.ModelForm, TaxonCleanerMixin):
    class Meta:
        model = Family
        fields = ('__all__')


