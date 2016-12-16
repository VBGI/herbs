
from __future__ import print_function

import os, subprocess


CDIR = os.path.dirname(os.path.abspath(__file__))

subprocess.call(['python', os.path.join(CDIR, 'loadcountries.py')])

subprocess.call(['unzip', os.path.join(CDIR, 'species.zip'), '-d', CDIR])

for file in os.listdir(CDIR):
    if file.endswith(".csv"):
        subprocess.call(['python', os.path.join(CDIR, 'evalfile.py'), os.path.basename(file)])



subprocess.call(['rm', os.path.join(CDIR, '*.csv')])

# ---------- All data was loaded successfully --------------
