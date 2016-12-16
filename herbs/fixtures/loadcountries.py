from __future__ import print_function

import sys, os

sys.path.append('/home/scidam/webapps/bgitest/bgi')
os.environ['DJANGO_SETTINGS_MODULE']='bgi.settings'

from .countries import *
from ..models import Country


CDIR = os.path.dirname(os.path.abspath(__file__))


# --------------- Loading countries ----------------------
print('Loading counties... ')
for key in eng_codes:
    nru = [k for k,v in  codes.iteritems() if v == key][0]
    Country.objects.get_or_create(name_en=eng_codes[key], name_ru=nru)
print('Countries were successfully loaded')
# --------------------------------------------------------


