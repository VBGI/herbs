# -*- coding: utf-8 -*-
import operator
from django.http import HttpResponse, StreamingHttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.forms.models import model_to_dict
from django.utils.translation import ugettext as _
from .models import (Family, Genus, HerbItem, Country,
                     DetHistory, Species, SpeciesSynonym, Additionals,
                     HerbCounter, Subdivision)
from .forms import SearchForm, RectSelectorForm
from .conf import settings
from .utils import _smartify_altitude, _smartify_dates, herb_as_dict, translit
from streamingjson import JSONEncoder as JSONStreamer
from django.utils.text import capfirst
from django.contrib.auth.decorators import login_required
from django.utils import translation, timezone
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings as main_settings

import json
import re
import gc
import csv
import os
from .hlabel import PDF_DOC, BARCODE, PDF_BRYOPHYTE
try:
    from django.core.cache import cache
except (ImportError,ImproperlyConfigured):
    cache = None


digit_pat = re.compile(r'\d+')

class EchoData(object):
    def write(self, value):
        return value

def _get_rows_for_csv(queryset):
    header = []
    for field in HerbItem._meta.fields:
        header.append(field.name)
    header.remove('coordinates')
    header.append('latitude')
    header.append('longitude')
    header.append('family')
    yield header
    for qs_obj in queryset.iterator():
        row = []
        for field in header:
            cur_property = getattr(qs_obj, field, None)
            if cur_property is not None:
                if callable(cur_property):
                    val = cur_property()
                else:
                    val = cur_property

                if (field == 'acronym') or (field == 'subdivision'):
                    val = cur_property.name

                if field == 'country':
                    val = cur_property.name_ru if translation.get_language() == 'ru' else cur_property.name_en

                if field == 'devstage':
                    val = qs_obj.get_devstage_display()
                row.append(val)
            else:
                if (field == 'latitude'):
                    val = '%s' % qs_obj.coordinates.latitude if qs_obj.coordinates else ''
                elif (field == 'longitude'):
                    val = '%s'  % qs_obj.coordinates.longitude if qs_obj.coordinates else ''
                elif (field =='family'):
                    val = capfirst(qs_obj.species.genus.family.name) if qs_obj.species else ''
                else:
                    val = ''
                row.append(val)
        yield row


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


