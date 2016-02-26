
import autocomplete 

from .models import Family, Genus, HerbItem

from django import forms



class TaxonCleanerMixin(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['recipients']
        if "fred@example.com" not in data:
            raise forms.ValidationError("You have forgotten about Fred!")

        # Always return the cleaned data, whether you have changed it or
        # not.
        return data


class HerbItemForm(autocomplete.ModelForm, TaxonCleanerMixin):
    def __init__(self, *args, **kwargs):
        
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


