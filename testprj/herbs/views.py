# -*- coding: utf-8 -*-
import operator
import datetime
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.forms.models import model_to_dict

from .models import Family, Genus, HerbItem, Species
from .countries import codes as contry_codes
from .forms import SearchForm
from .conf import settings
from django.utils.text import capfirst


from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
import json

# from django.db.models.base import ModelState

countries = [key.decode('utf-8') for key in contry_codes]

@csrf_exempt
def get_item_data(request):
    '''Get herbitem as a json object '''
    context = {'error': ''}
    objid = request.GET.get('id', '')
    if objid:
        try:
            hobj = HerbItem.objects.get(id=objid)
            tojson = model_to_dict(hobj)
            context.update({'data': tojson})
        except HerbItem.DoesNotExists:
            context = {'error': u'Объект не найден'}
    return  HttpResponse(json.dumps(context), content_type="application/json; charset=utf-8")


def parse_date(d):
    if not d: return None
    try:
       res = datetime.datetime.strptime(d, '%m/%d/%Y')
    except ValueError:
        res = None
    return res


csrf_exempt
def show_herbs(request):
    '''
    Answer on queries for herbitems
    '''
    if request.method == 'POST':
        return HttpResponse('Only GET-methods are acceptable')

    context = {'error': '', 'has_previous': None, 'has_next': None,
               'pagenumber': 1, 'pagecount': 0}

    if request.is_ajax():
        dataform = SearchForm(request.GET)
        if dataform.is_valid():
            data = {key: dataform.cleaned_data[key] for key in dataform.fields}
            bigquery = [Q(public=True)]
            bigquery += [Q(family__name__iexact=data['family'])] if data['family'] else []
            bigquery += [Q(genus__name__iexact=data['genus'])] if data['genus'] else []
            bigquery += [Q(species__name__iexact=data['species'])] if data['species'] else []
            bigquery += [Q(itemcode__icontains=data['itemcode'])] if data['itemcode'] else []
            bigquery += [Q(gcode__icontains=data['gcode'])] if data['gcode'] else []
            bigquery += [Q(collectedby__icontains=data['collectedby'])] if data['collectedby'] else []
            bigquery += [Q(identifiedby__icontains=data['identifiedby'])] if data['identifiedby'] else []
            bigquery += [Q(country__icontains=data['country'])] if data['country'] else []
            # place handle
            bigquery += [Q(region__icontains=data['place'])|\
                         Q(detailed__icontains=data['place'])|\
                         Q(district__icontains=data['place'])] if data['place'] else []

            # dates
            stdate = parse_date(request.GET.get('colstart', ''))
            endate = parse_date(request.GET.get('colend', ''))

            bigquery += [Q(collected_s__gt=stdate)] if stdate else []
            bigquery += [Q(collected_e__lt=endate)] if endate else []

            object_filtered = HerbItem.objects.filter(reduce(operator.and_, bigquery))

            if not object_filtered.exists():
                context.update({'herbobjs' : [],
                                'total': 0,
                                'error': 'Ни одного элемента не удолетворяет условиям запроса'})
                return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")

            # ------- Sorting items --------------
            # sorting isn't implemented yet
            # ---------  pagination-----------------
            pagcount = request.GET.get('pagcount', '')
            page = request.GET.get('page', '1')
            pagcount = int(pagcount) if pagcount.isdigit() else settings.HERBS_PAGINATION_COUNT
            page = int(page) if page.isdigit() else 1
            paginator = Paginator(object_filtered, pagcount)
            try:
                obj_to_show = paginator.page(page)
            except:
                obj_to_show = paginator.page(1)
            # ----------- Conversion to list of dicts with string needed ----------
            # make json encoding smarty
            data_tojson = []
            for item in obj_to_show.object_list:
                data_tojson.append(
                    {'family': item.family.get_full_name() if hasattr(item.family, 'get_full_name') else '',
                     'genus': item.genus.get_full_name() if hasattr(item.genus, 'get_full_name')  else '',
                     'species': item.species.get_full_name() if hasattr(item.species, 'get_full_name') else '',
                     'itemcode': item.itemcode,
                     'gcode': item.gcode,
                     'id': item.pk,
                    # Extra data to show herbitem details
                     'ecodescr': item.ecodescr,
                     'height': item.height,
                     'district': item.district,
                     'country': item.country,
                     'region': item.region,
                     'collectedby': item.collectedby,
                     'collected_s': item.collected_s,
                     'identifiedby': item.identifiedby,
                     'note': item.note,
                     'created':  str(item.created),
                     'updated': str(item.updated)
                     })

            # ---------------------------------------------------------------------
            context.update({'herbobjs' : data_tojson,
                            'has_previous': obj_to_show.has_previous(),
                            'has_next': obj_to_show.has_next(),
                            'pagenumber': page,
                            'pagecount': paginator.num_pages,
                            'total': object_filtered.count(),
                            })

            return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type="application/json;charset=utf-8")
        else:
            context.update({'herbobjs': [],
                            'total': 0,
                            'error': 'Ошибка в форме поиска'})
            return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type="application/json;charset=utf-8")
    else:
        return HttpResponse('Only ajax-requests are acceptable')


