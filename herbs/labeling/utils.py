#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .settings import *
import tempfile
import qrcode
from bs4 import BeautifulSoup

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


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
    except TypeError:
        with open(temp_name, 'wb') as tmpfile:
            img.save(tmpfile)
            tmpfile.flush()
            pdf.set_xy(x + lw - QR_SIZE - 2, y + lh - QR_SIZE - 4)
            pdf.image(temp_name, w=QR_SIZE, h=QR_SIZE)
    finally:
        try:
            os.remove(temp_name)
        except IOError:
            pass

def lat_repr(latitude):
    res = ''
    if latitude:
        res += '{0: .5f}'.format(abs(float(latitude)))
        if float(latitude) >= 0.0:
            res += u'\N{DEGREE SIGN}N'
        else:
             res += u'\N{DEGREE SIGN}S'
    return res

def lon_repr(longitude):
    res = ''
    if longitude:
        res += '{0:.5f}'.format(abs(float(longitude)))
        if float(longitude) >= 0.0:
            res += u'\N{DEGREE SIGN}E'
        else:
            res += u'\N{DEGREE SIGN}W'
    return res


class LabelParser(HTMLParser, object):

    def __init__(self, *args, **kwargs):
        self._stack_ = ['']
        self._data_ = []
        super(LabelParser, self).__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'sup':
            tag = 'v'
        elif tag.lower() == 'sub':
            tag = 'n'
        self._stack_.append(tag)

    def handle_endtag(self, tag):
        if tag.lower() == 'sup':
            tag = 'v'
        elif tag.lower() == 'sub':
            tag = 'n'
        if tag in self._stack_:
            self._stack_.reverse()
            self._stack_.remove(tag)
            self._stack_.reverse()

    def handle_entityref(self, name):
        self._data_.append((BeautifulSoup('&' + name + ';', 'html.parser').text, ''.join(self._stack_)))

    def handle_data(self, data):
        self._data_.append((data, ''.join(self._stack_)))

    @property
    def parsed(self):
        return self._data_


class Word:
    """
    An abstract element that can be safely printed
    """

    def __init__(self, data, pdf_driver):
        self.data = data
        self.pdf_driver = pdf_driver
    
    def select_font_size(self, item, font_size):
        if 'n' in item[-1]:
            fs = font_size * SUBSCRIPT_FS
        elif 'v' in item[-1]:
            fs = font_size * SUPERSCRIPT_FS
        else:
            fs = font_size
        return fs

    def width(self, font_size):
        w = 0
        for item in self.data:
            fs = self.select_font_size(item, font_size)
            self.pdf_driver.pdf.set_font(self.pdf_driver.choose_font(item[-1]), item[0], fs)
            w += self.pdf_driver.pdf.get_string_width(item[0])
        return w

    def render(self, xpos, ypos, font_size):
        xpos = xpos
        for item in self.data:
            fs = self.select_font_size(item, font_size)
            if 'n' in item[-1]:
                shift = SUBSCRIPT_SHIFT
            elif 'v' in item[-1]:
                shift = SUPERSCRIPT_SHIFT
            else:
                shift = 0
            self.pdf_driver.pdf.set_xy(xpos, ypos + shift)
            self.pdf_driver.pdf.set_font(self.pdf_driver.choose_font(item[-1]), item[0], fs)
            self.pdf_driver.pdf.cell(0, 0, item[0])
            self.pdf_driver.pdf.set_y(ypos)
            xpos += self.pdf_driver.pdf.get_string_width(item[0])
        return xpos
