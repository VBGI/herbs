# -*- coding: utf-8 -*-
import operator
import datetime
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.forms.models import model_to_dict

from .models import Family, Genus, HerbItem, Species, SpeciesAuthorship
from .countries import codes as contry_codes
from .forms import SearchForm
from .conf import settings
from .utils import _smartify_altitude,_smartify_family, _smartify_dates

from django.utils.text import capfirst
from django.contrib.auth.decorators import login_required

from django.utils import translation, timezone

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
import json
import re
import gc

# from django.db.models.base import ModelState
digit_pat = re.compile(r'\d+')
countries = [key.decode('utf-8') for key in contry_codes]

from .hlabel import PDF_DOC


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
            bigquery += [Q(genus__gcode__contains=data['gcode'])] if data['gcode'] else []
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
                     'gcode': item.genus.gcode,
                     'id': item.pk,
                    # Extra data to show herbitem details
                     'ecodescr': item.ecodescr,
                     'altitude': item.altitude,
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
            objects = Genus.objects.filter(gcode__contains=query).order_by('gcode')
            data = [{'id': item.pk, 'text': item.gcode} for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
        elif cfield == 'genus':
            # TODO: DB structure: changes needed, (seems to be fixed...)
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


@login_required
def make_label(request, q):
    '''Return pdf-doc or error page otherwise.
    '''
    if len(q) > 100:
        return HttpResponse('Your query is too long... Try again')

    q = q.split(',')
    q = filter(lambda x: len(x) <= 15, q)  # No one can imagine that the number of sheet will exeeds 10^15.

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

    translation.activate('en')  # Labels are constructed in Eng. only
    llabel_data = []
    if objs.exists():
        for item in objs:
            ddict = _smartify_species(item)
            ddict.update({'date': _smartify_dates(item)})
            ddict.update({'family': _smartify_family(item.family.name),
                     'country': item.country,
                     'region': item.region,
                     'altitude': _smartify_altitude(item.altitude),
                     'latitude': '{0:.5f}'.format(item.coordinates.latitude) if item.coordinates else '',
                     'longitude': '{0:.5f}'.format(item.coordinates.longitude) if item.coordinates else '',
                     'place': item.detailed,
                     'collected': item.collectedby,
                     'identified': item.identifiedby,
                     'itemid': '%s' % item.pk,
                     'number': '%s' % item.itemcode if item.itemcode else '*',
                     'acronym': item.acronym.name if item.acronym else ''
                     })
            llabel_data.append(ddict)

    # We are ready to generate pdf-output
    pdf_template = PDF_DOC()
    pdf_template.tile_labels(llabel_data)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % timezone.now().strftime('%Y-%B-%d-%M-%s')
    response.write(pdf_template.get_pdf())
    del pdf_template
    gc.collect()
    return response


def _smartify_species(item):
    authors = [x for x in SpeciesAuthorship.objects.filter(species=item.species).order_by('priority')]
    howmany = len(authors) # We used len here because author's len<=3
    if howmany > 1:
        inside = [x for x in authors[:howmany-1]]
        spauth2 = ''
        if inside:
             spauth2 += ' '.join([x.get_name() for x in inside])
        spauth1 = authors[howmany-1].get_name()
    elif howmany == 1:
        spauth1 =  authors[0].get_name()
        spauth2 = ''
    else:
        spauth2 = ''
        spauth1 = ''
    species = capfirst(item.genus.name) + ' ' + \
        (item.species.name if item.species else '')
    return {'spauth1': spauth1, 'spauth2': spauth2, 'species': species}


