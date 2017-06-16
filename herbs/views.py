# -*- coding: utf-8 -*-
import operator
import datetime
from django.http import HttpResponse, StreamingHttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _
from .models import (Family, Genus, HerbItem, Country,
                     DetHistory, Species, SpeciesSynonym)
from .forms import SearchForm, RectSelectorForm
from .conf import settings
from .utils import _smartify_altitude, _smartify_dates, herb_as_dict
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
import json
import re
import gc
import csv
from .hlabel import PDF_DOC
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

def parse_date(d):
    if not d: return None
    try:
       res = datetime.datetime.strptime(d, '%m/%d/%Y')
    except (ValueError, TypeError):
        res = None
    return res


def get_data(request):
    '''Evaluate search query and return data'''

    errors = []
    warnings = []
    objects_filtered = HerbItem.objects.none()

    dataform = SearchForm(request.GET)
    rectform = RectSelectorForm(request.GET)
    search_by_synonyms = request.GET.get('synonyms', False)
    if search_by_synonyms == 'true':
        search_by_synonyms = True
    elif search_by_synonyms == 'false':
        search_by_synonyms = False
    else:
        search_by_synonyms = False

    search_by_adds = request.GET.get('adds', False)
    if search_by_adds == 'true':
        search_by_adds = True
    elif search_by_adds == 'false':
        search_by_adds =  False
    else:
        search_by_adds = False

    if dataform.is_valid():
        data = {}
        for key in dataform.fields:
            if hasattr(dataform.cleaned_data[key], 'strip'):
                data.update({key: dataform.cleaned_data[key].strip()})
            else:
                data.update({key: dataform.cleaned_data[key]})
        bigquery = [Q(public=True)]

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
                    warnings.append(_('Неверно сформированы таблицы синонимов. Условие поиска по синонимам прогнорировано.'))
                    search_by_synonyms = False
            else:
                warnings.append(_('Не заданы поля род и/или видовой эпитет, либо такой вид отсутствует в базе. Условие поиска по синонимам проигнорировано.'))
                search_by_synonyms = False

        if not search_by_synonyms:
            bigquery += [Q(species__genus__family__name__iexact=data['family'])] if data['family'] else []
            bigquery += [Q(species__genus__name__iexact=data['genus'])] if data['genus'] else []
            bigquery += [Q(species__name__icontains=data['species_epithet'])] if data['species_epithet'] else []
        # -----------------------------------------------------

        # ------ Searching in History of determination --------
        dethistory_query = []
        if search_by_synonyms:
            dethistory_query += [Q(dethistory__species__pk__in=intermediate)]
        else:
            dethistory_query += [Q(dethistory__species__name__icontains=data['species_epithet'])] if data['species_epithet'] else []
            dethistory_query += [Q(dethistory__species__genus__name__iexact=data['genus'])] if data['genus'] else []
            dethistory_query += [Q(dethistory__species__genus__family__name__iexact=data['family'])] if data['family'] else []
        if dethistory_query:
            dethistory_query = reduce(operator.and_, dethistory_query)


        # ------  Searching by rectangular selection...
        if rectform.is_valid():
            latl = rectform.cleaned_data['latl']
            latu = rectform.cleaned_data['latu']
            lonl = rectform.cleaned_data['lonl']
            lonu = rectform.cleaned_data['lonu']
            if None in [latl, lonl, latu, lonu] and any([latl, lonl, latu, lonu]):
                warnings.append(_('Заданы не все границы области поиска. Условия поиска по области будут проигнорированы.'))
            elif (not (-90.0 <= latl <= 90) or not (-90.0 <= latu <= 90.0) or
                  not (-180.0 <= lonl <= 180.0) or not(-180.0 <= lonu <= 180.0))\
                  and all([latl, lonl, latu, lonu]):
                warnings.append(_('Границы области поиска неправдоподобны для географических координат. Условя поиска по области будут проигнорированы.'))
            elif all([latl, lonl, latu, lonu]):
                bigquery += [Q(latitude__gte=latl) & Q(latitude__lte=latu)]
                if lonu < lonl:
                    bigquery += [(Q(longitude__gte=lonl) & Q(longitude__lte=180.0)) |
                                 (Q(longitude__gte=-180.0) & Q(longitude__lte=lonu))]
                else:
                    bigquery += [Q(longitude__gte=lonl) & Q(longitude__lte=lonu)]
        else:
            warnings.append(_('Область на карте задана нeкорректно. Условия поиска по области будут проигнорированы.'))

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

        bigquery += [Q(collectedby__icontains=data['collectedby'])] if data['collectedby'] else []
        bigquery += [Q(identifiedby__icontains=data['identifiedby'])] if data['identifiedby'] else []
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
            bigquery += [Q(acronym__name__iexact=acronym)]

        # subdivision filtering
        subdivision = request.GET.get('subdivision', '')
        try:
            subdivision = int(subdivision)
            bigquery += [Q(subdivision__id=subdivision)]
        except (ValueError, TypeError):
            bigquery += [Q(subdivision__name__icontains=subdivision)]

        if dethistory_query:
            objects_filtered = HerbItem.objects.filter(reduce(operator.and_,
                                                            bigquery)|dethistory_query)
        else:
            objects_filtered = HerbItem.objects.filter(reduce(operator.and_, bigquery))

        if not objects_filtered.exists():
            warnings.append(_("Ни одного элемента не удовлетворяет условиям поискового запроса"))
            return (None, 1, 0, objects_filtered, errors, warnings)
        else:
            # ------- Sorting items --------------
            # sorting isn't implemented yet
            # ---------  pagination-----------------
            pagcount = request.GET.get('pagcount', '')
            page = request.GET.get('page', '1')
            pagcount = int(pagcount) if pagcount.isdigit() else settings.HERBS_PAGINATION_COUNT
            page = int(page) if page.isdigit() else 1
            if pagcount <= 0 or pagcount > 1000:
                pagcount = settings.HERBS_PAGINATION_COUNT
                warnings.append(_('Задано недопустимое количество объектов для оторажения на одной странице: ') + str(pagcount))
            paginator = Paginator(objects_filtered, pagcount)
            try:
                paginated_data = paginator.page(page)
            except:
                paginated_data = paginator.page(1)
            return (paginated_data, page, paginator.num_pages, objects_filtered,
                    errors, warnings)
    else:
        errors.append(_('Некорректно сформированный поисковый запрос.'))
        return (None, 0, 0, None, errors, warnings)




