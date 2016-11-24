#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import fpdf
import tempfile
import qrcode, os
from transliterate import translit
from countries import eng_codes, codes

msgs = {'org':   'Herbarium',
        'addr':  '690024, Russia, Vladivostok, Makovskogo st., 142',
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

def translate_country_name(name):
    try:
        res = eng_codes[codes[name.encode('utf-8')]]
    except:
        res = translit(name, 'ru', reversed=True)
    return res

FPDF = fpdf.FPDF

BASE_URL = os.path.dirname(os.path.abspath(__file__))

fpdf.set_global('FPDF_FONT_DIR', os.path.join(BASE_URL, './fonts'))

BGI_LOGO_IMG = os.path.join(BASE_URL, './imgs', 'bgi_logo.png')

LABEL_WIDTH = 140
LABEL_HEIGHT = 100

FIRST_LINE = LABEL_HEIGHT/7
global LINE_HEIGHT
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

HERBURL = 'http://botsad.ru/hitem/%s'


def insert_qr(pdf, x, y, code=1234567):
    if len(code) > 8: return;
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(HERBURL % code)
    qr.make(fit=True)
    img = qr.make_image()
    temp_name = os.path.join(BASE_URL, './tmp',
                             next(tempfile._get_candidate_names()))
    temp_name += '.png'
    try:
        with open(temp_name, 'w') as tmpfile:
            img.save(tmpfile)
            tmpfile.flush()
            pdf.set_xy(x + LABEL_WIDTH - QR_SIZE - 2, y + LABEL_HEIGHT - QR_SIZE - 4)
            pdf.image(temp_name, w=QR_SIZE, h=QR_SIZE)
    finally:
        try:
            os.remove(temp_name)
        except IOError:
            pass

def to_unicode(s):
    if isinstance(s, unicode):
        return s
    elif s is None:
        return u''
    else:
        return s.decode('utf-8')

class PDF_DOC:
    def __init__(self):
        self.pdf = FPDF(orientation='L')
        self.pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)
        self.pdf.add_font('DejaVub', '', 'DejaVuSans-Bold.ttf', uni=True)
        self.pdf.set_margins(5, 5, 5)
        self.pdf.set_auto_page_break(0, 0)
        self.pdf.add_page()
        self._ln = 0

    def goto(self, y, n, inter=0):
        return  y + PADDING_Y + (LINE_HEIGHT + INTERSPACE) * n + inter

    def _add_label(self, x, y, family='', species='', spauth1='', spauth2='',
                   date='', latitude='', longitude='',
                   place='', country='', region='', collected='',
                   altitude='', identified='', number='', itemid='',
                   acronym='', institute=''):
        global LINE_HEIGHT
        self.pdf.rect(x, y, LABEL_WIDTH,LABEL_HEIGHT, '')
        self.pdf.set_xy(x + PADDING_X, y + PADDING_Y)
        self.pdf.image(BGI_LOGO_IMG, w=LOGO_WIDTH, h=LOGO_HEIGHT)

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
        self.pdf.cell(LABEL_WIDTH - LOGO_WIDTH - 2 * PADDING_X, 0, msgs['addr'],
                      align='C')
        self.pdf.line(x + PADDING_X, self.goto(y,2) + 4,
                     x + LABEL_WIDTH - PADDING_X, self.goto(y,2) + 4)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln) + 1)
        self.pdf.set_font('DejaVui', '', REGULAR_FONT_SIZE)
        if family:
            self.pdf.cell(LABEL_WIDTH - 2 * PADDING_X, 0, '{}'.format(family),
                          align='C')
        else:
            self.pdf.cell(LABEL_WIDTH - 2 * PADDING_X, 0, '_____________________',
                          align='C')

        # -------------- Plot Species name ------------
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        species_name = species
        author_name =  ''
        author_name += '(%s)' % spauth2 if spauth2 else ''
        author_name += ' %s' % spauth1 if spauth1 else ''
        self.pdf.set_font_size(SMALL_FONT_SIZE)
        sp_w = self.pdf.get_string_width(species_name)
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        au_w = self.pdf.get_string_width(author_name)
        x_pos = LABEL_WIDTH / 2 - (au_w + sp_w + 2) / 2
        if x_pos > PADDING_X:
            self.pdf.set_xy(x + x_pos, self.goto(y, self._ln))
        self.pdf.set_font('DejaVui', '', SMALL_FONT_SIZE)
        self.pdf.set_font_size(SMALL_FONT_SIZE)
        self.pdf.cell(0, 0, '{}'.format(species_name))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x+ x_pos + sp_w + 2, self.goto(y, self._ln))
        self.pdf.cell(0, 0,'{}'.format(author_name))
        # ----------------------------------------------



        # ------------- place of collecting ------------
        if not country: country = ''
        country = translate_country_name(country)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y,self._ln))
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        tw = self.pdf.get_string_width(msgs['country'])
        self.pdf.cell(0,0, msgs['country'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        cw = self.pdf.get_string_width( country)
        self.pdf.cell(0, 0, country)

        if region:
            region = translit(region, 'ru', reversed=True)
            self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
            rw = self.pdf.get_string_width(msgs['region'])
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
            rtw = self.pdf.get_string_width(region)
            if (PADDING_X + 4 + tw + cw + rw + rtw < LABEL_WIDTH):
                self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                self.pdf.set_xy(x + PADDING_X + 4 + tw + cw,
                                self.goto(y, self._ln))
                self.pdf.cell(0, 0, msgs['region'])
                self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
                self.pdf.set_xy(x + PADDING_X + 5 + tw + cw + rw,
                                self.goto(y, self._ln))
                self.pdf.cell(0, 0, region)
        # split long text of the place foundi
        prepare = []
        if place:
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
            if len(prepare) > 2:
                LINE_HEIGHT *= LINE_SCALE
                inter = INTERSPACE + SMALL_FONT_SIZE/3.0
            else:
                inter = 0
            for line in prepare[1:]:
                self._ln += 1
                self.pdf.set_xy(x + PADDING_X + 2, self.goto(y, self._ln, inter=inter))
                self.pdf.cell(0, 0, line)

       # ----------------------------------------------
        # ------------- Altitude info ------------------
        self._ln += 1 if len(prepare) < 3 else 2
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        tw = self.pdf.get_string_width(msgs['alt'])
        self.pdf.cell(0, 0, msgs['alt'])
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.cell(0, 0, altitude)

        # ------------- Coordinates found -------------
        self._ln += 1
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        tw = self.pdf.get_string_width(msgs['coords'])
        self.pdf.cell(0, 0, msgs['coords'])
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        if latitude and longitude:
            self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
            self.pdf.cell(0, 0, 'LAT=' + str(latitude) + u'\N{DEGREE SIGN},'+\
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
        self.pdf.cell(0, 0, date)
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
        fflag = True
        collected = translit(collected, 'ru', reversed=True)
        for k in collected.split():
            ss += self.pdf.get_string_width(k + ' ')
            if (ss < (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE)) and fflag:
                fline.append(k)
            if  (ss >= (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE)) and fflag:
                break
        if fline:
            fline = ' '.join(fline).strip()
            if fline[-1] == ',': fline = fline[:-1]
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
        iw = self.pdf.get_string_width(identified)
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        if ((tw + iw) > (LABEL_WIDTH-PADDING_X-QR_SIZE)):
            self.pdf.cell(0, 0, '____________________')
        else:
            self.pdf.cell(0, 0, identified)

        # ----------------------------------------------

        # -----------------------------------------------

        # ------------ Catalogue number ----------------
        if len(prepare)>2: LINE_HEIGHT /= LINE_SCALE
        self.pdf.set_font_size(TITLE_FONT_SIZE + 2)
        self.pdf.set_xy(x + 2 * PADDING_X, y + LABEL_HEIGHT - PADDING_Y)
        self.pdf.cell(0, 0, 'ID: %s/%s' % (number, itemid))

        # ----------------------------------------------

        # --------- qr insertion -----------------------
        insert_qr(self.pdf, x, y, code=itemid)

        # ----------------------------------------------

        # Extra info (to get without qr reader ----------
        self.pdf.set_font_size(SMALL_FONT_SIZE-4)
        tw = self.pdf.get_string_width(HERBURL % itemid)
        self.pdf.set_xy(x + LABEL_WIDTH - PADDING_X - tw, y + LABEL_HEIGHT - 2)
        self.pdf.cell(0,0, HERBURL % itemid)

        # ----------------------------------------------


    def make_label(self, x, y, **kwargs):
        self._ln = 0
        self._add_label(x, y, **kwargs)

    def tile_labels(self, l_labels):
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
            self.make_label(x, y+ LABEL_HEIGHT + 1, **l_labels[2])
        elif len(l_labels) == 4:
            self.make_label(x, y, **l_labels[0])
            self.make_label(x + LABEL_WIDTH + 2, y, **l_labels[1])
            self.make_label(x, y + LABEL_HEIGHT + 1, **l_labels[2])
            self.make_label(x + LABEL_WIDTH + 2, y + LABEL_HEIGHT + 1,
                            **l_labels[3])
        else:
            pass

    def _test_page(self):
        testdict = {'family': 'AWESOMEFAMILY', 'species':'Some species',
                    'spauth1':'Author1', 'spauth2':'',
                    'date': '12 Nov 2002',
                    'latitude': '12.1231',
                    'longitude': '123.212312',
                    'region': u'Приморский край',
                    'altitude': '123 m o.s.l',
                    'country': u'Россия',
                    'place': u'Никому неизвестное село глубоко в лесу; На горе росли цветы небывалой красоты, мы собрали их в дождливую погоду и было очень прохладно',
                    'collected':u'Один М.С., Другой Б.В., Третий А.А., Четвертый Б.Б., Пятый И.И., Шестой В.В., Седьмой' ,
                    'identified':u'Один, Другой',
                    'number': '17823781', 'itemid': '12312',
                    'acronym':'VBGI',
                    'institute': 'Botanical Garden-Institute FEB RAS'}
        llabels = [testdict] * 4
        self.tile_labels(llabels)

    def get_pdf(self):
        return self.pdf.output(dest='S')

    def create_file(self, fname):
        self.pdf.output(fname, dest='F')

if __name__ == '__main__':
    my = PDF_DOC()
    my._test_page()
    print my.get_pdf()
