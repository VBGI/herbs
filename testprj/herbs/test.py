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
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)

    def _add_label(self, x, y, family=''):
        pdf.rect(x, y, LABEL_WIDTH,LABEL_HEIGHT, '')
        pdf.rect(x-3, y-3, LABEL_WIDTH+6, LABEL_HEIGHT+6, '')
        pdf.set_xy(x+5, y+5)
        pdf.image('./imgs/bgi_logo.png', w=15, h=15)
        pdf.set_font('DejaVu', '', 14)
        pdf.set_xy(x+20, goto(0))
        pdf.cell(LABEL_WIDTH - 20, 0, msgs['org'], align='C')
        pdf.set_font_size(10)
        pdf.set_xy(x+20, goto(1))
        pdf.cell(LABEL_WIDTH - 20,0, msgs['addr'],align='C')
        pdf.set_xy(x+20, goto(2))
        pdf.cell(LABEL_WIDTH - 20, 0,msgs['descr'], align='C')
        pdf.line(x + 5, goto(2) + 4,LABEL_WIDTH + 5 - 2 ,goto(2) + 4)
        pdf.set_xy(x + 5, goto(3))
        pdf.set_font('DejaVui', '', 12)
        if family_name:
            pdf.cell(LABEL_WIDTH, 0, '{}'.format(family_name), align='C')
        else:
            pdf.cell(LABEL_WIDTH, 0, '_____________________', align='C')

        # -------------- Plot Genus name ---------------
        pdf.set_xy(5, goto(4))
        species_name = 'Some species'
        author_name = '(Sec. Author) Prim. Author'
        pdf.set_font_size(10)
        sp_w = pdf.get_string_width(species_name)
        pdf.set_font('DejaVu', '', 10)
        au_w = pdf.get_string_width(author_name)
        pdf.set_xy(LABEL_WIDTH/2-(au_w+sp_w+2)/2, goto(4))
        pdf.set_font('DejaVui', '', 10)
        pdf.set_font_size(10)
        pdf.cell(0,0, '{}'.format(species_name))
        pdf.set_font('DejaVu', '', 10)
        pdf.set_xy(LABEL_WIDTH/2-(au_w+sp_w+2)/2 + sp_w + 2, goto(4))
        pdf.cell(0,0,'{}'.format(author_name))
        # ----------------------------------------------













# ------------- place of collecting ------------
pdf.set_xy(5,goto(5))
pdf.set_font('DejaVu', '', 9)
tw = pdf.get_string_width(msgs['where'])
pdf.cell(0, 0, msgs['where'])
pdf.set_xy(5 + 1 + tw, goto(5))
pdf.cell(0, 0, 'Россия, Приморский край, с.xxxx')


pdf.set_xy(5, goto(6))
pdf.cell(LABEL_WIDTH, 0, 'более длинное описание места сбора...', align='C')
# ----------------------------------------------


# ------------- Coordinates found -------------

pdf.set_xy(5, goto(7))
tw = pdf.get_string_width(msgs['coords'])
pdf.cell(0,0, msgs['coords'])
pdf.set_xy(5+1+tw, goto(7))
pdf.cell(0,0, 'LAT=12.2390'+u'\N{DEGREE SIGN}'+', '+'LON=123.399312'+u'\N{DEGREE SIGN}')


#-----------------------------------------------

pdf.set_xy(5, goto(8))
pdf.cell(0,0,msgs['date'])
tw=pdf.get_string_width(msgs['date'])
pdf.set_xy(5+1+tw, goto(8))
pdf.cell(0,0,'12 Июля 2000 г.')

pdf.set_xy(5, goto(9))
pdf.cell(0,0,msgs['det'])
tw=pdf.get_string_width(msgs['det'])
pdf.set_xy(5+1+tw, goto(9))
pdf.cell(0,0,'Иванов И.И., Петров А.А. ')

pdf.set_font_size(12)
pdf.set_xy(15,goto(11))
pdf.cell(0,0,'Инв. №: 445511:1122')



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