def json_generator(queryset):
    for obj in queryset.iterator():
        yield herb_as_dict(obj)
    if cache:
        if cache.get(settings.HERBS_JSON_API_CONN_KEY_NAME) is not None:
            cache.decr(settings.HERBS_JSON_API_CONN_KEY_NAME)

@never_cache
def json_api(request):
    '''Herbarium json-api view '''

    gc.collect()
    context = {
        'errors': [],
        'warnings': [],
        'data': [],
    }

    if request.method == 'POST':
        context['errors'].append(_('Допустимы только GET-запросы'))

    #  TODO: Make a warning if GET has disallowed paramaters...


    hid = request.GET.get('id', None)
    if hid:
        try:
            objects_filtered = HerbItem.objects.filter(id=hid)
        except HerbItem.DoesNotExist:
            context['errors'].append(_('Объект с данным ID не найден'))
            context['warnings'].append(_('При поиске по ID другие поля поиска игнорируются'))
            objects_filtered = HerbItem.objects.none()
        if objects_filtered.exists():
            if objects_filtered[0].public:
                context.update({'data':[herb_as_dict(objects_filtered[0])]})
            else:
                context.update({'data': []})
                context['errors'].append(_('Объект с данным ID не опубликован'))
        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder),
                            content_type="application/json;charset=utf-8")

    # -------- Long running http-response: check the number of connections
    if cache:
        conn = cache.get(settings.HERBS_JSON_API_CONN_KEY_NAME)
        if conn is None:
            cache.set(settings.HERBS_JSON_API_CONN_KEY_NAME, 0, settings.HERBS_JSON_API_CONN_MAX_TIME)
        elif conn >= settings.HERBS_JSON_API_SIMULTANEOUS_CONN:
            context['errors'].append(_('Сервер занят. Повторите попытку позже.'))
            return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder),
                                content_type="application/json;charset=utf-8")
        else:
            cache.incr(settings.HERBS_JSON_API_CONN_KEY_NAME)
    no, no, no, objects_filtered, errors, warnings = get_data(request)
    authorship = request.GET.get('authorship', '')[:settings.HERBS_ALLOWED_AUTHORSHIP_SYMB_IN_GET]
    fieldid = request.GET.get('fieldid', '')[:settings.HERBS_ALLOWED_FIELDID_SYMB_IN_GET]
    itemcode = request.GET.get('itemcode', '')[:settings.HERBS_ALLOWED_ITEMCODE_SYMB_IN_GET]
    if authorship:
        objects_filtered = objects_filtered.filter(authorship__icontains=authorship)
    if fieldid:
        objects_filtered = objects_filtered.filter(fieldid__icontains=fieldid)
    if itemcode:
        objects_filtered = objects_filtered.filter(itemcode__icontains=itemcode)
    json_streamer = JSONStreamer()
    context['errors'].extend(errors)
    context['warnings'].extend(warnings)
    context.update({'data': json_generator(objects_filtered)})
    json_response = StreamingHttpResponse(json_streamer.iterencode(context),
                                          content_type="application/json;charset=utf-8")
    return json_response