def get_data(request):
    '''Evaluate search query and return data'''

    errors = []
    warnings = []
    objects_filtered = HerbItem.objects.none()

    if request.method == 'POST':
        errors.append(_(u'Допустимы только GET-запросы'))
        return (None, 0, 0, objects_filtered , errors, warnings)

    dataform = SearchForm(request.GET)
    rectform = RectSelectorForm(request.GET)
    search_by_synonyms = request.GET.get('synonyms', False)
    if search_by_synonyms == 'true':
        search_by_synonyms = True
    elif search_by_synonyms == 'false':
        search_by_synonyms = False
    else:
        search_by_synonyms = False

    search_by_additionals = request.GET.get('additionals', False)
    if search_by_additionals == 'true':
        search_by_additionals = True
    elif search_by_additionals == 'false':
        search_by_additionals =  False
    else:
        search_by_additionals = False

    if dataform.is_valid():
        data = {}
        for key in dataform.fields:
            if hasattr(dataform.cleaned_data[key], 'strip'):
                data.update({key: dataform.cleaned_data[key].strip()})
            else:
                data.update({key: dataform.cleaned_data[key]})
        bigquery = []

        # -------- synonyms searching -----------------------
        if search_by_synonyms:
            species_queryset = Species.objects.filter(genus__name__iexact=data['genus'], name__iexact=data['species_epithet']).exclude(status='D')
            # make a warning if species object isn't unique... TODO!
            if species_queryset.exists():
                syn_aux = map(lambda x: Q(json_content__contains=',' + '%s' % x + ','),
                                species_queryset.values_list('id', flat=True))
                intermediate = filter(bool,
                                        sum([item.json_content.split(',') for item in SpeciesSynonym.objects.filter(reduce(operator.or_, syn_aux))], []))
                try:
                    intermediate =  map(int, intermediate)
                except (ValueError, TypeError):
                    intermediate = []
                if intermediate:
                    bigquery += [Q(species__pk__in=intermediate)]
                else:
                    warnings.append(_(u'Неверно сформированы таблицы синонимов. Условие поиска по синонимам прогнорировано.'))
                    search_by_synonyms = False
            else:
                warnings.append(_(u'Не заданы поля род и/или видовой эпитет, либо такой вид отсутствует в базе. Условие поиска по синонимам проигнорировано.'))
                search_by_synonyms = False

        if not search_by_synonyms:
            bigquery += [Q(species__genus__family__name__iexact=data['family'])] if data['family'] else []
            bigquery += [Q(species__genus__name__iexact=data['genus'])] if data['genus'] else []
            bigquery += [Q(species__name__icontains=data['species_epithet'])|
                         Q(species__infra_epithet__icontains=data['species_epithet'])] if data['species_epithet'] else []
        # -----------------------------------------------------

        # ------ Searching in History of determination --------
        dethistory_query = []
        if search_by_synonyms:
            dethistory_query += [Q(dethistory__species__pk__in=intermediate)]
        else:
            dethistory_query += [Q(dethistory__species__name__icontains=data['species_epithet'])|
                                 Q(dethistory__species__infra_epithet__icontains=data['species_epithet'])] if data['species_epithet'] else []
            dethistory_query += [Q(dethistory__species__genus__name__iexact=data['genus'])] if data['genus'] else []
            dethistory_query += [Q(dethistory__species__genus__family__name__iexact=data['family'])] if data['family'] else []
        if dethistory_query:
            dethistory_query = reduce(operator.and_, dethistory_query)

        # ---------- searching by additionals -----------------
        additionals_query = []
        if search_by_additionals:
            if search_by_synonyms:
                additionals_query += [Q(additionals__species__pk__in=intermediate)]
            else:
                additionals_query += [Q(additionals__species__name__icontains=data['species_epithet'])|
                                      Q(additionals__species__infra_epithet__icontains=data['species_epithet'])
                                      ] if data['species_epithet'] else []
                additionals_query += [Q(additionals__species__genus__name__iexact=data['genus'])] if data['genus'] else []
                additionals_query += [Q(additionals__species__genus__family__name__iexact=data['family'])] if data['family'] else []
        if additionals_query:
            additionals_query = reduce(operator.and_, additionals_query)

        # ------  Searching by rectangular selection...
        if rectform.is_valid():
            latl = rectform.cleaned_data['latl']
            latu = rectform.cleaned_data['latu']
            lonl = rectform.cleaned_data['lonl']
            lonu = rectform.cleaned_data['lonu']
            if None in [latl, lonl, latu, lonu] and any([latl, lonl, latu, lonu]):
                warnings.append(_(u'Заданы не все границы области поиска. Условия поиска по области будут проигнорированы.'))
            elif (not (-90.0 <= latl <= 90) or not (-90.0 <= latu <= 90.0) or
                  not (-180.0 <= lonl <= 180.0) or not(-180.0 <= lonu <= 180.0))\
                  and all([latl, lonl, latu, lonu]):
                warnings.append(_(u'Границы области поиска неправдоподобны для географических координат. Условя поиска по области будут проигнорированы.'))
            elif all([latl, lonl, latu, lonu]):
                bigquery += [Q(latitude__gte=latl) & Q(latitude__lte=latu)]
                if lonu < lonl:
                    bigquery += [(Q(longitude__gte=lonl) & Q(longitude__lte=180.0)) |
                                 (Q(longitude__gte=-180.0) & Q(longitude__lte=lonu))]
                else:
                    bigquery += [Q(longitude__gte=lonl) & Q(longitude__lte=lonu)]
        else:
            warnings.append(_(u'Область на карте задана нeкорректно. Условия поиска по области будут проигнорированы.'))

        if data['itemcode']:
            try:
                intitemcode = int(data['itemcode'])
                bigquery += [Q(itemcode__icontains=data['itemcode'])|
                            Q(fieldid__icontains=data['itemcode'])|
                            Q(id=intitemcode)
                            ]

            except (ValueError, TypeError):
                    bigquery += [Q(itemcode__icontains=data['itemcode'])|
                            Q(fieldid__icontains=data['itemcode'])
                            ]

        bigquery += [Q(collectedby__icontains=data['collectedby'])|
                     Q(collectedby__icontains=translit(data['collectedby'],
                                                       'ru',
                                                       reversed=True))] if data['collectedby'] else []
        bigquery += [Q(identifiedby__icontains=data['identifiedby'])|
                     Q(identifiedby__icontains=translit(data['identifiedby'],'ru',
                                                             reversed=True))] if data['identifiedby'] else []
        if data['country']:
            bigquery += [Q(country__name_ru__icontains=data['country'])|
                            Q(country__name_en__icontains=data['country'])]

        bigquery += [Q(region__icontains=data['place'])|
                        Q(detailed__icontains=data['place'])|
                        Q(district__icontains=data['place'])|
                        Q(note__icontains=data['place'])] if data['place'] else []

        # dates
        if data['colend'] and data['colstart']:
            colendin = Q(collected_e__gte=data['colstart']) & Q(collected_e__lte=data['colend'])
            colstartin = Q(collected_s__gte=data['colstart']) & Q(collected_s__lte=data['colend'])
            bigquery += [colstartin | colendin]
        elif data['colstart']:
            bigquery += [Q(collected_s__gte=data['colstart']) | Q(collected_e__gte=data['colstart'])]
        elif data['colend']:
            bigquery += [Q(collected_s__lte=data['colend']) | Q(collected_e__lte=data['colend'])]

        # acronym filtering
        acronym = request.GET.get('acronym', '')
        try:
            acronym = int(acronym)
            bigquery += [Q(acronym__id=acronym)]
        except (ValueError, TypeError):
            if acronym:
                bigquery += [Q(acronym__name__iexact=acronym)]

        # subdivision filtering
        subdivision = request.GET.get('subdivision', '')
        try:
            subdivision = int(subdivision)
            try:
                thesubdiv = Subdivision.objects.get(id=subdivision)
                subdivisions = [item.pk for item in thesubdiv.get_all_children()]
            except Subdivision.DoesNotExist:
                subdivisions = [subdivision]
            bigquery += [Q(subdivision__id__in=subdivisions)]
        except (ValueError, TypeError):
            if subdivision:
                bigquery += [Q(subdivision__name__icontains=subdivision)]

        if dethistory_query and additionals_query:
            extra_query = dethistory_query | additionals_query
        else:
            extra_query = dethistory_query or additionals_query

        if extra_query and bigquery:
            objects_filtered = HerbItem.objects.filter(reduce(operator.and_,
                                                          bigquery)|
                                                   extra_query).exclude(public=False)
        elif bigquery:
            objects_filtered = HerbItem.objects.filter(reduce(operator.and_,
                                                          bigquery)).exclude(public=False)
        else:
            objects_filtered = HerbItem.objects.filter(public=True)
        if not objects_filtered.exists():
            msg = _(u"Ни одного элемента не удовлетворяет условиям поискового запроса")
            warnings.append(msg)
            return (None, 1, 0, objects_filtered, errors, warnings)
        else:
            # --------- Applying ordering to results retrieved ----------------
            ordering_direction = request.GET.get('order', False)
            if ordering_direction == 'true':
                ordering_direction = True
            elif ordering_direction == 'false':
                ordering_direction =  False
            else:
                ordering_direction = True

            ordering_field = request.GET.get('orderby', 'id')
            if ordering_field not in [x[0] for x in settings.HERBS_SEARCHFORM_ORDERING_FIELDS]:
                ordering_field = 'id'
            ord_string = '' if ordering_direction else '-'
            objects_filtered = objects_filtered.order_by(ord_string\
                                                        + ordering_field)

            # ---------  pagination-----------------
            pagcount = request.GET.get('pagcount', '')
            page = request.GET.get('page', '1')
            pagcount = int(pagcount) if pagcount.isdigit() else settings.HERBS_PAGINATION_COUNT
            page = int(page) if page.isdigit() else 1
            if pagcount <= 0 or pagcount > 1000:
                pagcount = settings.HERBS_PAGINATION_COUNT
                warnings.append(_(u'Задано недопустимое количество объектов для оторажения на одной странице: ') + str(pagcount))
            paginator = Paginator(objects_filtered, pagcount)
            try:
                paginated_data = paginator.page(page)
            except:
                paginated_data = paginator.page(1)
            return (paginated_data, page, paginator.num_pages, objects_filtered,
                    errors, warnings)
    else:
        errors.append(_(u'Некорректно сформированный поисковый запрос.'))
        return (None, 0, 0, objects_filtered, errors, warnings)