@never_cache
def advice_select(request):
    if not request.is_ajax():
        return HttpResponse('Only ajax-requests are acceptable')
    if request.method == 'POST':
        return HttpResponse('Only GET-methods are acceptable')

    dataform = SearchForm(request.GET)
    context = {'error': ''}
    if dataform.is_valid():
        cfield = request.GET.get('model', 'species')
        if cfield not in dataform.fields:
            cfield = 'species'
        query = request.GET.get('q', '')
        if cfield == 'itemcode':
            if query:
                objects = HerbItem.objects.filter(itemcode__contains=query)[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            else:
                objects = HerbItem.objects.all()[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            data = [{'id': item.pk, 'text': item.itemcode} for item in objects]
        elif cfield == 'family':
            if query:
                objects = Family.objects.filter(name__icontains=query)[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            else:
                objects = Family.objects.all()[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            data = [{'id': item.pk, 'text': item.name} for item in objects]
        elif cfield == 'gcode':
            objects = HerbItem.objects.filter(gcode__contains=query)
            tostore = map(lambda x: x[0], objects.order_by('gcode').values_list('gcode').distinct())[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            if tostore:
                data = [{'id': ind + 2, 'text': item} for ind, item in enumerate(tostore)]
            else:
                data = []
        elif cfield == 'genus':
            # TODO: DB structure: changes needed,
            if dataform.cleaned_data['family']:
                if query:
                    objects = Genus.objects.filter(family__name__iexact=dataform.cleaned_data['family'],
                                                   name__icontains=query)
                else:
                    objects = Genus.objects.filter(family__name__iexact=dataform.cleaned_data['family'])
            else:
                if query:
                    objects = Genus.objects.filter(name__icontains=query)
                else:
                    objects = Genus.objects.all()
            data = [{'id': item.pk, 'text': item.name} for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
        elif cfield == 'species':
            if dataform.cleaned_data['family'] and dataform.cleaned_data['genus']:
                if query:
                    objects = Species.objects.filter(genus__family__name__iexact=dataform.cleaned_data['family'],
                                                     genus__name__iexact=dataform.cleaned_data['genus'],
                                                     name__icontains=query)
                else:
                    objects = Species.objects.filter(genus__family__name__iexact=dataform.cleaned_data['family'],
                                                     genus__name__iexact=dataform.cleaned_data['genus'])
            elif dataform.cleaned_data['family'] and not dataform.cleaned_data['genus']:
                if query:
                    objects = Species.objects.filter(genus__family__name__iexact=dataform.cleaned_data['family'],
                                                     name__icontains=query)
                else:
                    objects = Species.objects.filter(genus__family__name__iexact=dataform.cleaned_data['family'])
            elif not dataform.cleaned_data['family'] and dataform.cleaned_data['genus']:
                if query:
                    objects = Species.objects.filter(genus__name__iexact=dataform.cleaned_data['genus'],
                                                     name__icontains=query)
                else:
                    objects = Species.objects.filter(genus__name__iexact=dataform.cleaned_data['genus'])
            elif not dataform.cleaned_data['family'] and not dataform.cleaned_data['genus']:
                if query:
                    objects = Species.objects.filter(name__icontains=query)
                else:
                    objects = Species.objects.all()
            data = [{'id': item.pk, 'text': item.name}
                    for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
        elif cfield == 'country':
            data = [{'id': ind + 2, 'text': val} for ind, val in enumerate(filter(lambda x: query in x, countries))]
    else:
        # invalid form (That isn't possible,  I hope! )
        context.update({'error': 'Странный запрос'})
        data = []
    if data:
        for item in data: item['text'] = capfirst(item['text'])
    context.update({'items': data})
    return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")
