
from __future__ import print_function
from .countries import *
from ..models import Family, Genus, Species, Country
import gc
import time

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
        data = pd.read_csv(file, dtype=pd.np.object)
        for row in data.iterrows():
            genus = row[-1]['Genus']
            family = row[-1]['Family']
            species = row[-1]['Species']
            authorship = row[-1]['Authorship']
            famobj = Family.objects.get_or_create(name=family.lower().strip())
            genobj = Genus.objects.get_or_create(family=famobj,
                                                 name=genus.lower().strip())
            spobj = Species.objects.get_or_create(genus=genobj,
                                                  name=species.lower().strip(),
                                                  authorship=authorship)
            time.sleep(0.001)
        gc.collect()
subprocess.call(['rm', os.path.join(CDIR, '*.csv')])

# ---------- All data was loaded successfully --------------


