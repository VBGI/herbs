 # -*- coding: utf-8 -*-
from __future__ import print_function
import sys, os

sys.path.append('/home/scidam/webapps/bgicms242/bgi')
os.environ['DJANGO_SETTINGS_MODULE']='bgi.settings'

from .countries import *
from ..models import Family, Genus, Species, Country
from ..utils import  create_safely
import pandas as pd
import os


CDIR = os.path.dirname(os.path.abspath(__file__))

def evalfile(afile):
    data = pd.read_csv(os.path.join(CDIR, afile), dtype=pd.np.object)
    print('Evaluating file %s' % afile)
    for row in data.iterrows():
        genus = row[-1]['Genus'].lower().strip()
        family = row[-1]['Family'].lower().strip()
        species = row[-1]['Species'].lower().strip()
        authorship = row[-1]['Authorship']
        famobj = create_safely(Family, ('name',), (family,))
        genobj = create_safely(Genus, ('name','family'), (genus,famobj), postamble='')
        spobj = create_safely(Species, ('name', 'genus', 'authorship'), (species, genobj, authorship), postamble='')

afile = sys.argv[1]
evalfile(afile)