def json_generator(queryset):
    for obj in queryset.iterator():
        if cache:
            cache.set(settings.HERBS_JSON_API_CONN_KEY_FLAG, 1,
                      settings.HERBS_JSON_API_CONN_TIMEOUT)
        yield herb_as_dict(obj)
    if cache:
        if cache.get(settings.HERBS_JSON_API_CONN_KEY_NAME) is not None:
            cache.decr(settings.HERBS_JSON_API_CONN_KEY_NAME)
            cache.delete(settings.HERBS_JSON_API_CONN_KEY_FLAG)


@never_cache
def json_api(request):
    '''Herbarium json-api view '''

    gc.collect()
    context = {
        'errors': [],
        'warnings': [],
        'data': [],
    }
    allowed_parameters = set(('family', 'genus', 'id', 'species_epithet',
                              'itemcode', 'identifiedby', 'place', 'collectedby',
                              'country', 'colstart', 'colend', 'acronym',
                              'subdivision', 'synonyms', 'additionals', 'latl',
                              'latu', 'lonl', 'lonu', 'additionals', 'fieldid',
                              'authorship'))

    if request.method == 'POST':
        context['errors'].append('Only GET-requests is allowed')

    current_parameters = set(request.GET.keys())
    diff = current_parameters - allowed_parameters
    if len(diff) > 0:
        extra_key_warning = 'Following GET-parameters were ignored: ' +\
                            ', '.join(map(lambda x: x.encode('utf-8'), diff))
        context['warnings'].append(extra_key_warning)

    if len(current_parameters.intersection(allowed_parameters)) == 0:
        context['errors'].append("Making empty searching requests aren't permitted")
        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder),
                            content_type="application/json;charset=utf-8")

    hid = request.GET.get('id', None)
    if hid:
        try:
           hid = int(hid)
        except (ValueError, TypeError):
           context['errors'].append("Illegal format of ID")
           return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder))
        objects_filtered = HerbItem.objects.filter(id=hid)
        context['warnings'].append("All searching fields will be ignored when do searching by ID")
        if objects_filtered.exists():
            if objects_filtered[0].public:
                context.update({'data':[herb_as_dict(objects_filtered[0])]})
            else:
                context.update({'data': []})
                context['errors'].append("The record with this ID isn't published")
        else:
            context['errors'].append("The record with the requested ID wasn't found")
        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder),
                            content_type="application/json;charset=utf-8")

    # -------- Long-running http-response: check the number of connections
    if cache:
        conn = cache.get(settings.HERBS_JSON_API_CONN_KEY_NAME)
        flag = cache.get(settings.HERBS_JSON_API_CONN_KEY_FLAG)
        if conn is None or flag is None:
            cache.set(settings.HERBS_JSON_API_CONN_KEY_NAME, 1)
        elif conn >= settings.HERBS_JSON_API_SIMULTANEOUS_CONN:
            context['errors'].append('Server is busy. Try again later.')
            return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder),
                                content_type="application/json;charset=utf-8")
        else:
            cache.incr(settings.HERBS_JSON_API_CONN_KEY_NAME)

    current_lang = translation.get_language()
    translation.activate('en')
    no, no, no, objects_filtered, errors, warnings = get_data(request)
    translation.activate(current_lang)
    authorship = request.GET.get('authorship', '')[:settings.HERBS_ALLOWED_AUTHORSHIP_SYMB_IN_GET]
    fieldid = request.GET.get('fieldid', '')[:settings.HERBS_ALLOWED_FIELDID_SYMB_IN_GET]
    itemcode = request.GET.get('itemcode', '')[:settings.HERBS_ALLOWED_ITEMCODE_SYMB_IN_GET]
    if authorship:
        objects_filtered = objects_filtered.filter(authorship__icontains=authorship)
    if fieldid:
        objects_filtered = objects_filtered.filter(fieldid__icontains=fieldid)
    if itemcode:
        objects_filtered = objects_filtered.filter(itemcode__icontains=itemcode)
    json_streamer = JSONStreamer(ensure_ascii=False)
    context['errors'].extend(errors)
    context['warnings'].extend(warnings)
    context.update({'data': json_generator(objects_filtered)})
    json_response = StreamingHttpResponse(json_streamer.iterencode(context),
                                          content_type="application/json;charset=utf-8")
    return json_response


