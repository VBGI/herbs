 # -*- coding: utf-8 -*-
from __future__ import print_function

sys.path.append('/home/scidam/webapps/bgicms242/bgi')
os.environ['DJANGO_SETTINGS_MODULE']='bgi.settings'
from bgi.herbs.models import HerbItem, Additionals
import os
import datetime
from collections import OrderedDict
CDIR = os.path.dirname(os.path.abspath(__file__))
objects = HerbItem.objects.filter(latitude__gte=43.633782794186466,
                                  latitude__lte=44.54517028489244,
                                  longitude__lte=146.63062789080493
                                  longitude__gte=145.34228556295,
                                  collectedby__icontains='bakal',
                                  acronym__name='VBGI'
                                  )
print("Total number of objects", objects.count())

total = dict()
for obj in objects:
    name = obj.get_full_name()
    if name not in total:
        total[name] = list()
    total[name].append([(obj.latitude, obj.longitude),  obj.fieldid])
    
    for ad in Additionals.objects.filter(herbitem=obj):
        name = obj.get_full_name()
        if name not in total:
            total[name] = list()
        total[name].append([(obj.latitude, obj.longitude),  obj.fieldid])

total = OrderedDict(sorted(total.items(), key=lambda x: x[0]))    
for item in total:
    print(item, ";", total[item])
