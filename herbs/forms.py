
import autocomplete 

from .models import Family, Genus, HerbItem

from django import forms





class HerbItemForm(autocomplete.ModelForm):
    def __init__(self, *args, **kwargs):
        
    class Meta:
        model = HerbItem
        fields = ('__all__')
        


class GenusForm(forms.ModelForm):
    name = forms.ModelChoiceField(
        queryset=Genus.objects.all(),
        widget=autocomplete.ModelSelect2(url='family-autocomplete')
    )
    class Meta:
        model = Genus
        fields = ('__all__')


# class HerbItemForm(forms.ModelForm):
#     family = forms.ModelChoiceField(
#         queryset=Genus.objects.all(),
#         widget=autocomplete.ModelSelect2(url='family-autocomplete')
#     )
#     class Meta:
#         model = HerbItem
#         fields = ('__all__')