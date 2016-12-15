
from __future__ import print_function
from .countries import *
from ..models import Family, Genus, Species, Country
from ..utils import  create_safely

import gc
import time
import os


CDIR = os.path.dirname(os.path.abspath(__file__))


# --------------- Loading countries ----------------------
print('Loading counties... ')
for key in eng_codes:
    nru = [k for k,v in  codes.iteritems() if v == key][0]
    Country.objects.get_or_create(name_en=eng_codes[key], name_ru=nru)
gc.collect()
print('Countries were successfully loaded')
# --------------------------------------------------------


# ----------- Loading Families, Genera and Species -------
import pandas as pd
import os, subprocess


subprocess.call(['unzip', os.path.join(CDIR, 'species.zip'), '-d', CDIR])

for file in os.listdir(CDIR):
    if file.endswith(".csv"):
        data = pd.read_csv(os.path.join(CDIR, file), dtype=pd.np.object)
        for row in data.iterrows():
            genus = row[-1]['Genus'].lower().strip()
            family = row[-1]['Family'].lower().strip()
            species = row[-1]['Species'].lower().strip()
            authorship = row[-1]['Authorship']
            famobj = create_safely(Family, ('name',), (family,))
            genobj = create_safely(Genus, ('name','family__name'), (genus,family))
            spobj = create_safely(Species, ('name', 'genus__name', 'authorship'), (species, genus, authorship))
            time.sleep(0.001)
        gc.collect()
subprocess.call(['rm', os.path.join(CDIR, '*.csv')])

# ---------- All data was loaded successfully --------------
