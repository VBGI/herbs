# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms.models import model_to_dict
 
 
from .models import Family, Genus, HerbItem
from .forms import SearchForm, ExtendedSearchForm

from django.template.loader import render_to_string

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def get_item_data(request):
    context = {'error': ''}
    objid = request.GET.get('id', '')
    if objid:
        try:
            hobj = HerbItem.objects.get(id=objid)
            tojson = model_to_dict(hobj)
            context.update(tojson)
        except HerbItem.DoesNotExists:
            context = {'error': u'Объект не найден'}
    return  HttpResponse(json.dumps(context), content_type="application/json") 



def showherbs(request):
    '''
    Answer on quries about herbs
    '''
    if request.is_ajax():
        
        # basic search components
        family = request.POST.get('family', '')
        genus = request.POST.get('genus', '')
        species = request.POST.get('species', '')
        gcode = request.POST.get('gcode', '')  # Search by internal code (assigned by this system)
        collectors = request.POST.get('collectors', '')
        country = request.POST.get('country', '')
        region = request.POST.get('region', '')

        object_filtered = HerbItem.objects.all()
            
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
        pass



# ----- Copied from plantsets application
@never_cache
def advice_mixin(request,qclass=PlantFamily):
    if not request.is_ajax():
        return HttpResponse(json.dumps(''), content_type="application/json;charset=utf-8")
    query = request.POST.get('q','')
    if qclass == CollectionObject:
        objects = qclass.objects.filter(Q(latin_name__icontains=query)|Q(common_name_ru__icontains=query)|Q(common_name_en__icontains=query)).order_by('latin_name')
    else:
        objects = qclass.objects.filter(Q(latin_name__icontains=query)|Q(name_ru__icontains=query)|Q(name_en__icontains=query)).order_by('latin_name')
    data = []
    _data = []
    for item in objects.iterator():
        _data.append(item.latin_name)
    _data = sorted(list(set(_data)))
    for ind,val in enumerate(_data):
        data.append({"id": random.randint(1,10**8), "text": val})
    return HttpResponse(json.dumps({'items':data}), content_type="application/json;charset=utf-8")

 

