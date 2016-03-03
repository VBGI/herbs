import autocomplete_light.shortcuts as al
from .models. import HerbItem, Family, Genus


al.register(Family, search_fields=('name',),
    autocomplete_js_attributes={'placeholder': 'Select family name ..'})


def _get_allowed_genus(family_id):
    result = Genus.objects.none()
    try:
        herbs = HerbItem.objects.filter(family=family_id)
        result = herbs.objects.select_related('genus')
    except HerbItem.DoestNotExists:
        return result
    return result 
    




class AutocompleteGenus(autocomplete_light.AutocompleteModelBase):
    autocomplete_js_attributes={'placeholder': 'region name ..'}

    def choices_for_request(self):
        q = self.request.GET.get('q', '')
        family_id = self.request.GET.get('family_id', None)

        choices = self.choices.all()
        if q:
            choices = choices.filter(name__icontains=q)
        if family_id:
            choices = choices.filter(country_id=country_id)

        return self.order_choices(choices)[0:self.limit_choices]



autocomplete_light.register(Region, AutocompleteRegion)