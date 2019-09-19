from ajax_select import register, LookupChannel
from .models import (Family, Genus, Species, Country, HerbItem,
                     DetHistory, Additionals, HerbAcronym)
from .conf import settings, HerbsAppConf
from django.db.models import Count
from django.utils.encoding import force_text
from django.utils.html import escape, mark_safe
from django.utils import timezone
from datetime import timedelta
from django.core.urlresolvers import reverse
import re


def get_acronym(request):
    query = HerbAcronym.objects.filter(
        allowed_users__icontains=request.user.username)
    if query.exists():
        return query[0]  # NOTE: only 1 acronym used.


NS = getattr(settings, '%s_AUTOSUGGEST_NUM_ADMIN' % HerbsAppConf.Meta.prefix.upper(), 20)
ACHAR = getattr(settings, '%s_AUTOSUGGEST_CHAR' % HerbsAppConf.Meta.prefix.upper(), 3)


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
        if obj:
            total = HerbItem.objects.filter(species=obj).count() + \
                    DetHistory.objects.filter(species=obj).exclude(
                    herbitem__isnull=True).count() + \
                    Additionals.objects.filter(species=obj).exclude(
                    herbitem__isnull=True).count()
        else:
            total = 0
        result = escape(force_text(obj)) +\
                 u'<a href="%s" target="_blank"> (Edit sp.) </a>' % (url,)
        result += '<br/>  Sp. occurence in the DB: %s' % total
        return result

    def format_match(self, obj):
        if obj:
            total = HerbItem.objects.filter(species=obj).count() + \
                    DetHistory.objects.filter(species=obj).exclude(
                    herbitem__isnull=True).count() + \
                    Additionals.objects.filter(species=obj).exclude(
                    herbitem__isnull=True).count()
        else:
            total = 0
        return escape(force_text(obj)) + '&nbsp; (%s)' % total


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
    def get_query(self, q, request):
        acronym  = get_acronym(request)
        if acronym:
            kwargs = {'%s__icontains' % self.fieldname: q.lstrip(),
                      'acronym': acronym}
        else:
            kwargs = {'%s__icontains' % self.fieldname: q.lstrip()}
        kwargs.update({'created__gte': (timezone.now() - timedelta(days=settings.HERBS_DAYS_TO_REMEMBER)).date()})
        return HerbItem.objects.filter(**kwargs).values(self.fieldname).annotate(num_items=Count(self.fieldname)).filter(num_items__gte=2).values_list(self.fieldname, flat=True)[:NS]

    def format_item_display(self, obj):
        return mark_safe('&'.join(map(escape, force_text(obj).split('&'))))

    get_result = format_item_display
    format_match = format_item_display



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