@csrf_exempt
def show_herbs(request):
    '''
    Show all specimen records
    '''
    if not request.is_ajax():
        return HttpResponse(_(u'Допустимы только XMLHttp-запросы'))

    paginated_data, page, num_pages, objects_filtered, errors, warnings = get_data(request)

    if request.GET.get('getcsv', None) and request.user.is_authenticated():
        writer = csv.writer(EchoData(), delimiter=';')
        csv_response = StreamingHttpResponse((writer.writerow([unicode(s).encode("utf-8") for s in row]) for row in _get_rows_for_csv(objects_filtered)), content_type="text/csv")
        csv_response['Content-Disposition'] = 'attachment; filename=herb_data_%s.csv' % timezone.now().strftime('%Y-%B-%d-%M-%s')
        return csv_response

    lang = translation.get_language()
    if paginated_data:
        data_tojson = []
        for item in paginated_data.object_list:
            hc = item.herbcounter.all()
            data_tojson.append(
                {
                    'species': item.get_full_name(),
                    'itemcode': item.itemcode,
                    'id': item.pk,
                    'herbhits': hc[0].count if hc.exists() else 0,
                    'fieldid': item.fieldid,
                    'lat': '{0:.5f}'.format(item.coordinates.latitude) if item.coordinates else '0.0',
                    'lon': '{0:.5f}'.format(item.coordinates.longitude) if item.coordinates else '0.0',
                    'collectedby': item.collectedby if lang == 'ru' else translit(item.collectedby, 'ru', reversed=True),
                    'collected_s': item.collected_s,
                    'identifiedby': item.identifiedby if lang == 'ru' else translit(item.identifiedby, 'ru', reversed=True),
                    'created': str(item.created),
                    'updated': str(item.updated),
                    'has_images': True if item.has_images else False
                    })

        # ------------------------------------------------------------------
        context = {'herbitems' : data_tojson,
                   'has_previous': paginated_data.has_previous(),
                   'has_next': paginated_data.has_next(),
                   'pagenumber': page,
                   'pagecount': num_pages,
                   'total': objects_filtered.count(),
                   'errors': errors,
                   'warnings': warnings
                   }

        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type="application/json;charset=utf-8")
    else:
        context = {'herbitems': [],
                   'total': 0,
                   'has_previous': False,
                   'has_next': False,
                   'pagenumber': page,
                   'pagecount': num_pages,
                   'total': 0,
                   'errors': errors,
                   'warnings': warnings}
        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type="application/json;charset=utf-8")


