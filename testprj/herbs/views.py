# -*- coding: utf-8 -*-
import operator
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms.models import model_to_dict
 
 
from .models import Family, Genus, HerbItem
from .forms import SearchForm

from django.template.loader import render_to_string

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json


HERB_PAGINATION_COUNT = 100

@csrf_exempt
def get_item_data(request):
    '''Get herbitem as a json object '''
    context = {'error': ''}
    objid = request.GET.get('id', '')
    if objid:
        try:
            hobj = HerbItem.objects.get(id=objid)
            tojson = model_to_dict(hobj)
            context.update(tojson)
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
            bigquery += [Q(colstart__gt=data['colstart'])] if data['colstart'] else []
            bigquery += [Q(colstart__lt=data['colend'])] if data['colstart'] else []

            object_filtered = HerbItem.objects.filter(reduce(operator.and_, biquery))
            
            # ------- Sorting items --------------
            
            # pagination
            pag_count = request.POST.get('pag',str(HERB_PAGINATION_COUNT))
            page = request.POST.get('page','1')
            
        else: 
            #Form is invalid, that isn't possible; 
            pass
        
        if family:
            object_filtered = object_filtered.filter(family__name__icontains=family)

        if genus:
            object_filtered = object_filtered.filter(genus__name__icontains=genus)
        
        if species:
            object_filtered = object_filtered.filter(species__name__icontains=species)

        if gcode:
            object_filtered = object_filtered.filter(gcode=gcode)
        if itemcode:
            object_filtered = object_filtered.filter(itemcode=itemcode)        
        
        # Form a herbs list according to request
        pass
    else:
        # Request isn't ajax
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
        cfield = request.GET.get('cfield', 'species')
        if cfield not in dataform.fields:
            cfield = 'species'
        query = requiest.GET.get('query', '')
        if not query:
            data = []
            return HttpResponse(json.dumps({'items': data}),
                                content_type="application/json;charset=utf-8")
        if cfield == 'itemcode':
            objects = HerbItem.objects.filter(itemcode__contains=query)
            data = [{'id': item.pk, 'text': item.itemcode} for item in objects.iterator()]
        elif cfield == 'family':
            objects = Family.objects.filter(name__icontains=query)
            data = [{'id': item.pk, 'text': item.name} for item in objects.iterator()]
        elif cfield == 'genus':
            if dataform.cleaned_data['family']:
                objects = HerbItem.objects.filter(family__name__iexact=dataform.cleaned_data['family'],
                                                  genus__name__icontains=query)
                data = [{'id': item.genus.pk, 'text': item.genus.name} for item in objects.iterator()]
            else:
                objects = Genus.objects.filter(name__icontains=query)
                data = [{'id': item.pk, 'text': item.name} for item in objects.iterator()]
        elif cfield == 'species':
            if dataform.cleaned_data['family'] and dataform.cleaned_data['genus']:
                objects = HerbItem.objects.filter(family__name__iexact=dataform.cleaned_data['family'],
                                                  genus__name__iexact=dataform.cleaned_data['genus'],
                                                  species__name__icontains=query)
            elif dataform.cleaned_data['family'] and not dataform.cleaned_data['genus']:
                objects = HerbItem.objects.filter(family__name__iexact=dataform.cleaned_data['family'],
                                                  species__name__icontains=query)
            elif not dataform.cleaned_data['family'] and dataform.cleaned_data['genus']:
                objects = HerbItem.objects.filter(genus__name__iexact=dataform.cleaned_data['genus'],
                                                  species__name__icontains=query)
            elif not dataform.cleaned_data['family'] and not dataform.cleaned_data['genus']:
                objects = HerbItem.objects.filter(species__name__icontains=query)
            data = [{'id': item.species.pk, 'text': item.get_full_name(), 'text-final': item.species.name} for item in objects.iterator()]

    else:
        # invalid form (That isn't possible,  I hope! )
        context.update({'error': 'Странный запрос'})
        data = []
    context.update({'items': data})
    return HttpResponse(json.dumps(context), content_type="application/json;charset=utf-8")
