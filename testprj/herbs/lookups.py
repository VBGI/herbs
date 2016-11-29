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
        return self.model.objects.filter(name__icontains=q).order_by('name').values('name').distinct()[:20]

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



class DistinctValueMixin(LookupChannel):

    def format_match(self, obj):
        return escape(force_text(obj))

    def get_result(self, obj):
        return escape(force_text(obj))

    def format_item_display(self, obj):
        return escape(force_text(obj))


@register('region')
class RegionLookup(DistinctValueMixin):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(region__icontains=q).order_by('updated',
                                                                     'region').values_list('region').distinct())[:20]

@register('district')
class DistrictLookup(LookupChannel):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(district__icontains=q).order_by('updated',
                                                                     'district').values_list('district').distinct())[:20]


@register('collectedby')
class CollectorsLookup(LookupChannel):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(collectedby__icontains=q).order_by('updated',
                                                                     'collectedby').values_list('collectedby').distinct())[:20]


@register('identifiedby')
class IdentifiersLookup(LookupChannel):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(identifiedby__icontains=q).order_by('updated',
                                                                     'identifiedby').values_list('identifiedby').distinct())[:20]

