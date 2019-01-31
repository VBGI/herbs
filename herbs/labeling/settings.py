#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fpdf
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

fpdf.set_global('FPDF_FONT_DIR', os.path.join(BASE_PATH, './fonts'))

BGI_LOGO_IMG = os.path.join(BASE_PATH, './imgs', 'bgi_logo.png')


# ----------- Common settings -----------------------
LABEL_WIDTH = 140
LABEL_HEIGHT = 100

FIRST_LINE = LABEL_HEIGHT/7
LINE_HEIGHT = LABEL_HEIGHT/16
LINE_SCALE = 0.85
PADDING_X = 3
PADDING_Y = 4
INTERSPACE = 1

LOGO_WIDTH = 15
LOGO_HEIGHT = 15

QR_SIZE = 28

TITLE_FONT_SIZE = 16
REGULAR_FONT_SIZE = 14
SMALL_FONT_SIZE = 12

DEFAULT_PAGE_WIDTH = 210.0
DEFAULT_PAGE_HEIGHT = 297.0

HERB_URL = 'http://botsad.ru/hitem/%s'
# ---------------------------------------------------

# --------- Superscript/subscript behavior ----------

SUPERSCRIPT_SHIFT = -0.6
SUBSCRIPT_SHIFT = 0.6
SUPERSCRIPT_FS = 0.8  # ratio of default font size
SUBSCRIPT_FS = 0.8

# --------- Species abbreviations -------------------
SPECIES_ABBR = 'sp.'

# ------------- Barcode settings --------------------
BARCODE_ITEM_HEIGHT = 10
BARCODE_ITEM_WIDTH = 1
BARCODE_FONTSIZE = 12
BARCODE_PAGE_WIDTH = DEFAULT_PAGE_HEIGHT
BARCODE_PAGE_HEIGHT = DEFAULT_PAGE_WIDTH
BARCODE_INITX = 10.0
BARCODE_INITY = 10.0
BARCODE_VSEP = 7.0
BARCODE_HSEP = 10.0
# ---------------------------------------------------


# ------------ Bryophyte label settings -------------
BRYOPHYTE_TOP_MARGIN = 10.0
BRYOPHYTE_LEFT_MARGIN = 45.0
BRYOPHYTE_MARGIN_EXTRA = 3.0
BRYOPHYTE_NOTE_FSIZE = 10
BRYOPHYTE_NOTENUM_FSIZE = 9
BRYOPHYTE_MIN_FSIZE = 5
BRYOPHYTE_LINE_LENGTH = 10
# ---------------------------------------------------

# -------------- Service field names ----------------
msgs = {'org':   'Herbarium',
        'descr': 'of the %s (%s)',
        'place': 'Place:',
        'coords': 'Coordinates:',
        'date': 'Date:',
        'col': 'Collector(s):',
        'det': 'Identifier(s):',
        'diden': 'Date Ident.:',
        'alt': 'Altitude, m. a.s.l.:',
        'country': 'Country:',
        'region': 'Region:'
        }