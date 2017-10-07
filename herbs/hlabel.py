#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fpdf
import tempfile
import qrcode
import os
from .utils import translit, smartify_language


msgs = {'org':   'Herbarium',
        'descr': 'of the %s (%s)',
        'place': 'Place:',
        'coords': 'Coordinates:',
        'date': 'Date:',
        'col': 'Collector(s):',
        'det': 'Identifier(s):',
        'diden': 'Date Ident.:',
        'alt': 'Altitude:',
        'country': 'Country:',
        'region': 'Region:'
        }


FPDF = fpdf.FPDF

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

fpdf.set_global('FPDF_FONT_DIR', os.path.join(BASE_PATH, './fonts'))

BGI_LOGO_IMG = os.path.join(BASE_PATH, './imgs', 'bgi_logo.png')


# ----------- Common settings -----------------------
# TODO:
# Settings should be moved to conf-file
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
BRYOPHYTE_LINE_LENGTH = 10
# ---------------------------------------------------


def insert_qr(pdf, x, y, code='1234567', lw=LABEL_WIDTH, lh=LABEL_HEIGHT):
    if len(code) > 8:
        return
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(HERB_URL % code)
    qr.make(fit=True)
    img = qr.make_image()
    temp_name = os.path.join(BASE_PATH, './tmp',
                             next(tempfile._get_candidate_names()))
    temp_name += '.png'
    try:
        with open(temp_name, 'w') as tmpfile:
            img.save(tmpfile)
            tmpfile.flush()
            pdf.set_xy(x + lw - QR_SIZE - 2, y + lh - QR_SIZE - 4)
            pdf.image(temp_name, w=QR_SIZE, h=QR_SIZE)
    finally:
        try:
            os.remove(temp_name)
        except IOError:
            pass


class PDF_MIXIN(object):
    def __init__(self, orientation='L'):
        self.pdf = FPDF(orientation=orientation)
        self.pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)
        self.pdf.add_font('DejaVub', '', 'DejaVuSans-Bold.ttf', uni=True)
        self.pdf.add_font('Dejavubi', '', 'DejaVuSans-BoldOblique.ttf', uni=True)
        self.pdf.set_margins(5, 5, 5)
        self.pdf.set_auto_page_break(0, 0)
        self.pdf.add_page()
        self._ln = 0
        self.lnhght = LINE_HEIGHT

    def goto(self, y, n, inter=0):
        return y + PADDING_Y + (self.lnhght + INTERSPACE) * n + inter

    def get_pdf(self):
        return self.pdf.output(dest='S')

    def create_file(self, fname):
        self.pdf.output(fname, dest='F')


