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
        self._stack_.append(tag)

    def handle_endtag(self, tag):
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
    
    def width(self, font_size):
        w = 0
        for item in self.data:
            self.pdf_driver.set_font(self.pdf_driver.choose_font(item[-1]), item[0], font_size)
            w += self.pdf_driver.pdf.get_string_width(item[0])
        return w

    def print(self):
        raise NotImplementedError

