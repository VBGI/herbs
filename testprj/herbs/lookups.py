from ajax_select import register, LookupChannel
from .models import Family, Genus, Species, SpeciesAuthorship, Author, HerbItem
from .countries import codes as ccodes
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import escape


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
    
@register('authorlookup')
class AuthorLookup(LookupChannel):
    model = Author
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:20]


@register('country')
class CountryLookup(LookupChannel):
    def get_query(self, q, request):
        res = [item for item in ccodes if q.lower() in item.decode('utf-8').lower()]
        return res[:20]

    def format_match(self, obj):
        return obj
    
    def get_result(self, obj):
        return obj
    
    def format_item_display(self, obj):
        return obj


@register('region')
class RegionLookup(LookupChannel):
    def get_query(self, q, request):
        return HerbItem.objects.filter(region__icontains=q).order_by('updated', 'region')[:20]
        
    def format_match(self, obj):
        return escape(force_text(obj.region))
    
    def get_result(self, obj):
        return escape(force_text(obj.region))
    
    def format_item_display(self, obj):
        return escape(force_text(obj.region))
    
    
@register('district')
class DistrictLookup(LookupChannel):
    
    def get_query(self, q, request):
        return HerbItem.objects.filter(district__icontains=q).order_by('updated', 'district')[:20]

    def format_match(self, obj):
        return escape(force_text(obj.district))
    
    def get_result(self, obj):
        return escape(force_text(obj.district))
    
    def format_item_display(self, obj):
        return escape(force_text(obj.district))
    
    
    
@register('collectors')
class CollectorsLookup(LookupChannel):
    
    def get_query(self, q, request):
        return HerbItem.objects.filter(collectors__icontains=q).order_by('updated', 'collectors')[:20]

    def format_match(self, obj):
        return escape(force_text(obj.collectors))
    
    def get_result(self, obj):
        return escape(force_text(obj.collectors))
    
    def format_item_display(self, obj):
        return escape(force_text(obj.collectors))
    

    
@register('identifiers')
class IdentifiersLookup(LookupChannel):
    
    def get_query(self, q, request):
        return HerbItem.objects.filter(identifiers__icontains=q).order_by('updated', 'identifiers')[:20]

    def format_match(self, obj):
        return escape(force_text(obj.identifiers))
    
    def get_result(self, obj):
        return escape(force_text(obj.identifiers))
    
    def format_item_display(self, obj):
        return escape(force_text(obj.identifiers))    
    
          