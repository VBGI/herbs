from ajax_select import register, LookupChannel
from .models import Family, Genus, Species, Country, HerbItem
from .conf import settings, HerbsAppConf
import re


NS = getattr(settings,
             '%s_AUTOSUGGEST_NUM_ADMIN' % HerbsAppConf.Meta.prefix.upper(),
             20)
ACHAR = getattr(settings,
             '%s_AUTOSUGGEST_CHAR' % HerbsAppConf.Meta.prefix.upper(),
             3)


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
        mq = q.lstrip()
        res = self.model.objects.none()
        if len(mq) >= ACHAR:
            splitted = mq.split()
            if len(splitted) > 1:
                res = self.model.objects.filter(genus__name__icontains=splitted[0],
                                             name__icontains=splitted[1])
            else:
                res = self.model.objects.filter(genus__name__icontains=splitted[0])
        return res[:NS]


@register('country')
class CountryLookup(LookupChannel):
    model = Country
    def get_query(self, q, request):
        if re.match('.*[a-zA-Z]+.*', q):
            res = self.model.objects.filter(name_en__icontains=q)
        else:
            res = self.model.objects.filter(name_ru__icontains=q)
        return res[:NS]


#class DifferentValueMixin(LookupChannel):
    #'''Abstract class'''
    #def get_query(self, q, request):
        #objs = HerbItem.objects.raw('''SELECT * FROM herbs_herbitem WHERE %s LIKE "%%%s%%" GROUP BY %s''',
                                    #[self.fieldname, q, self.fieldname])
        #return map(lambda x: getattr(x, self.fieldname), objs[:NS])


@register('region')
class RegionLookup(LookupChannel):
    objs = HerbItem.objects.raw('''SELECT * FROM herbs_herbitem WHERE region LIKE "%%%s%%" GROUP BY region''', [q])
    return map(lambda x: getattr(x, self.region), objs[:NS])

@register('district')
class DistrictLookup(LookupChannel):
    objs = HerbItem.objects.raw('''SELECT * FROM herbs_herbitem WHERE district LIKE "%%%s%%" GROUP BY district''', [q])
    return map(lambda x: getattr(x, self.district), objs[:NS])

@register('collectedby')
class CollectorsLookup(DifferentValueMixin):
    objs = HerbItem.objects.raw('''SELECT * FROM herbs_herbitem WHERE collectedby LIKE "%%%s%%" GROUP BY collectedby''', [q])
    return map(lambda x: getattr(x, self.collectedby), objs[:NS])

@register('identifiedby')
class IdentifiersLookup(DifferentValueMixin):
    objs = HerbItem.objects.raw('''SELECT * FROM herbs_herbitem WHERE identifiedby LIKE "%%%s%%" GROUP BY identifiedby''', [q])
    return map(lambda x: getattr(x, self.identifiedby), objs[:NS])
