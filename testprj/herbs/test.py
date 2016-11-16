#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from fpdf import FPDF
import tempfile

msgs = {'org':   'Ботанический сад-институт ДВО РАН',
        'addr':  '690024, г. Владивосток, ул. Маковского, 142',
        'descr': 'VLA, Botanical Garden-Institue, Russia, Vladivostok',
        'where': 'Место сбора / Place found:',
        'coords': 'Координаты / Coordinates:',
        'date': 'Дата сбора / Date found:',
        'det': 'Определил(и) / Identified by:'
        }


pdf = FPDF(orientation='L')
pdf.add_page()

LABEL_WIDTH = 140
LABEL_HEIGHT = 100

FIRST_LINE = LABEL_HEIGHT/7
LINE_HEIGHT = LABEL_HEIGHT/12

MARGIN_X = 10
MARGIN_Y = 10


goto = lambda n: FIRST_LINE + LINE_HEIGHT * n



class PDF_DOC:
    def __init__(self):
        self.pdf = FPDF(orientation='L')
        self.pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)

    def _add_label(self, x, y, family='', species='', spauth1='', spauth2='',
                   date=''):
        self.pdf.rect(x, y, LABEL_WIDTH,LABEL_HEIGHT, '')
        self.pdf.rect(x - 3, y - 3, LABEL_WIDTH + 6, LABEL_HEIGHT + 6, '')
        self.pdf.set_xy(x + 5, y + 5)
        self.pdf.image('./imgs/bgi_logo.png', w=15, h=15)
        self.pdf.set_font('DejaVu', '', 14)
        self.pdf.set_xy(x + 20, goto(0))
        self.pdf.cell(LABEL_WIDTH - 20, 0, msgs['org'], align='C')
        self.pdf.set_font_size(10)
        self.pdf.set_xy(x + 20, goto(1))
        self.pdf.cell(LABEL_WIDTH - 20,0, msgs['addr'],align='C')
        self.pdf.set_xy(x + 20, goto(2))
        self.pdf.cell(LABEL_WIDTH - 20, 0,msgs['descr'], align='C')
        self.pdf.line(x + 5, goto(2) + 4,LABEL_WIDTH + 5 - 2 ,goto(2) + 4)
        self.pdf.set_xy(x + 5, goto(3))
        self.pdf.set_font('DejaVui', '', 12)
        if family:
            self.pdf.cell(LABEL_WIDTH, 0, '{}'.format(family), align='C')
        else:
            self.pdf.cell(LABEL_WIDTH, 0, '_____________________', align='C')

        # -------------- Plot Genus name ---------------
        self.pdf.set_xy(x + 5, goto(4))
        species_name = species
        author_name = ''
        author_name += '(%s)' % spauth2 if spauth2 else ''
        author_name += ' %s' % spauth1 if spauth1 else ''
        self.pdf.set_font_size(11)
        sp_w = self.pdf.get_string_width(species_name)
        self.pdf.set_font('DejaVu', '', 11)
        au_w = self.pdf.get_string_width(author_name)
        self.pdf.set_xy(LABEL_WIDTH/2-(au_w+sp_w+2)/2, goto(4))
        self.pdf.set_font('DejaVui', '', 11)
        self.pdf.set_font_size(11)
        self.pdf.cell(0,0, '{}'.format(species_name))
        self.pdf.set_font('DejaVu', '', 11)
        self.pdf.set_xy(LABEL_WIDTH/2-(au_w+sp_w+2)/2 + sp_w + 2, goto(4))
        self.pdf.cell(0,0,'{}'.format(author_name))
        # ----------------------------------------------



        # ------------- place of collecting ------------

        self.pdf.set_xy(5, goto(5))
        self.pdf.set_font('DejaVu', '', 9)
        tw = self.pdf.get_string_width(msgs['where'])
        self.pdf.cell(0, 0, msgs['where'])
        self.pdf.set_xy(x + 5 + 1 + tw, goto(5))
        self.pdf.cell(0, 0, place_short)
        self.pdf.set_xy(x + 5, goto(6))
        self.pdf.cell(LABEL_WIDTH, 0, place_long, align='C')

        # ----------------------------------------------

        # ------------- Coordinates found -------------

        self.pdf.set_xy(x + 5, goto(7))
        tw = self.pdf.get_string_width(msgs['coords'])
        self.pdf.cell(0, 0, msgs['coords'])

        if self.latitude and self.longitude:
            self.pdf.set_xy(x + 5 + 1 + tw, goto(7))
            self.pdf.cell(0, 0, 'LAT=' + str(latitude) + u'\N{DEGREE SIGN}'+\
                          ' LON=' + str(longitude) + u'\N{DEGREE SIGN}')

        # ----------------------------------------------

        # ----------- Date found -----------------------
        self.pdf.set_xy(x + 5, goto(8))
        self.pdf.cell(0, 0, msgs['date'])
        tw = self.pdf.get_string_width(msgs['date'])
        self.pdf.set_xy(x + 5 + 1 + tw, goto(8))
        self.pdf.cell(0, 0, str(date))


        self.df.set_xy(x + 5, goto(9))
        self.pdf.cell(0, 0, msgs['det'])
        tw = self.pdf.get_string_width(msgs['det'])
        self.pdf.set_xy(x + 5 + 1 + tw, goto(9))

        for k in identified.split():
            pass
        self.pdf.cell(0,0, iden)

        self.pdf.set_font_size(12)
        self.pdf.set_xy(x + 15, goto(11))
        self.pdf.cell(0,0,'Инв. №: %s' % number)



import qrcode, os


qr = qrcode.QRCode(
    version=2,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=2,
)
qr.add_data('http://botsad.ru/hitem/1234567')
qr.make(fit=True)
img = qr.make_image()


temp_name = os.path.join('./tmp', next(tempfile._get_candidate_names()))
temp_name += '.png'

try:
    with open(temp_name, 'w') as tmpfile:
        img.save(tmpfile)
        tmpfile.flush()
        pdf.set_xy(LABEL_WIDTH+5-24,LABEL_HEIGHT+5-24)
        pdf.image(temp_name, w=22, h=22)
finally:
    try:
        os.remove(temp_name)
    except IOError:
        pass

pdf.output('MYF.pdf', 'F')




