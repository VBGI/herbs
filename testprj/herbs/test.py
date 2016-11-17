#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import fpdf
import tempfile
import qrcode, os

msgs = {'org':   'Botanical Garden Institute',
        'addr':  '690024, Russia, Vladivostok, Makovskogo st., 142',
        'descr': 'Herbarium of the Botanical Garden Institute (VBGI)',
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

fpdf.set_global('FPDF_FONT_DIR',
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'))


LABEL_WIDTH = 140
LABEL_HEIGHT = 100

FIRST_LINE = LABEL_HEIGHT/7
LINE_HEIGHT = LABEL_HEIGHT/13

PADDING_X = 3
PADDING_Y = 4

LOGO_WIDTH = 15
LOGO_HEIGHT = 15

QR_SIZE = 28

TITLE_FONT_SIZE = 16
REGULAR_FONT_SIZE = 14
SMALL_FONT_SIZE = 12


def insert_qr(pdf, x, y, code=1234567):
    if len(code) > 8: return;
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data('http://botsad.ru/hitem/%s' % code)
    qr.make(fit=True)
    img = qr.make_image()
    temp_name = os.path.join('./tmp', next(tempfile._get_candidate_names()))
    temp_name += '.png'
    try:
        with open(temp_name, 'w') as tmpfile:
            img.save(tmpfile)
            tmpfile.flush()
            pdf.set_xy(x + LABEL_WIDTH - QR_SIZE - 2, y + LABEL_HEIGHT - QR_SIZE - 2)
            pdf.image(temp_name, w=QR_SIZE, h=QR_SIZE)
    finally:
        try:
            os.remove(temp_name)
        except IOError:
            pass


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

    def goto(self, y, n):
        return  y + PADDING_Y + LINE_HEIGHT * n

    def _add_label(self, x, y, family='', species='', spauth1='', spauth2='',
                   date='', latitude='', longitude='',
                   place='', country='', region='', collected='',
                   altitude='', identified='', number='', itemid=''):
        self.pdf.rect(x, y, LABEL_WIDTH,LABEL_HEIGHT, '')
        self.pdf.set_xy(x + PADDING_X, y + PADDING_Y)
        self.pdf.image('./imgs/bgi_logo.png', w=LOGO_WIDTH, h=LOGO_HEIGHT)

        self.pdf.set_font('DejaVu', '', TITLE_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X + LOGO_WIDTH, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - LOGO_WIDTH-2 * PADDING_X, 0, msgs['org'],
                      align='C')
        self.pdf.set_font_size(REGULAR_FONT_SIZE)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X + LOGO_WIDTH, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - LOGO_WIDTH - 2 * PADDING_X, 0, msgs['descr'],
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
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y,self._ln))
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        tw = self.pdf.get_string_width(msgs['country'])
        self.pdf.cell(0,0, msgs['country'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        cw = self.pdf.get_string_width(country)
        self.pdf.cell(0, 0, country)
        if region:
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
        # split long text of the place found

        if place:
            self._ln += 1
            self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
            tw = self.pdf.get_string_width(msgs['place'])
            self.pdf.set_xy(x + PADDING_X + 1, self.goto(y, self._ln))
            self.pdf.cell(0, 0, msgs['place'])
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
            cline = []
            ss = PADDING_X + 1 + tw
            ln = 1
            for item in place.split():
                ss += self.pdf.get_string_width(item + ' ')
                print item, len(cline), ss
                if ss < LABEL_WIDTH-2*PADDING_X:
                    cline.append(item)
                else:
                    if ln == 1:
                        self.pdf.set_xy(x + PADDING_X + 2 + tw,self.goto(y, self._ln))
                        self.pdf.cell(0, 0, ' '.join(cline))
                        cline = [item]
                        ss = PADDING_X + 1
                        ln += 1
                        self._ln += 1
                    else:
                        break
            else:
                if cline:
                    self.pdf.set_xy(x + PADDING_X + 2, self.goto(y, self._ln))
                    self.pdf.cell(0, 0, ' '.join(cline))
        # ----------------------------------------------
        # ------------- Altitude info ------------------
        self._ln += 1
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
        self.pdf.cell(0, 0, str(date))
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        self.pdf.cell(0, 0, msgs['col'])
        tw = self.pdf.get_string_width(msgs['col'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        ss = 0
        fline = []
        fflag = True
        for k in collected.split():
            ss += self.pdf.get_string_width(k + ' ')
            if (ss < (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE)) and fflag:
                fline.append(k)
            if  (ss >= (LABEL_WIDTH - tw - 1 - 2 * PADDING_X-QR_SIZE)) and fflag:
                fline += '...'
                break
        if fline:
            self.pdf.cell(0, 0, ' '.join(fline))
        # ----------------------------------------------

        # --------------- Identified by ----------------
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

        self.pdf.set_font_size(TITLE_FONT_SIZE + 2)
        self.pdf.set_xy(x + 2 * PADDING_X, y + LABEL_HEIGHT - PADDING_Y)
        self.pdf.cell(0, 0, 'ID: %s/%s' % (number, itemid))

        # ----------------------------------------------

        # --------- qr insertion -----------------------
        insert_qr(self.pdf, x, y, code=itemid)

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
                    'date':'12 ноября 2002 г.','latitude': '12.1231',
                    'longitude': '123.212312',
                    'region': 'Приморский край',
                    'altitude': '123 m o.s.l',
                    'country': 'Россия',
                    'place': 'Никому неизвестное село глубоко в лесу; На горе росли цветы небывалой красоты, мы собрали их в дождливую погоду и было очень прохладно',
                    'collected':'Один М.С., Другой Б.В., Третий А.А., Четвертый Б.Б., Пятый И.И., Шестой В.В., Седьмой' ,
                    'identified':'Один, Другой',
                    'number': '17823781', 'itemid': '12312'}
        llabels = [testdict] * 4
        self.tile_labels(llabels)

    def create_file(self, fname):
        self.pdf.output(fname, 'F')



my = PDF_DOC()
my._test_page()
my.create_file('myf.pdf')






