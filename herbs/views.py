# -*- coding: utf-8 -*-
import operator
import datetime
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Count
from django.forms.models import model_to_dict
from .models import Family, Genus, HerbItem, Species, Country, DetHistory
from .forms import SearchForm
from .conf import settings
from .utils import _smartify_altitude,_smartify_family, _smartify_dates
from django.utils.text import capfirst
from django.contrib.auth.decorators import login_required
from django.utils import translation, timezone
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
import json
import re
import gc
from .hlabel import PDF_DOC

digit_pat = re.compile(r'\d+')


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
        except HerbItem.DoesNotExist:
            context = {'error': u'Объект не найден'}
    return  HttpResponse(json.dumps(context),
                         content_type="application/json; charset=utf-8")

def parse_date(d):
    if not d: return None
    try:
       res = datetime.datetime.strptime(d, '%m/%d/%Y')
    except ValueError:
        res = None
    return res



# TODO: Fixes needed: DetHistory added
@csrf_exempt
def show_herbs(request):
    '''
    Get herbitems view
    '''
    if request.method == 'POST':
        return HttpResponse('Only GET-queries are acceptable')

    context = {'error': '', 'has_previous': None, 'has_next': None,
               'pagenumber': 1, 'pagecount': 0}

    if request.is_ajax():
        dataform = SearchForm(request.GET)
        if dataform.is_valid():
            data = {}
            for key in dataform.fields:
                if hasattr(dataform.cleaned_data[key], 'strip'):
                    data.update({key: dataform.cleaned_data[key].strip()})
                else:
                    data.update({key: dataform.cleaned_data[key]})
            bigquery = [Q(public=True)]
            bigquery += [Q(species__genus__family__name__iexact=data['family'])] if data['family'] else []
            bigquery += [Q(species__genus__name__iexact=data['genus'])] if data['genus'] else []
            bigquery += [Q(species__name__icontains=data['species'])] if data['species'] else []
            if data['itemcode']:
                bigquery += [Q(itemcode__icontains=data['itemcode'])|
                             Q(fieldid__icontains=data['itemcode'])|
                             Q(id__exact=data['itemcode'])
                             ]
            bigquery += [Q(collectedby__icontains=data['collectedby'])] if data['collectedby'] else []
            bigquery += [Q(identifiedby__icontains=data['identifiedby'])] if data['identifiedby'] else []
            if data['country']:
                bigquery += [Q(country__name_ru__icontains=data['country'])|
                             Q(country__name_en__icontains=data['country'])]

            # place handle #TODO: Probably note should be added to search fields
            bigquery += [Q(region__icontains=data['place'])|
                         Q(detailed__icontains=data['place'])|
                         Q(district__icontains=data['place'])] if data['place'] else []

            # dates
            if data['colend']:
                bigquery += [Q(collected_e__lt=data['colend'])]
            if data['colstart']:
                bigquery += [Q(collected_s__gt=data['colstart'])]

            object_filtered = HerbItem.objects.filter(reduce(operator.and_,
                                                             bigquery))

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
                    {
                     'species': item.get_full_name(),
                     'itemcode': item.itemcode,
                     'id': item.pk,
                     'fieldid': item.fieldid,
                    # Extra data to show herbitem details
                     'collectedby': item.collectedby,
                     'collected_s': item.collected_s,
                     'identifiedby': item.identifiedby,
                     'created': str(item.created),
                     'updated': str(item.updated)
                     })

            # ------------------------------------------------------------------
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
def show_herbitem(request, inum):
    context = {'error': ''}
    try:
        hobj = HerbItem.objects.get(id=inum)
        context.update({'curobj': hobj})
    except HerbItem.DoesNotExist:
        context.update({'error': 'No herbarium sheet with id=%s was found'%inum})
    result = render_to_string('herbitem_details.html', context,
                              context_instance=RequestContext(request))
    return HttpResponse(result)


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
        RU = translation.get_language() == 'ru'
        if cfield == 'family':
            famquery = Family.objects.annotate(herbitem_count=Count('genus__species__herbitem'))
            if query:
                objects = famquery.filter(name__istartswith=query, herbitem_count__gt=0)[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            else:
                objects = famquery.filter(herbitem_count__gt=0)[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]
            data = [{'id': item.pk, 'text': item.name} for item in objects]
        elif cfield == 'genus':
            genquery = Genus.objects.annotate(herbitem_count=Count('species__herbitem'))
            if dataform.cleaned_data['family']:
                if query:

                    objects = genquery.filter(family__name__iexact=dataform.cleaned_data['family'],
                                                   name__istartswith=query,
                                              herbitem_count__gt=0)
                else:
                    objects = genquery.filter(family__name__iexact=dataform.cleaned_data['family'],
                                                   herbitem_count__gt=0)
            else:
                if query:
                    objects = genquery.filter(name__istartswith=query, herbitem_count__gt=0)
                else:
                    objects = genquery.filter(herbitem_count__gt=0)
            data = [{'id': item.pk, 'text': item.name} for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
        elif cfield == 'country':
            objects = Country.objects.filter(Q(name_ru__icontains=query)|
                                             Q(name_en__icontains=query))
            data = [{'id': item.pk, 'text': item.name_ru if RU else item.name_en}
                    for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
    else:
        context.update({'error': 'Странный запрос'})
        data = []
    if data:
        for item in data: item['text'] = capfirst(item['text'])
    context.update({'items': data})
    return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")


@login_required
@never_cache
def make_label(request, q):
    '''Return pdf-doc or error page otherwise.
    '''
    if len(q) > 100:
        return HttpResponse('Your query is too long... Try again')

    q = q.split(',')
    q = filter(lambda x: len(x) <= 15, q)

    if len(q) > 4:
        return HttpResponse('You cannt generate more than 4 labels at a time. Try again.')


    # --------  Gathering data for labels ... --------
    q = map(lambda x: int(x), q)
    try:
       objs = HerbItem.objects.filter(public=True, id__in=q)
    except HerbItem.DoesNotExist:
       return HttpResponse('No herbarium sheets were found.\
                                Make sure you made search for public items.\
                                Non-public items not showed.')
    if not objs.exists():
        return HttpResponse('Empty or malformed query. Try again')
    lang = translation.get_language()
    translation.activate('en')  # Labels are constructed in Eng. only
    llabel_data = []
    if objs.exists():
        for item in objs:
            # -------------- get indentifiedby ---------------
            if not item.identifiedby:
                try:
                    dhist = DetHistory.objects.filter(herbitem=item).latest('identified_s')
                    identified = dhist.identifiedby
                except DetHistory.DoesNotExist:
                    identified = ''
            else:
                identified = item.identifiedby
            ddict = _smartify_species(item)
            ddict.update({'date': _smartify_dates(item)})
            ddict.update({'family': item.species.genus.family.name.upper() if item.species else '',
                     'country': item.country.name_en if item.country else '',
                     'region': item.region,
                     'altitude': _smartify_altitude(item.altitude),
                     'latitude': '{0:.5f}'.format(item.coordinates.latitude) if item.coordinates else '',
                     'longitude': '{0:.5f}'.format(item.coordinates.longitude) if item.coordinates else '',
                     'place': item.detailed,
                     'collected': item.collectedby,
                     'identified': identified,
                     'itemid': '%s' % item.pk,
                     'number': '%s' % item.itemcode or '*',
                     'acronym': item.acronym.name if item.acronym else '',
                     'address': item.acronym.address if item.acronym else '',
                     'institute': item.acronym.institute if item.acronym else '',
                     'gform': item.devstage or '',
                     'fieldid': item.fieldid
                     })
            llabel_data.append(ddict)

    # We are ready to generate pdf-output
    pdf_template = PDF_DOC()
    pdf_template.tile_labels(llabel_data)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % timezone.now().strftime('%Y-%B-%d-%M-%s')
    response.write(pdf_template.get_pdf())
    translation.activate(lang)
    del pdf_template
    gc.collect()
    return response


def _smartify_species(item):
    if item.species:
        if item.species.genus:
            species = capfirst(item.species.genus.name) + ' ' + item.species.name
        else:
            species = 'No genus ' + item.species.name
        authorship = item.species.authorship or ''
    else:
        species = ''
        authorship = ''
    return {'spauth': authorship, 'species': species}


