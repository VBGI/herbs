import autocomplete_light
from .models import HerbItem, Family, Genus, Species, OrderedAuthor



class AutocompleFamilyHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Family name ..'}
    search_fields = ['name']
    model = Family
#     choices = Family.objects.all()
# 
#     def choices_for_request(self):
#         q = self.request.GET.get('q', '')
#         self.choices = Family.objects.filter(name__icontains=q)
#         return super(AutocompleFamilyHerb, self).choices_for_request()



class AutocompleGenusHerb(autocomplete_light.AutocompleteModelBase):
    choices = Genus.objects.all()
    autocomplete_js_attributes={'placeholder': 'Genus name ..'}
    search_fields = ['name']
    model = Genus


class AutocompleSpeciesHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Species name ..'}
    search_fields = ['name']
    model = Species
    
class AutocompleAuthorHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Authorship ..'}
    search_fields = ['name']
    model = OrderedAuthor
    

# class AutocompleteAuthorship(autocomplete_light.AutocompleteModelBase):
#     autocomplete_js_attributes={'placeholder': 'Authorship ..'}
#     search_fields = ['authorship']
#     model = HerbItem
#     def choices_for_request(self):
#         choices = self.choices.all()


autocomplete_light.register(AutocompleFamilyHerb)
autocomplete_light.register(AutocompleGenusHerb)
autocomplete_light.register(AutocompleSpeciesHerb)
autocomplete_light.register(AutocompleAuthorHerb)
