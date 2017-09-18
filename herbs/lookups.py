from ajax_select import register, LookupChannel
from .models import Family, Genus, Species, Country, HerbItem
from .conf import settings, HerbsAppConf
from django.db.models import Count
from django.utils.encoding import force_text
from django.utils.html import escape
from django.core.urlresolvers import reverse
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
        return self.model.objects.filter(name__istartswith=q).order_by('name')[:NS]


@register('genus')
class GenusLookup(LookupChannel):
    model = Genus
    def get_query(self, q, request):
        return self.model.objects.filter(name__istartswith=q).order_by('name')[:NS]


@register('species')
class SpeciesLookup(LookupChannel):
    model = Species
    def get_query(self, q, request):
        mq = q.lstrip()
        res = self.model.objects.none()
        if len(mq) >= ACHAR:
            splitted = mq.split()
            if len(splitted) > 1:
                res = self.model.objects.filter(genus__name__istartswith=splitted[0],
                                             name__icontains=splitted[1]).exclude(status='D')
            else:
                res = self.model.objects.filter(genus__name__istartswith=splitted[0]).exclude(status='D')
        return res[:NS]
    
    def format_item_display(self, obj):
        url = reverse('admin:%s_%s_change' % (obj._meta.app_label,  obj._meta.module_name),  args=[obj.id])
        return escape(force_text(obj)) + u'<a href="%s"> (Edit sp.) </a>' % (url, )

@register('country')
class CountryLookup(LookupChannel):
    model = Country
    def get_query(self, q, request):
        if re.match('.*[a-zA-Z]+.*', q):
            res = self.model.objects.filter(name_en__icontains=q)
        else:
            res = self.model.objects.filter(name_ru__icontains=q)
        return res[:NS]


class DifferentValuesMixin(LookupChannel):
    '''Abstract class'''
    def get_query(self, q, request):
        kwargs = {'%s__icontains' % self.fieldname: q}
        return HerbItem.objects.filter(**kwargs).values(self.fieldname).annotate(Count(self.fieldname)).values_list(self.fieldname, flat=True)[:NS]

@register('region')
class RegionLookup(DifferentValuesMixin):
    fieldname = 'region'

@register('district')
class DistrictLookup(DifferentValuesMixin):
    fieldname = 'district'


@register('collectedby')
class CollectorsLookup(DifferentValuesMixin):
    fieldname = 'collectedby'

@register('identifiedby')
class IdentifiersLookup(DifferentValuesMixin):
    fieldname = 'identifiedby'
