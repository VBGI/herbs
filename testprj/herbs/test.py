#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from fpdf import FPDF


pdf = FPDF()
pdf.add_page()

LABEL_WIDTH = 110
LABEL_HEIGHT = 80

FIRST_LINE = LABEL_HEIGHT/7
LINE_HEIGHT = LABEL_HEIGHT/12


pdf.rect(5,5,LABEL_WIDTH,LABEL_HEIGHT, '')
pdf.rect(2,2,LABEL_WIDTH+6,LABEL_HEIGHT+6, '')
pdf.image('./imgs/bgi_logo.png', w=15, h=15)


pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)

pdf.set_font('DejaVu', '', 13)
pdf.set_xy(22,FIRST_LINE)
pdf.cell(LABEL_WIDTH - 22,0,'Ботанический сад-институт ДВО РАН', align='C')
pdf.set_font_size(8)
pdf.set_xy(22, FIRST_LINE + LINE_HEIGHT)
pdf.cell(LABEL_WIDTH - 22,0, '690024, г. Владивосток, ул. Маковского, 142',align='C')
pdf.set_xy(22, FIRST_LINE + LINE_HEIGHT * 2)
pdf.cell(LABEL_WIDTH - 22, 0, 'VLA, Botanical Garden-Institue, Russia, Vladivostok', align='C')
pdf.set_font('DejaVui', '', 10)
pdf.line(7, FIRST_LINE + LINE_HEIGHT * 2 + 3,LABEL_WIDTH + 5 - 2 ,FIRST_LINE+LINE_HEIGHT*2+3)

# -------------- Plot Family -------------------
family_name = 'AWESOMEFAMILY'

pdf.set_xy(5, FIRST_LINE + LINE_HEIGHT * 3)
pdf.set_font('DejaVui', '', 11)

if family_name:
    pdf.cell(LABEL_WIDTH, 0, '{}'.format(family_name), align='C')
else:
    pdf.cell(LABEL_WIDTH, 0, '_____________________', align='C')
# ----------------------------------------------



# -------------- Plot Genus name ---------------
pdf.set_xy(5, FIRST_LINE + LINE_HEIGHT * 4)
species_name = 'Some species'
author_name = '(Second. Invent.) Prim. Invent.'
pdf.set_font_size(10)
sp_w = pdf.get_string_width(species_name)
pdf.set_font('DejaVu', '', 10)
au_w = pdf.get_string_width(author_name)

pdf.set_xy(LABEL_WIDTH/2-(au_w+sp_w+2)/2, FIRST_LINE + LINE_HEIGHT * 4)
pdf.set_font('DejaVui', '', 10)
pdf.set_font_size(10)
pdf.cell(0,0, '{}'.format(species_name))
pdf.set_font('DejaVu', '', 10)

pdf.set_xy(LABEL_WIDTH/2-(au_w+sp_w+2)/2 + sp_w + 2, FIRST_LINE + LINE_HEIGHT * 4)
pdf.cell(0,0,'{}'.format(author_name))
# ----------------------------------------------


pdf.interleaved2of5('123456', 15, LABEL_HEIGHT-6,w=1,h=8)
pdf.interleaved2of5('123456', 50, LABEL_HEIGHT-6,w=1,h=8)
pdf.interleaved2of5('123456', 80, LABEL_HEIGHT-6,w=1,h=8)
pdf.output('MYF.pdf', 'F')


