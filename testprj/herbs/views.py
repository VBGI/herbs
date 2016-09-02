# -*- coding: utf-8 -*-
import operator
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms.models import model_to_dict
  
from .models import Family, Genus, HerbItem, Species
from .countries import codes as contry_codes
from .forms import SearchForm
from .conf import settings
from django.utils.text import capfirst

from django.template.loader import render_to_string

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json

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


@csrf_exempt
def show_herbs(request):
    '''
    Answer on queries for herbitems
    '''
    if request.method == 'POST':
        return HttpResponse('Only GET-methods are acceptable')    

    context = {'error': '', 'has_pervious': None, 'has_next': None,
               'pagenumber': 1, 'pagecount': 0}

    if request.is_ajax():
        dataform = SearchForm(request.GET)
        if dataform.is_valid():
            data = {key: dataform.cleaned_data[key] for key in dataform.fields}
            bigquery = []
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
            if data['colstart']:
                try:
                    stdate = parse_date(datap['colstart']).date()
                except ValueError:
                    stdate = None
            else:
                stdate = None
            if data['colend']:
                try:
                    endate = parse_date(datap['ValueError']).date()
                except ValueError:
                    endate = None
            else:
                endate = None
                
            bigquery += [Q(colstart__gt=stdate)] if stdate else []
            bigquery += [Q(colstart__lt=endate)] if endate else []

            if not bigquery:
                object_filtered = HerbItem.objects.all()
            else:
                object_filtered = HerbItem.objects.filter(reduce(operator.and_, bigquery))
            
            if not object_filtered.exists():
                context.update({'herbobjs' : [],
                                'total': 0,
                                'error': 'Не одного элемента не удолетворяет условиям запроса'})
                return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")
            # ------- Sorting items --------------
            # sorting isn't implemented yet
            # -----  
            
            # ---------  pagination-----------------
            pagcount = request.POST.get('pagcount', '')
            page = request.POST.get('page', '1')
            
            pagcount = int(pagcount) if pagcount.isdigit() else settings.HERBS_PAGINATION_COUNT
            page = int(page) if page.isdigit() else 1
            
            paginator = Paginator(object_filtered, pag_count)
            
            try:
                obj_to_show = paginator.page(page)
            except:
                obj_to_show = paginator.page(1)
            
            context.update({'herbobjs' : map(lambda x: model_to_dict(x), obj_to_show),
                            'has_pervious': obj_to_show.has_pervious(),
                            'has_next': obj_to_show.has_next(),
                            'pagenumber': page,
                            'pagecount': paginator.num_pages,
                            'total': object_filtered.count(),
                            })

            return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")
        else: 
            context.update({'herbobjs' : [],
                                'total': 0,
                                'error': 'Ошибка в форме поиска'})
            return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")
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
                data = [{'id': ind + 2, 'text': item} for ind,item in enumerate(tostore)]
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
            data = [{'id': item.pk, 'text': item.get_full_name()}\
                    for item in objects[:settings.HERBS_AUTOSUGGEST_NUM_TO_SHOW]]
        elif cfield == 'country':
            data = [{'id': ind + 2,'text': val} for ind, val in enumerate(filter(lambda x: query in x, countries))]
    else:
        # invalid form (That isn't possible,  I hope! )
        context.update({'error': 'Странный запрос'})
        data = []
    if data:
        for item in data: item['text'] = capfirst(item['text'])
        
    context.update({'items': data})
    return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")