@csrf_exempt
def show_herbs(request):
    '''
    Get herbitems view
    '''

    # TODO: Move this to get_data view
    if request.method == 'POST':
        return HttpResponse(_('Допустимы только GET-запросы'))

    if not request.is_ajax():
        return HttpResponse(_('Допустимы только XMLHttp-запросы'))

    paginated_data, page, num_pages, objects_filtered, errors, warnings = get_data(request)

    if request.GET.get('getcsv', None) and request.user.is_authenticated():
        writer = csv.writer(EchoData(), delimiter=';')
        csv_response = StreamingHttpResponse((writer.writerow([unicode(s).encode("utf-8") for s in row]) for row in _get_rows_for_csv(objects_filtered)), content_type="text/csv")
        csv_response['Content-Disposition'] = 'attachment; filename=herb_data_%s.csv' % timezone.now().strftime('%Y-%B-%d-%M-%s')
        return csv_response

    if paginated_data:
        data_tojson = []
        for item in paginated_data.object_list:
            data_tojson.append(
                {
                    'species': item.get_full_name(),
                    'itemcode': item.itemcode,
                    'id': item.pk,
                    'fieldid': item.fieldid,
                    'lat': item.coordinates.latitude if item.coordinates else 0.0,
                    'lon': item.coordinates.longitude if item.coordinates else 0.0,
                    'collectedby': item.collectedby,
                    'collected_s': item.collected_s,
                    'identifiedby': item.identifiedby,
                    'created': str(item.created),
                    'updated': str(item.updated)
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
        context.update({'curobj': hobj})
    except HerbItem.DoesNotExist:
        context.update({'error': _(u'Гербарного образца с id=%s не было найдено') % inum})
    result = render_to_string('herbitem_details.html', context,
                              context_instance=RequestContext(request))
    return HttpResponse(result)


@never_cache
def advice_select(request):
    if not request.is_ajax():
        return HttpResponse(_('Допустимы только XMLHttp запросы'))
    if request.method == 'POST':
        return HttpResponse(_('Допустимы только GET-методы'))

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
        context.update({'error': _('Странный запрос')})
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
        return HttpResponse(_('Ваш запрос слишком длинный, выберите меньшее количество элементов'))

    q = q.split(',')
    q = filter(lambda x: len(x) <= 15, q)

    if len(q) > 4:
        return HttpResponse(_('Вы не можете создать более 4-х этикеток одновременно'))


    # --------  Gathering data for labels ... --------
    q = map(lambda x: int(x), q)
    try:
       objs = HerbItem.objects.filter(public=True, id__in=q)
    except HerbItem.DoesNotExist:
       return HttpResponse(_('Выбранный образцы либо не опубликованы, либо не существуют'))
    if not objs.exists():
        return HttpResponse(_('Пустой или неправильно сформированный запрос'))
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