@never_cache
@csrf_exempt
def show_herbitem(request, inum):
    context = {'error': ''}
    clang = request.POST.get('lang', 'ru')
    if clang not in ['ru', 'en']:
        translation.activate('ru')
    else:
        translation.activate(clang)


    try:
        hobj = HerbItem.objects.get(id=inum)

        # ---------- get image urls

        if hobj.has_images:
            urls = []
            splitted = hobj.has_images.split(',')
            baseurl = '/'.join(s.strip('/') for s in
                           [getattr(main_settings, 'HERBS_SOURCE_IMAGE_URL_RELATIVE', ''),
                            hobj.acronym.name])
            for im in splitted:
                getpars = '&'.join(["baseurl=%s" % baseurl,
                            "resolution=ss",
                            "image=%s" % os.path.basename(im)
                            ])
                urls.append(getattr(main_settings, 'HERBS_SOURCE_IMAGE_VIEWER', '') + '?' + getpars)
            image_urls = [(x, y) for x,y in zip(splitted, urls)]
        else:
            image_urls = []

        #--------------------------

        if hobj.public:
            if hobj.herbcounter.exists():
                hc = hobj.herbcounter.all()[0]
                hc.count += 1
                hc.save()
            else:
                HerbCounter.objects.create(herbitem=hobj, count=1)
        context.update({'curobj': hobj, 'image_urls': image_urls})
    except HerbItem.DoesNotExist:
        context.update({'error': _(u'Гербарного образца с id=%s не было найдено') % inum})
    result = render_to_string('herbitem_details.html', context,
                              context_instance=RequestContext(request))
    return HttpResponse(result)


