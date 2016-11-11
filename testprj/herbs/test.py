#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from fpdf import FPDF


pdf = FPDF()
pdf.add_page()
pdf.image('./imgs/bgi_logo.png', w=15, h=15)
pdf.set_font('times')
pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)

pdf.set_font('DejaVu', '', 14)
pdf.set_xy(30,12)
pdf.cell(90,0,'Ботанический сад-институт ДВО РАН', align='C')
pdf.set_font_size(8)
pdf.set_xy(30, 18)
pdf.cell(90,0, '690024, г. Владивосток, ул. Маковского, 142',align='C')
pdf.set_xy(30, 22)
pdf.cell(90, 0, 'VLA, Botanical Garden-Institue, Vladivostok', align='C')
pdf.set_font('DejaVui', '', 10)
pdf.rect(5,5,120,100, '')
pdf.line(8,27,122,27)
pdf.output('MYF.pdf', 'F')


