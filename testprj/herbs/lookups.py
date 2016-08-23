from ajax_select import register, LookupChannel
from .models import Family, Genus, Species

@register('family')
class FamilyLookup(LookupChannel):
    model = Family
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('name')[:20]
    
@register('genus')
class GenusLookup(LookupChannel):
    model = Genus
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('name')[:20]

@register('species')
class SpeciesLookup(LookupChannel):
    model = Species
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('name')[:20]
    
        