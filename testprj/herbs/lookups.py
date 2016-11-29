from ajax_select import register, LookupChannel
from .models import Family, Genus, Species, SpeciesAuthorship, Author, HerbItem
from .countries import codes as ccodes
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import escape
from .conf import settings

NS = settings.AUTOSUGGEST_NUM_ADMIN

@register('family')
class FamilyLookup(LookupChannel):
    model = Family
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('name')[:NS]

@register('genus')
class GenusLookup(LookupChannel):
    model = Genus
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('name')[:NS]

@register('species')
class SpeciesLookup(LookupChannel):
    model = Species
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('name').values_list('name').distinct()[:NS]

@register('authorlookup')
class AuthorLookup(LookupChannel):
    model = Author
    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:NS]


@register('country')
class CountryLookup(LookupChannel):
    def get_query(self, q, request):
        res = [item for item in ccodes if q.lower() in item.decode('utf-8').lower()]
        return res[:NS]

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
                                                                     'region').values_list('region').distinct())[:NS]

@register('district')
class DistrictLookup(LookupChannel):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(district__icontains=q).order_by('updated',
                                                                     'district').values_list('district').distinct())[:NS]


@register('collectedby')
class CollectorsLookup(LookupChannel):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(collectedby__icontains=q).order_by('updated',
                                                                     'collectedby').values_list('collectedby').distinct())[:NS]


@register('identifiedby')
class IdentifiersLookup(LookupChannel):
    def get_query(self, q, request):
        return map(lambda x: x[0], HerbItem.objects.filter(identifiedby__icontains=q).order_by('updated',
                                                                     'identifiedby').values_list('identifiedby').distinct())[:NS]