@never_cache
def advice_select(request):
    if not request.is_ajax():
        return HttpResponse(_(u'Допустимы только XMLHttp запросы'))
    if request.method == 'POST':
        return HttpResponse(_(u'Допустимы только GET-методы'))

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
                objects = famquery.filter(name__istartswith=query, herbitem_count__gt=0).order_by('name')
            else:
                objects = famquery.filter(herbitem_count__gt=0).order_by('name')
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
            data = [{'id': item.pk, 'text': item.name} for item in objects.order_by('name')]
        elif cfield == 'country':
            objects = Country.objects.filter(Q(name_ru__icontains=query)|
                                             Q(name_en__icontains=query))
            data = [{'id': item.pk, 'text': item.name_ru if RU else item.name_en}
                    for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
    else:
        context.update({'error': _(u'Странный запрос')})
        data = []
    if data:
        for item in data: item['text'] = capfirst(item['text'])
    context.update({'items': data})
    return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")


def collect_label_data(q):
    result = []
    q = map(lambda x: int(x), q)
    objs = HerbItem.objects.filter(public=True, id__in=q)
    if not objs.exists():
        return result
    lang = translation.get_language()
    translation.activate('en')
    if objs.exists():
        for item in objs:
            history = DetHistory.objects.filter(herbitem=item)
            if not item.identifiedby:
                try:
                    dhist = history.latest('identified_s')
                    identified = dhist.identifiedby
                except DetHistory.DoesNotExist:
                    identified = ''
            else:
                identified = item.identifiedby

            _dethistory = []
            if history.exists():
                for hist_obj in history:
                    if hist_obj.species:
                        _sp_hist = _smartify_species(hist_obj)
                        _dethistory.append(
                            {
            'identifiedby': hist_obj.identifiedby,
            'identified': _smartify_dates(hist_obj, prefix='identified'),
            'species': _sp_hist
                            }
                                           )

            addspecies = []
            addsps_obj = Additionals.objects.filter(herbitem=item)
            if addsps_obj.exists():
                for addsp in addsps_obj:
                    addspecies.append([addsp.get_basic_name(),
                                       addsp.species.authorship,
                                       addsp.species.get_infra_rank_display(),
                                       addsp.species.infra_epithet,
                                       addsp.note])
            ddict = _smartify_species(item)
            ddict.update({'coldate': _smartify_dates(item)})
            ddict.update({'detdate': _smartify_dates(item, prefix='identified')})
            current_family = ''
            if item.species:
                if item.species.genus.family:
                    current_family = item.species.genus.family.name.upper()
            ddict.update({'family': current_family,
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
                        'fieldid': item.fieldid or '',
                        'addspecies': addspecies,
                        'district': item.district or '',
                        'note': item.note or '',
                        'short_note': item.short_note or '',
                        'gpsbased': item.gpsbased,
                        'dethistory':  _dethistory,
                        'logo_path': os.path.join(getattr(main_settings,
                                                          'MEDIA_ROOT', ''),
                                                  str(item.acronym.logo)) if item.acronym else ''
                          })
            result.append(ddict)
    translation.activate(lang)
    return result


@login_required
@never_cache
def make_label(request, q):
    '''Return pdf-doc or error page otherwise'''
    if len(q) > 1000:
        return HttpResponse(_(u'Ваш запрос слишком длинный, выберите меньшее количество элементов'))

    q = q.split(',')
    q = filter(lambda x: len(x) <= 15, q)

    if len(q) > 100:
        return HttpResponse(_(u'Вы не можете создать более 100 этикеток одновременно'))
    label_data = collect_label_data(q)

    if not label_data:
        return HttpResponse(_(u'Не выбрано ни одного образца для создания этикеток'))

    # Generate pdf-output
    pdf_template = PDF_DOC()
    pdf_template.tile_labels(label_data)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % timezone.now().strftime('%Y-%B-%d-%M-%s')
    response.write(pdf_template.get_pdf())
    del pdf_template
    gc.collect()
    return response


@login_required
@never_cache
def make_bryopyte_label(request, q):
    '''Return pdf-doc or error page otherwise'''

    if len(q) > 1000:
        return HttpResponse(_(u'Ваш запрос слишком длинный, выберите меньшее количество элементов'))

    q = q.split(',')
    q = filter(lambda x: len(x) <= 15, q)

    if len(q) > 100:
        return HttpResponse(_(u'Вы не можете создать более 100 этикеток одновременно'))
    label_data = collect_label_data(q)

    if not label_data:
        return HttpResponse(_(u'Не выбрано ни одного образца для создания этикеток'))

    preprocessed_labels = []
    for label in label_data:
        label.pop('logo_path', None)
        label.pop('gform', None)
        label.pop('address', None)
        label.pop('number', None)
        label.pop('family', None)
        allspecies = [[label['species'],
                       label['spauth'],
                       label['infra_rank'],
                       label['infra_epithet'],
                       label['short_note'] or '']] + label['addspecies']
        label.pop('short_note', None)
        label.pop('addspecies', None)
        label.pop('spauth', None)
        label.pop('infra_rank', None)
        label.pop('infra_epithet', None)
        label.pop('species', None)
        label.update({'allspecies': allspecies})
        preprocessed_labels.append(label)
    # Generate pdf-outputmake_bryophyte_label
    pdf_template = PDF_BRYOPHYTE()
    pdf_template.generate_labels(preprocessed_labels)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % timezone.now().strftime('%Y-%B-%d-%M-%s')
    response.write(pdf_template.get_pdf())
    del pdf_template
    gc.collect()
    return response


@login_required
@never_cache
def make_barcodes(request, q):
    '''Return pdf-file of barcodes'''

    if len(q) > 2000:
        return HttpResponse(_(u'Ваш запрос слишком длинный, выберите меньшее количество элементов'))

    q = q.split(',')
    q = filter(lambda x: len(x) <= 15, q)

    if len(q) > 100:
        return HttpResponse(_(u'Вы не можете создать более 100 этикеток одновременно'))

    q = map(lambda x: int(x), q)

    objs = HerbItem.objects.filter(id__in=q)

    if not objs.exists():
        return HttpResponse(_(u'Пустой или неправильно сформированный запрос'))
    array = []
    if objs.exists():
        for item in objs:
            array.append({'acronym': item.acronym.name if item.acronym else '',
                          'id': item.pk,
                          'institute': item.acronym.institute if item.acronym else ''
                          })
    # NOw, we are ready to produce pdf-output
    pdf_template = BARCODE()
    pdf_template.spread_codes(array)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="BCS%s.pdf"' % timezone.now().strftime('%Y-%B-%d-%M-%s')
    response.write(pdf_template.get_pdf())
    del pdf_template
    gc.collect()
    return response

def _smartify_species(item):
    if item.species:
        if item.species.genus:
            siglevel = item.significance + ' ' if item.significance else ''
            species = capfirst(item.species.genus.name) + ' ' + \
                      siglevel + item.species.name
        else:
            species = 'No genus ' + item.species.name
        authorship = item.species.authorship or ''
    else:
        species = ''
        authorship = ''
    return {'spauth': authorship, 'species': species,
            'infra_rank': item.species.get_infra_rank_display(),
            'infra_epithet': item.species.infra_epithet}

