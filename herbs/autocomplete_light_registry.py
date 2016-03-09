import autocomplete_light.shortcuts as al
from .models. import HerbItem, Family, Genus, Species



class AutocompleFamilyHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Family name ..'}
    search_fields = ['family']
    model = HerbItem
    def choices_for_request(self):
        choices = self.choices.all()

class AutocompleGenusHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Genus name ..'}
    search_fields = ['genus']
    model = HerbItem
    def choices_for_request(self):
        choices = self.choices.all()

class AutocompleSpeciesHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Species name ..'}
    search_fields = ['species']
    model = HerbItem
    def choices_for_request(self):
        choices = self.choices.all()

class AutocompleAuthorHerb(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'Authorship ..'}
    search_fields = ['authorship']
    model = HerbItem
    def choices_for_request(self):
        choices = self.choices.all()

# class AutocompleteAuthorship(autocomplete_light.AutocompleteModelBase):
#     autocomplete_js_attributes={'placeholder': 'Authorship ..'}
#     search_fields = ['authorship']
#     model = HerbItem
#     def choices_for_request(self):
#         choices = self.choices.all()


autocomplete_light.register(HerbItem, AutocompleFamilyHerb)
autocomplete_light.register(HerbItem, AutocompleGenusHerb)
autocomplete_light.register(HerbItem, AutocompleSpeciesHerb)
autocomplete_light.register(HerbItem, AutocompleAuthorHerb)