class PDF_DOC(PDF_MIXIN):

    def _add_label(self, x, y, family='', species='', spauth='',
                   coldate='', latitude='', longitude='',
                   place='', country='', region='', collected='',
                   altitude='', identified='', number='', itemid='', fieldid='',
                   acronym='', institute='', address='', gform='', addspecies='',
                   district='', note='', short_note='', gpsbased='',
                   dethistory='', infra_rank='', infra_epithet='', logo_path=''):
        self.pdf.rect(x, y, LABEL_WIDTH, LABEL_HEIGHT, '')
        self.pdf.set_xy(x + PADDING_X, y + PADDING_Y)
        self.pdf.image(logo_path or BGI_LOGO_IMG, w=LOGO_WIDTH, h=LOGO_HEIGHT)

        self.pdf.set_font('DejaVu', '', TITLE_FONT_SIZE + 2)
        self.pdf.set_xy(x + PADDING_X + LOGO_WIDTH, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - LOGO_WIDTH-2 * PADDING_X, 0, msgs['org'],
                      align='C')
        self.pdf.set_font_size(REGULAR_FONT_SIZE)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X + LOGO_WIDTH, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - LOGO_WIDTH - 2 * PADDING_X, 0,
                      msgs['descr'] % (institute, acronym),
                      align='C')
        self.pdf.set_font_size(SMALL_FONT_SIZE)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X + LOGO_WIDTH, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - LOGO_WIDTH - 2 * PADDING_X, 0, address,
                      align='C')
        self.pdf.line(x + PADDING_X, self.goto(y, 2) + 4,
                      x + LABEL_WIDTH - PADDING_X, self.goto(y, 2) + 4)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln) + 1)
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        if family:
            self.pdf.cell(LABEL_WIDTH - 2 * PADDING_X, 0, family,
                          align='C')
        else:
            self.pdf.cell(LABEL_WIDTH - 2 * PADDING_X, 0, ' ' * 20,
                          align='C')

        self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
        if gform:
            self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln) + 1)
            if gform == 'G':
                self.pdf.cell(0, 0, 'Growth form')
            elif gform == 'D':
                self.pdf.cell(0, 0, 'Dev.stage partly')
        # TODO: species name fixes needed: infraspecific rank supporting

        # -------------- Plot Species name ------------
        self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
        self._ln += 1
        author_name = spauth if spauth else ''
        sp_w = self.pdf.get_string_width(species)
        self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
        au_w = self.pdf.get_string_width(author_name)
        x_pos = LABEL_WIDTH / 2 - (au_w + sp_w + 2) / 2
        if not infra_rank:
            scaled = False
            if x_pos > PADDING_X:
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, species)
                self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
                self.pdf.set_xy(x + x_pos + sp_w + 2, self.goto(y, self._ln))
                self.pdf.cell(0, 0, author_name)
            else:
                x_pos = LABEL_WIDTH / 2 - sp_w / 2
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, species)
                self._ln += 1
                x_pos = LABEL_WIDTH / 2 - au_w / 2
                self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.cell(0, 0, author_name)
                self.lnhght *= LINE_SCALE
                self._ln += 1
                scaled = True
        else:
            self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
            epw = self.pdf.get_string_width(infra_epithet)
            rw = self.pdf.get_string_width(infra_rank)
            x_pos = LABEL_WIDTH / 2 - (au_w + sp_w +rw + epw + 2) / 2
            scaled = False
            if x_pos > PADDING_X:
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, species)

                x_pos += sp_w + 1
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, infra_rank)

                x_pos += rw
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, infra_epithet)

                x_pos += epw + 1
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, author_name)
            else:
                x_pos = LABEL_WIDTH / 2 - sp_w / 2
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
                self.pdf.cell(0, 0, species)
                self._ln += 1
                x_pos = LABEL_WIDTH  - au_w - self.pdf.get_string_width(infra_rank + ' ' + infra_epithet)
                x_pos /= 2.0
                self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.cell(0, 0, infra_rank)

                self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
                x_pos += rw + 1
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.cell(0, 0, infra_epithet)

                x_pos += epw + 1
                self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
                self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
                self.pdf.cell(0, 0, author_name)

                scaled = True
        # ----------------------------------------------

        # ------------- place of collecting ------------
        if not country:
            country = ''
        country = smartify_language(country, lang='en')
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        tw = self.pdf.get_string_width(msgs['country'])
        self.pdf.cell(0, 0, msgs['country'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        cw = self.pdf.get_string_width(country)
        self.pdf.cell(0, 0, country)

        if region:
            region = translit(smartify_language(region, lang='en'), 'ru',
                              reversed=True)
            self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
            rw = self.pdf.get_string_width(msgs['region'])
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
            rtw = self.pdf.get_string_width(region)
            if PADDING_X + 4 + tw + cw + rw + rtw < LABEL_WIDTH:
                self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                self.pdf.set_xy(x + PADDING_X + 4 + tw + cw,
                                self.goto(y, self._ln))
                self.pdf.cell(0, 0, msgs['region'])
                self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                self.pdf.set_xy(x + PADDING_X + 5 + tw + cw + rw,
                                self.goto(y, self._ln))
                self.pdf.cell(0, 0, region)

        prepare = []
        if place:
            place = smartify_language(place, lang='en')
            self._ln += 1
            self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
            tw = self.pdf.get_string_width(msgs['place'])
            self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
            self.pdf.cell(0, 0, msgs['place'])
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
            cline = []
            ss = PADDING_X + 1 + tw
            for item in place.split():
                ss += self.pdf.get_string_width(item + ' ')
                if ss < LABEL_WIDTH - 2 * PADDING_X:
                    cline.append(item)
                else:
                    prepare.append(' '.join(cline))
                    cline = [item]
                    ss = PADDING_X + self.pdf.get_string_width(item + ' ')
            if cline:
                prepare.append(' '.join(cline))
            self.pdf.set_xy(x + PADDING_X + 2 + tw, self.goto(y, self._ln))
            self.pdf.cell(0, 0, prepare[0])
            if len(prepare) > 3:
                self.lnhght *= LINE_SCALE**2
                self._ln += 2 if not scaled else 2.5
            elif len(prepare) == 3:
                self.lnhght *= LINE_SCALE
                self._ln += 1
            for line in prepare[1:4]:
                self._ln += 1
                self.pdf.set_xy(x + PADDING_X + 2, self.goto(y, self._ln))
                self.pdf.cell(0, 0, line)

        # ----------------------------------------------

        # ------------- Altitude info ------------------
        self._ln += 1
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        tw = self.pdf.get_string_width(msgs['alt'])
        self.pdf.cell(0, 0, msgs['alt'])
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.cell(0, 0, translit(smartify_language(altitude, lang='en'),
                                     'ru', reversed=True))

        # ------------- Coordinates found -------------
        self._ln += 1
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        tw = self.pdf.get_string_width(msgs['coords'])
        self.pdf.cell(0, 0, msgs['coords'])
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        if latitude and longitude:
            self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
            self.pdf.cell(0, 0, 'LAT=' + str(latitude) + u'\N{DEGREE SIGN},' +
                          ' LON=' + str(longitude) + u'\N{DEGREE SIGN}')
        # ----------------------------------------------

        # ----------- Date found -----------------------
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.cell(0, 0, msgs['date'])
        tw = self.pdf.get_string_width(msgs['date'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        self.pdf.cell(0, 0, coldate)
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        # -------------- Collectors --------------------
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        self.pdf.cell(0, 0, msgs['col'])
        tw = self.pdf.get_string_width(msgs['col'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        ss = 0
        fline = []
        collected = translit(collected, 'ru', reversed=True)
        for k in collected.split():
            ss += self.pdf.get_string_width(k + ' ')
            if ss < (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE):
                fline.append(k)
            if ss >= (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE):
                break
        if fline:
            fline = ' '.join(fline).strip()
            if fline[-1] == ',':
                fline = fline[:-1]
            self.pdf.cell(0, 0, fline)
        # ----------------------------------------------

        # --------------- Identified by ----------------
        identified = translit(identified, 'ru', reversed=True)
        self._ln += 1
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        self.pdf.cell(0, 0, msgs['det'])
        tw = self.pdf.get_string_width(msgs['det'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        ss = 0
        fline = []
        for k in identified.split():
            ss += self.pdf.get_string_width(k + ' ')
            if ss < (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE):
                fline.append(k)
            if ss >= (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE):
                break
        if fline:
            fline = ' '.join(fline).strip()
            if fline[-1] == ',':
                fline = fline[:-1]
            self.pdf.cell(0, 0, fline)
        # ----------------------------------------------

        # -----------------------------------------------

        # Extra info (to get without qr reader ----------
        self.pdf.set_font_size(SMALL_FONT_SIZE-4)
        tw = self.pdf.get_string_width(HERB_URL % itemid)
        self.pdf.set_xy(x + LABEL_WIDTH - PADDING_X - tw, y + LABEL_HEIGHT - 2)
        self.pdf.cell(0, 0, HERB_URL % itemid)

        # ----------------------------------------------

        # ------------ Catalogue number ----------------
        dfs = TITLE_FONT_SIZE + 2
        idtoprint = 'ID: %s/%s' % (number, itemid)
        if fieldid:
            idtoprint += '/%s' % fieldid
        self.pdf.set_font_size(dfs)
        cl = self.pdf.get_string_width(idtoprint)
        allowed_width = LABEL_WIDTH - 3 * PADDING_X - tw - 3
        while cl > allowed_width:
            dfs -= 2
            self.pdf.set_font_size(dfs)
            cl = self.pdf.get_string_width(idtoprint)
        self.pdf.set_xy(x + 2 * PADDING_X, y + LABEL_HEIGHT - PADDING_Y)
        self.pdf.cell(0, 0, idtoprint)

        # ----------------------------------------------

        # --------- qr insertion -----------------------
        insert_qr(self.pdf, x, y, code=itemid)

        # ----------------------------------------------

    def make_label(self, x, y, **kwargs):
        self._ln = 0
        self.lnhght = LINE_HEIGHT
        self._add_label(x, y, **kwargs)

    def tile_less4_labels(self, l_labels):
        x = self.pdf.get_x()
        y = self.pdf.get_y()
        if len(l_labels) == 1:
            self.make_label(x, y, **l_labels[0])
        elif len(l_labels) == 2:
            self.make_label(x, y, **l_labels[0])
            self.make_label(x + LABEL_WIDTH + 2, y, **l_labels[1])
        elif len(l_labels) == 3:
            self.make_label(x, y, **l_labels[0])
            self.make_label(x + LABEL_WIDTH + 2, y, **l_labels[1])
            self.make_label(x, y + LABEL_HEIGHT + 1, **l_labels[2])
        elif len(l_labels) == 4:
            self.make_label(x, y, **l_labels[0])
            self.make_label(x + LABEL_WIDTH + 2, y, **l_labels[1])
            self.make_label(x, y + LABEL_HEIGHT + 1, **l_labels[2])
            self.make_label(x + LABEL_WIDTH + 2, y + LABEL_HEIGHT + 1,
                            **l_labels[3])

    def tile_labels(self, l_labels):
        def chunks(l, n=4):
            for i in range(0, len(l), n):
                yield l[i:i + n]
        lset = list(chunks(l_labels))
        for labels in lset:
            self.tile_less4_labels(labels)
            if labels != lset[-1]:
                self.pdf.add_page()


    def _test_page(self):
        testdict = {'family': 'AWESOMEFAMILY', 'species': 'Some species',
                    'spauth': '(Somebody) Author',
                    'date': '12 Nov 2002',
                    'latitude': '12.1231',
                    'longitude': '123.212312',
                    'region': u'Приморский край',
                    'altitude': '123 m o.s.l',
                    'country': u'Россия',
                    'place': u'Никому неизвестное село глубоко в лесу; На горе росли цветы небывалой красоты, мы собрали их в дождливую погоду и было очень прохладно',
                    'collected': u'Один М.С., Другой Б.В., Третий А.А., Четвертый Б.Б., Пятый И.И., Шестой В.В., Седьмой',
                    'identified': u'Один, Другой',
                    'number': '17823781', 'itemid': '12312', 'fieldid': '123456789asdfghj',
                    'acronym': 'VBGI',
                    'institute': 'Botanical Garden-Institute FEB RAS',
                    'address': '690018, Russia, Vladivosotk, Makovskogo st. 142',
                    'gform': 'G', 'addspecies':'', 'short_note': '', 'gpsbased': '',
                    'dethistory': ''}
        llabels = [testdict] * 4
        self.tile_labels(llabels)


class BARCODE(PDF_MIXIN):

    def put_barcode(self, acronym, id, institute,  x, y):
        fs = BARCODE_FONTSIZE
        code = str(acronym).upper() + str(id)
        self.pdf.code39(code, x, y, w=BARCODE_ITEM_WIDTH, h=BARCODE_ITEM_HEIGHT)
        barcodesize = 5.0 * BARCODE_ITEM_WIDTH * len(code)
        self.pdf.set_font('DejaVu', '', fs)
        cw = self.pdf.get_string_width(code)
        self.pdf.set_xy(x + barcodesize / 2.0 - cw / 2.0, y + BARCODE_ITEM_HEIGHT + 3)
        self.pdf.cell(0, 0, code)
        fs -= 1
        self.pdf.set_font('DejaVu', '', fs)
        cw = self.pdf.get_string_width(institute)
        while cw > barcodesize:
            self.pdf.set_font('DejaVu', '', fs)
            cw = self.pdf.get_string_width(institute)
            fs -= 1
        if fs < 10.0:
            tau = 1
        else:
            tau = 2
        self.pdf.set_font('DejaVu', '', fs)
        cw = self.pdf.get_string_width(institute)
        self.pdf.set_xy(x + barcodesize / 2.0 - cw / 2.0, y - tau)
        self.pdf.cell(0, 0, institute)

    def spread_codes(self, codes):
        vsep = BARCODE_VSEP
        hsep = BARCODE_HSEP
        _x, _y = BARCODE_INITX, BARCODE_INITY
        for code in codes:
            code_string = str(code['acronym']).upper() + str(code['id'])
            barwidth = 5.0 * BARCODE_ITEM_WIDTH * len(code_string)
            barheight = BARCODE_ITEM_HEIGHT + 5
            if (_x + barwidth + hsep < BARCODE_PAGE_WIDTH):
                if (_y + barheight + vsep < BARCODE_PAGE_HEIGHT):
                    self.put_barcode(code['acronym'], code['id'], code['institute'], _x, _y)
                    _x += barwidth + hsep
                else:
                    self.pdf.add_page()
                    _x, _y = BARCODE_INITX, BARCODE_INITY
                    self.put_barcode(code['acronym'], code['id'], code['institute'], _x, _y)
                    _x += barwidth + hsep
            else:
                _x = BARCODE_INITX
                _y += barheight + vsep
                if (_y + barheight + vsep < BARCODE_PAGE_HEIGHT):
                    self.put_barcode(code['acronym'], code['id'], code['institute'], _x, _y)
                    _x += barwidth + hsep
                else:
                    self.pdf.add_page()
                    _x, _y = BARCODE_INITX, BARCODE_INITY
                    self.put_barcode(code['acronym'], code['id'], code['institute'], _x, _y)
                    _x += barwidth + hsep


class PDF_BRYOPHYTE(BARCODE):

    def __init__(self):
        super(PDF_BRYOPHYTE, self).__init__(orientation='P')

    def goto(self, y, n, inter=0, line_height=5):
        return y + BRYOPHYTE_TOP_MARGIN + line_height * n + inter

    def generate_label(self, allspecies=[],
                       coldate='', latitude='', longitude='',
                       place='', country='', region='', collected='',
                       altitude='', identified='', number='', itemid='',
                       fieldid='', acronym='', institute='', note='',
                       district='', gpsbased='', dethistory=[]):
        # -----  Insert qr-code in the center of the page ------
        insert_qr(self.pdf, DEFAULT_PAGE_WIDTH / 2.0 + QR_SIZE / 2.0,
                  DEFAULT_PAGE_HEIGHT / 2.0, code=itemid, lh=0, lw=0)
        # insert helper url
        self.pdf.set_font('DejaVu', '', REGULAR_FONT_SIZE)
        self.pdf.set_font_size(SMALL_FONT_SIZE - 4)
        urlw = self.pdf.get_string_width(HERB_URL % itemid)
        self.pdf.set_xy(DEFAULT_PAGE_WIDTH / 2.0 - urlw / 2 - 2,
                        DEFAULT_PAGE_HEIGHT / 2.0)
        self.pdf.cell(0, 0, HERB_URL % itemid)
        self._ln = 0

        if fieldid:
            field_string = 'Field id: %s' % fieldid
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE - 2)
            fsw = self.pdf.get_string_width(field_string)
            self.pdf.set_xy(DEFAULT_PAGE_WIDTH - BRYOPHYTE_LEFT_MARGIN - fsw,
                            self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                      self._ln - 1))
            self.pdf.cell(0, 0, field_string)

        addinfo = []
        addind = 1
        mainind = 0
        for sp, auth, ir, iep, _note in allspecies:
            mainind += 1
            self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                            self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                            self._ln))
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
            spaw = self.pdf.get_string_width(auth)
            self.pdf.set_font('DejaVubi', '', SMALL_FONT_SIZE)
            spw = self.pdf.get_string_width(sp)
            self.pdf.cell(0, 0, sp)
            if ir:
                irw = self.pdf.get_string_width(ir)
                iepw = self.pdf.get_string_width(iep)
                if spw + 2 + irw > DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN:
                    self._ln += 1
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, ir)

                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + irw + 4 + iepw,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, auth)

                    self.pdf.set_font('DejaVubi', '', SMALL_FONT_SIZE)
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + irw + 2,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.cell(0,0, iep)
                    cur_cell_width = irw + 4 + iepw + spaw
                elif spw + 2 + irw + iepw > DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN:
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, ir)
                    self._ln += 1
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVubi', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, iep)

                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + iepw + 2,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, auth)
                    cur_cell_width = spaw + iepw + 2
                elif spaw + spw + 2 + irw + iepw > DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN:
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, ir)
                    self.pdf.set_font('DejaVubi', '', SMALL_FONT_SIZE)
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2 + 2 + irw,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.cell(0, 0, iep)
                    self._ln += 1
                    self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.cell(0, 0, auth)
                    cur_cell_width = spaw
                else:
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, ir)
                    self.pdf.set_font('DejaVubi', '', SMALL_FONT_SIZE)
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2 + 2 + irw,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.cell(0, 0, iep)
                    self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 6 + irw +iepw,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                    self._ln))
                    self.pdf.cell(0, 0, auth)
                    cur_cell_width = spw + 6 + irw +iepw + spaw
            else:
                self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                            self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0, self._ln))
                fline = []
                sline = []
                if spaw + spw + 2 > DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN:
                    for word in auth.split():
                        if self.pdf.get_string_width(' '.join(fline + [word])) + spw + 2 <= DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN:
                            fline.append(word)
                        else:
                            sline.append(word)
                else:
                    fline = auth.split()
                self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                self.pdf.cell(0, 0, ' '.join(fline))
                cur_cell_width = spw + 2 + self.pdf.get_string_width(' '.join(fline))
                if sline:
                    self._ln += 1
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                    self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0,
                                              self._ln))
                    self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                    self.pdf.cell(0, 0, ' '.join(sline))
                    cur_cell_width = self.pdf.get_string_width(' '.join(sline))

            if _note or (dethistory and mainind == 1):
                self.pdf.set_font('DejaVu', '', BRYOPHYTE_NOTENUM_FSIZE)
                _y = self.pdf.get_y()
                _x = self.pdf.get_x()
                self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + cur_cell_width + 1,
                                _y - 1)
                self.pdf.cell(0, 0, '(' + str(addind) + ')')
                if dethistory and mainind == 1:
                    _note = _note.strip()
                    if _note:
                        if _note[-1] in [';', '.', ',']:
                            _note = _note[:-1]
                        _note += '; '
                    histlines = []
                    for hist_item in dethistory:
                        histline = translit(hist_item['identifiedby'], 'ru', reversed=True) + ': '
                        if hist_item['identified']:
                            histline += '(' + hist_item['identified'] + ') '
                        histline += hist_item['species']['species'] +\
                                    (' ' + hist_item['species']['infra_rank'] if hist_item['species']['infra_rank'] else '') +\
                                    (' ' + hist_item['species']['infra_epithet'] if hist_item['species']['infra_epithet'] else '') +\
                                    ' ' + hist_item['species']['spauth']
                        histlines.append(histline)
                    _note += '; '.join(histlines)
                addinfo.append([addind, _note.strip()])
                addind += 1
                self.pdf.set_xy(_x, _y)
            self._ln += 1

        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                        self.goto(DEFAULT_PAGE_HEIGHT * 2.0 / 3.0, self._ln))

        if collected:
            leg_info = 'Leg. ' + translit(collected, 'ru', reversed=True)
        else:
            leg_info = ''

        if coldate:
            leg_info += ' (%s);' % coldate

        latlon_info = ''

        if latitude:
            if float(latitude) >= 0.0:
                latlon_info += 'Lat.: %s' % latitude + u'\N{DEGREE SIGN}N;'
            else:
                latlon_info += 'Lat.: {0: .5f}'.format(abs(float(latitude))) + u'\N{DEGREE SIGN}S;'

        if longitude:
            if float(longitude) >= 0.0:
                latlon_info += ' Lon.: %s' % longitude + u'\N{DEGREE SIGN}E;'
            else:
                latlon_info += ' Lon.: {0: .5f}'.format(abs(float(longitude))) + u'\N{DEGREE SIGN}W;'

        if altitude:
            latlon_info += ' Alt.: %s m a.s.l.;' % translit(altitude, 'ru', reversed=True)

        if (latitude or longitude or altitude) and gpsbased:
            latlon_info += ' [GPS-based];'

        if identified:
            det_info = 'Det. ' + translit(identified, 'ru', reversed=True)
        else:
            det_info = ''

        self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
        self.pdf.set_font('DejaVubi', '', SMALL_FONT_SIZE)
        self.pdf.multi_cell(DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN,
                            5, smartify_language(country, lang='en'))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)



        pos_info = '; '.join([x.strip() for x in [smartify_language(region, lang='en'),
                                           smartify_language(district, lang='en'),
                                           latlon_info] if x])

        self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA)
        self.pdf.multi_cell(DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN -
                            BRYOPHYTE_MARGIN_EXTRA, 5, pos_info)

        self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA)
        self.pdf.multi_cell(DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN -
                            BRYOPHYTE_MARGIN_EXTRA, 5, leg_info)

        main_info = '; '.join([x.strip() for x in [smartify_language(note, lang='en'),
                                                   smartify_language(place, lang='en')
                                                   ] if x])

        self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA)
        self.pdf.multi_cell(DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN -
                            BRYOPHYTE_MARGIN_EXTRA, 5, main_info)

        self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
        if det_info:
            self.pdf.multi_cell(DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN,
                                5, det_info)

        if addinfo:
            self.pdf.set_font('DejaVu', '', BRYOPHYTE_NOTENUM_FSIZE)
            self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
            _y = self.pdf.get_y()
            self.pdf.line(BRYOPHYTE_LEFT_MARGIN, _y,
                          BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_LINE_LENGTH, _y)
            _y += 4
            for ind, _note in addinfo:
                self.pdf.set_font('DejaVu', '', BRYOPHYTE_NOTENUM_FSIZE)
                self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN, _y - 1)
                self.pdf.cell(0, 0, '(' + str(ind) + ')')
                self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + 5, _y - 2)
                self.pdf.set_font('DejaVu', '', BRYOPHYTE_NOTE_FSIZE)
                self.pdf.multi_cell(DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN - 4,
                    3, _note)
                _y = self.pdf.get_y()
                _y += 3


        # Barcode insertion
        barcodesize = 5.0 * BARCODE_ITEM_WIDTH * len(str(acronym).upper() + str(itemid))
        self.put_barcode(acronym, itemid, institute,
                            DEFAULT_PAGE_WIDTH - barcodesize - BRYOPHYTE_LEFT_MARGIN,
                            DEFAULT_PAGE_HEIGHT - 20)


    def generate_labels(self, labels):
        for label in labels:
            self.generate_label(**label)
            if label != labels[-1]:
                self.pdf.add_page()


if __name__ == '__main__':
    my = BARCODE()
    my.put_barcode('VBGI', 1231231, 10, 10)
    my.create_file('myf.pdf')
