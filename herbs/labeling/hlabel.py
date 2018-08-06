#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .settings import *
from .utils import *
from PIL import Image

if __name__ == '__main__':
    from transliterate import translit
    def smartify_language(value, lang=''):
        return value
    SIGNIFICANCE = (('aff.', 'affinis'),
                    ('cf.', 'confertum')
                    )
    settings = None # mocking for testing ...
else:
    from django.conf import settings
    from ..utils import translit, smartify_language, SIGNIFICANCE

# ------------ PDF font autoselect: japanese, korean fonts support
class StyledPDF(fpdf.FPDF):

    def set_font(self, family, sample='', size=0):
        sample = sample or 'n'
        family = self._test_language(sample) or family
        super(StyledPDF, self).set_font(family, '', size)

    @staticmethod
    def _test_language(s):
        ranges = {
            'japanese' :
            [
            {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},
            # compatibility ideographs
            {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},
            # compatibility ideographs
            {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},
            # compatibility ideographs
            {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")},
            # compatibility ideographs
            {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},  # Japanese Kana
            {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},
            # cjk radicals supplement
            {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
            {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
            {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
            {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
            {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
            {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}
            # included as of Unicode 8.0
                ],
            'korean':
                [
                    {"from": ord(u"\uac00"), "to": ord(u"\ud7a3")}, #Hangul Syllables
                    {"from": ord(u"\u1100"), "to": ord(u"\u11ff")}, #Hangul Jamo
                    {"from": ord(u"\u3130"), "to": ord(u"\u318f")}, #Hangul Compatibility
                    {"from": ord(u"\ua960"), "to": ord(u"\ua97f")}, #Hangul Jamo Extended A
                    {"from": ord(u"\ud7b0"), "to": ord(u"\ud7ff")}, #Hangul Jamo Extended B
                ]
                    }

        def test_all_chars(char, lang):
            return any(
                [range["from"] <= ord(char) <= range["to"] for range in ranges[lang]])

        for lang in ranges:
            if list(map(lambda x: test_all_chars(x, lang), s.strip())).count(True) >= len(s.strip()) / 2.0:
                return lang
        return None


class PDF_MIXIN(object):
    def __init__(self, orientation='L'):
        self.pdf = StyledPDF(orientation=orientation)
        self.pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.pdf.add_font('DejaVui', '', 'DejaVuSans-Oblique.ttf', uni=True)
        self.pdf.add_font('DejaVub', '', 'DejaVuSans-Bold.ttf', uni=True)
        self.pdf.add_font('Dejavubi', '', 'DejaVuSans-BoldOblique.ttf', uni=True)
        self.pdf.add_font('japanese', '', 'sazanami-mincho.ttf', uni=True)
        self.pdf.add_font('korean', '', 'UnShinmun.ttf', uni=True)
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

    @staticmethod
    def choose_font(fs='', sample=''):
        if fs == '':
            return 'DejaVu'
        elif fs == 'i':
            return 'DejaVui'
        elif fs == 'b':
            return 'DejaVub'
        elif fs == 'bi' or fs == 'ib':
            return 'DejaVubi'
        else:
            return 'DejaVu'

    def smarty_print(self, txt, lh, y=None, left_position=0,
                     first_indent=10, right_position=10,
                     line_nums=4, force=False, font_size=10):

        def strip_item(item):
            return [item[0].strip(), item[1], item[2]]

        parser = LabelParser()
        done = False

        if y:
            ypos = y + lh / 2.0
        else:
            ypos = self.pdf.get_y() + lh / 2.0

        while not done:
            parser.feed(txt)
            line_number = 0
            lines = [[]]
            cline_width = 0
            for item in parser.parsed:
                _splitted = item[0].split() or ([' '] if item[0][:1] == ' ' else [])
                space_flag = '' + ('post' if item[0][-1] == ' ' else '') + \
                             ('pre' if item[0][0] == ' ' else '')
                for ind, word in enumerate(_splitted):
                    if line_number == 0:
                        allowed_line_length = right_position - left_position - first_indent
                    else:
                        allowed_line_length = right_position - left_position

                    word_to_print = word
                    if 'post' in space_flag and ind == len(_splitted) - 1:
                        word_to_print += ' '
                    elif 'pre' in space_flag and ind == 0: # REMOVED not lines[-1]
                        word_to_print = ' ' + word_to_print
                    if len(_splitted) > 1 and ind != len(_splitted) - 1:
                        word_to_print += ' '
                    self.pdf.set_font(self.choose_font(item[-1]),
                                      word_to_print, font_size)
                    current_width = self.pdf.get_string_width(word_to_print)
                    cline_width += current_width
                    if (cline_width > allowed_line_length) and lines[-1]:
                        lines.append([])
                        cline_width = current_width
                        line_number += 1
                    lines[-1].append((word_to_print,
                                      self.pdf.get_string_width(word_to_print.strip()),
                                      self.choose_font(item[-1])))
            if font_size < 2:
                done = True
            if line_number > line_nums and force:
                font_size -= 1
            else:
                done = True
        xpos = left_position + first_indent
        for indl, line in enumerate(lines):
            preset = []
            for ind, item in enumerate(line):
                if ind == 0:
                    preset.append(strip_item(item))
                    if item[0].endswith(' '):
                        preset.append(' ')
                elif ind == len(line) - 1:
                    if item[0].startswith(' '):
                        preset.append(' ')
                    preset.append(strip_item(item))
                else:
                    if item[0].startswith(' '):
                        preset.append(' ')
                    preset.append(strip_item(item))
                    if item[0].endswith(' '):
                        preset.append(' ')

            n_spaces = preset.count(' ')

            if indl == 0:
                allowed_line_length = right_position - left_position - first_indent
            else:
                allowed_line_length = right_position - left_position
            cum_width = sum(map(lambda x: x[1], filter(lambda x: isinstance(x, list), preset)))

            if n_spaces:
                sep_w = (allowed_line_length - cum_width) / float(n_spaces)
            else:
                sep_w = 0

            if indl == len(lines) - 1:
                self.pdf.set_font(preset[0][-1], '', font_size)
                sep_w = self.pdf.get_string_width(' ')


            for item in preset:
                if isinstance(item, list):
                    self.pdf.set_font(item[-1], item[0], font_size)
                    self.pdf.set_xy(xpos, ypos)
                    self.pdf.cell(0, 0, item[0])
                    xpos += item[1]
                else:
                    xpos += sep_w
            ypos += lh
            xpos = left_position
        self.pdf.set_y(ypos - lh / 2.0)


class PDF_DOC(PDF_MIXIN):

    def _add_label(self, x, y, family='', species='', spauth='',
                   coldate='', latitude='', longitude='',
                   place='', country='', region='', collected='',
                   altitude='', identifiedby=[''], number='', itemid='', fieldid='',
                   acronym='', institute='', address='', gform='', addspecies='',
                   district='', note='', short_note='', gpsbased='',
                   dethistory='', infra_rank='', infra_epithet='', logo_path='',
                   detdate='', type_status='', infra_authorship=''):
        self.pdf.rect(x, y, LABEL_WIDTH, LABEL_HEIGHT, '')
        self.pdf.set_xy(x + PADDING_X, y + PADDING_Y)

        if logo_path:
            impath = os.path.join(settings.MEDIA_ROOT, logo_path)
            try:
                w, h = Image.open(impath).size
                logo_w = float(w) / h * LOGO_HEIGHT
            except:
                logo_w = LOGO_WIDTH
        else:
                logo_w = LOGO_WIDTH
        self.pdf.image(logo_path or BGI_LOGO_IMG, w=logo_w, h=LOGO_HEIGHT)

        # ------------- Herbarium title -------------
        self.pdf.set_font('DejaVu', '', TITLE_FONT_SIZE + 2)
        self.pdf.set_xy(x + PADDING_X + logo_w, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - logo_w-2 * PADDING_X, 0, msgs['org'],
                      align='C')
        # -------------------------------------------


        # ----------- Select font size for address and institution name

        institute_fs = REGULAR_FONT_SIZE
        institution = msgs['descr'] % (institute, acronym)
        self.pdf.set_font_size(institute_fs)
        while self.pdf.get_string_width(institution) > (LABEL_WIDTH - logo_w - 2 * PADDING_X):
            institute_fs -= 1
            self.pdf.set_font_size(institute_fs)
        self._ln += 1
        self.pdf.set_xy(x + PADDING_X + logo_w, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - logo_w - 2 * PADDING_X, 0,
                      msgs['descr'] % (institute, acronym),
                      align='C')

        addr_fs = SMALL_FONT_SIZE
        self.pdf.set_font_size(addr_fs)
        while self.pdf.get_string_width(address) > (
                LABEL_WIDTH - logo_w - 2 * PADDING_X):
                addr_fs -= 1
                self.pdf.set_font_size(addr_fs)

        self._ln += 1
        self.pdf.set_xy(x + PADDING_X + logo_w, self.goto(y, self._ln))
        self.pdf.cell(LABEL_WIDTH - logo_w - 2 * PADDING_X, 0, address,
                      align='C')
        # -------------------------------------------------

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

        if place.strip():
            prepare = []
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
            self.pdf.cell(0, 0, 'LAT=' + lat_repr(latitude) + ',' +
                          ' LON=' + lon_repr(longitude))
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
        identifiedby = translit(identifiedby[0], 'ru', reversed=True)
        self._ln += 1
        self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
        self.pdf.set_xy(x + PADDING_X, self.goto(y, self._ln))
        self.pdf.cell(0, 0, msgs['det'])
        tw = self.pdf.get_string_width(msgs['det'])
        self.pdf.set_xy(x + PADDING_X + 1 + tw, self.goto(y, self._ln))
        self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE)
        ss = 0
        fline = []
        for k in identifiedby.split():
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
                    'coldate': '12 Nov 2002',
                    'latitude': '12.1231',
                    'longitude': '123.212312',
                    'region': u'Приморский край',
                    'altitude': '123 m o.s.l',
                    'country': u'Россия',
                    'place': u'Никому неизвестное село глубоко в лесу; На горе росли цветы небывалой красоты, мы собрали их в дождливую погоду и было очень прохладно',
                    'collected': u'Один М.С., Другой Б.В., Третий А.А., Четвертый Б.Б., Пятый И.И., Шестой В.В., Седьмой',
                    'identifiedby': [u'Один, Другой'],
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
        self.pdf.code39('*' + code + '*', x, y, w=BARCODE_ITEM_WIDTH,
                        h=BARCODE_ITEM_HEIGHT)
        barcodesize = 5.0 * BARCODE_ITEM_WIDTH * (len(code) + 2)
        self.pdf.set_font('DejaVu', '', fs)
        cw = self.pdf.get_string_width(code)
        self.pdf.set_xy(x + barcodesize / 2.0 - cw / 2.0,
                        y + BARCODE_ITEM_HEIGHT + 3)
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
            barwidth = 5.0 * BARCODE_ITEM_WIDTH * (len(code_string) + 2)
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

    def _change_font_size(self):
        self._nfs = self._sfs * BRYOPHYTE_NOTE_FSIZE / float(SMALL_FONT_SIZE)
        self._nnfs = self._sfs * BRYOPHYTE_NOTENUM_FSIZE / float(
            SMALL_FONT_SIZE)
        self._lh = 5.0 * self._sfs / float(SMALL_FONT_SIZE)

    def goto(self, n, inter=0, y=DEFAULT_PAGE_HEIGHT * 2.0 / 3.0):
        return y + BRYOPHYTE_TOP_MARGIN + self._lh * n + inter

    def clear_page(self):
        self.pdf.page -= 1
        self.pdf._beginpage('P')
        self._change_font_size()

    def check_resize_required(self, w, bw):
        a = ((self.pdf.get_x() + w) >= (DEFAULT_PAGE_WIDTH -
                                       BRYOPHYTE_LEFT_MARGIN - bw))
        b = (self.pdf.get_y() >= (DEFAULT_PAGE_HEIGHT - BARCODE_ITEM_HEIGHT - 11))
        return a and b

    def generate_label(self, allspecies=[],
                       coldate='', latitude='', longitude='',
                       place='', country='', region='', collected='',
                       altitude='', identifiedby=[], number='', itemid='',
                       fieldid='', acronym='', institute='', note='', detdate='',
                       district='', gpsbased='', dethistory=[], type_status=''):
        self._sfs = SMALL_FONT_SIZE
        self._change_font_size()

        label_width = DEFAULT_PAGE_WIDTH - 2 * BRYOPHYTE_LEFT_MARGIN
        #  get barcode width
        barcode_width = 5.0 * BARCODE_ITEM_WIDTH * len(str(acronym).upper() +
                                                     str(itemid) + '**')
        done = False
        while not done:
            resize_required = []
            self.clear_page()
            # -----  Insert qr-code in the center of the page ------
            insert_qr(self.pdf, DEFAULT_PAGE_WIDTH / 2.0 + QR_SIZE / 2.0,
                      DEFAULT_PAGE_HEIGHT / 2.0, code=itemid, lh=0, lw=0)
            # insert helper url
            self.pdf.set_font('DejaVu', '', SMALL_FONT_SIZE - 4)
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
                                self.goto(self._ln - 1))
                self.pdf.cell(0, 0, field_string)

            if type_status:
                self.pdf.set_text_color(255, 0, 0)
                self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN - BRYOPHYTE_MARGIN_EXTRA,
                                self.goto(self._ln) - 2)
                self.pdf.set_font('DejaVub', '', SMALL_FONT_SIZE)
                self.pdf.cell(0, 0, type_status)
                self.pdf.set_text_color(0, 0, 0)
                self._ln += 1

            addinfo = []
            addind = 1
            mainind = 0
            for sp, auth, ir, iep, iauth, _note in allspecies:
                mainind += 1
                self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                self.goto(self._ln))
                self.pdf.set_font('DejaVu', '', self._sfs)
                spaw = self.pdf.get_string_width(auth)
                if iauth:
                    auth = ''
                    spaw = -2

                # Smart confertum and affinis printing...
                sp_decomposed = list(map(lambda x: x.strip(), sp.split()))
                if len(sp_decomposed) == 1:
                    self.pdf.set_font('DejaVubi', '', self._sfs)
                    spw = self.pdf.get_string_width(sp)
                    self.pdf.cell(0, 0, sp)
                elif sp_decomposed[1] in list(map(lambda x: x[0], SIGNIFICANCE)):
                    try:
                        sp_genus, sp_sign, sp_epithet = sp_decomposed[:3]
                    except ValueError:
                        sp_genus, sp_sign, sp_epithet = '', '', ''

                    self.pdf.set_font('DejaVubi', '', self._sfs)
                    sp_genus_w = self.pdf.get_string_width(sp_genus + ' ')
                    self.pdf.cell(0, 0, sp_genus)

                    self.pdf.set_font('DejaVu', '', self._sfs)
                    sp_sign_w = self.pdf.get_string_width(sp_sign + ' ')
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + sp_genus_w,
                                    self.goto(self._ln))
                    self.pdf.cell(0, 0, sp_sign)

                    self.pdf.set_font('DejaVubi', '', self._sfs)
                    sp_epithet_w = self.pdf.get_string_width(sp_epithet + ' ')
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + sp_genus_w +\
                                    sp_sign_w, self.goto(self._ln))
                    self.pdf.cell(0, 0, sp_epithet)
                    spw = sp_epithet_w + sp_sign_w + sp_genus_w
                else:
                    self.pdf.set_font('DejaVubi', '', self._sfs)
                    spw = self.pdf.get_string_width(sp)
                    self.pdf.cell(0, 0, sp)
                # --------- End of smart conf. and aff. printing...

                if ir:
                    self.pdf.set_font('DejaVu', '', self._sfs)
                    irw = self.pdf.get_string_width(ir)
                    iauthw = self.pdf.get_string_width(iauth)
                    self.pdf.set_font('DejaVubi', '', self._sfs)
                    iepw = self.pdf.get_string_width(iep)

                    if spw + 2 + spaw > label_width:
                        self._ln += 1
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, auth)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spaw + 2,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, ir)
                        self.pdf.set_font('DejaVubi', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spaw + irw + 4,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iep)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spaw + irw + iepw + 6,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, iauth)
                        cur_cell_width = spaw + irw + iepw + 6 + iauthw
                    elif spw + 2 + spaw + irw > label_width:
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, auth)
                        self._ln += 1
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, ir)
                        self.pdf.set_font('DejaVubi', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + irw + 2,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iep)
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + irw + iepw + 4,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iauth)
                        cur_cell_width = irw + 4 + iepw + iauthw

                    elif spw + 2  + spaw + irw + iepw > label_width:
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, auth)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + spaw + 4,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, ir)

                        self._ln += 1

                        self.pdf.set_font('DejaVubi', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iep)

                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + iepw + 2,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iauth)
                        cur_cell_width = 2 + iepw + iauthw

                    elif spw + 4 + spaw + irw + iepw + iauthw > label_width:
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, auth)

                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + spaw + 4,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, ir)

                        self.pdf.set_font('DejaVubi', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + spaw + 6 + irw,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iep)

                        self._ln += 1

                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, iauth)
                        cur_cell_width = iauthw

                    else:
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, auth)

                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + spaw + 4,
                                        self.goto(self._ln))
                        self.pdf.cell(0, 0, ir)
                        self.pdf.set_font('DejaVubi', '', self._sfs)
                        self.pdf.set_xy(
                            BRYOPHYTE_LEFT_MARGIN + spw + spaw + 6 + irw,
                            self.goto(self._ln))
                        self.pdf.cell(0, 0, iep)
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.set_xy(
                            BRYOPHYTE_LEFT_MARGIN + spw + spaw + 8 + irw + iepw,
                            self.goto(self._ln))
                        self.pdf.cell(0, 0, iauth)
                        cur_cell_width = spw + 8 + irw +iepw + spaw + iauthw
                else:
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + spw + 2,
                                self.goto(self._ln))
                    fline = []
                    sline = []
                    if spaw + spw + 2 > label_width:
                        for word in auth.split():
                            if self.pdf.get_string_width(' '.join(fline + [word])) + spw + 2 <= label_width:
                                fline.append(word)
                            else:
                                sline.append(word)
                    else:
                        fline = auth.split()
                    self.pdf.set_font('DejaVu', '', self._sfs)
                    self.pdf.cell(0, 0, ' '.join(fline))
                    cur_cell_width = spw + 2 + self.pdf.get_string_width(' '.join(fline))
                    if sline:
                        self._ln += 1
                        self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                                        self.goto(self._ln))
                        self.pdf.set_font('DejaVu', '', self._sfs)
                        self.pdf.cell(0, 0, ' '.join(sline))
                        cur_cell_width = self.pdf.get_string_width(' '.join(sline))

                if _note or (dethistory and mainind == 1) or len(identifiedby) > 1:
                    _note = _note.strip()
                    if len(identifiedby) > 1 and mainind > 1:
                        if _note and identifiedby[0] != identifiedby[mainind - 1]:
                            # UPDATE: Temporary removed, revision needed...
                            # if _note[-1] in [';', '.', ',']:
                            #     _note = _note[:-1]
                            if identifiedby[mainind-1].strip():
                                _note += '; '
                                _note += 'det. ' + translit(identifiedby[mainind - 1], 'ru', reversed=True)
                        elif identifiedby[0] != identifiedby[mainind - 1]:
                            if  identifiedby[mainind-1].strip():
                                _note += 'Det. ' + translit(identifiedby[mainind - 1], 'ru', reversed=True)
                    if dethistory and mainind == 1:
                        if _note:
                            # UPDATE: Temporary removed, revision needed...
                            #if _note[-1] in [';', '.', ',']:
                            #    _note = _note[:-1]
                            _note += '; '
                        histlines = []
                        for hist_item in dethistory:
                            histline = translit(hist_item['identifiedby'], 'ru', reversed=True) + ': '
                            if hist_item['identified']:
                                histline += '(' + hist_item['identified'] + ') '
                            histline += ('<i>{}</i>'.format(hist_item['species']['species']) if hist_item['species']['species'] else '') + \
                            (' ' + hist_item['species']['spauth'] if hist_item['species']['spauth'] else '') + \
                            (' ' + hist_item['species']['infra_rank'] if hist_item['species']['infra_rank'] else '') +\
                            (' ' + '<i>{}</i>'.format(hist_item['species']['infra_epithet']) if hist_item['species']['infra_epithet'] else '') +\
                            ' ' + hist_item['species']['infra_authorship']
                            histlines.append(histline)
                        _note +=  'ID history: ' + '; '.join(histlines)
                    if _note.strip():
                        self.pdf.set_font('DejaVu', '', self._nnfs)
                        _y = self.pdf.get_y()
                        _x = self.pdf.get_x()
                        self.pdf.set_xy(
                            BRYOPHYTE_LEFT_MARGIN + cur_cell_width + 1,
                            _y - 1)
                        self.pdf.cell(0, 0, '(' + str(addind) + ')')
                        addinfo.append([addind, _note.strip()])
                        addind += 1
                        self.pdf.set_xy(_x, _y)
                self._ln += 1

            self.pdf.set_font('DejaVu', '', self._sfs)
            self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN,
                            self.goto(self._ln))

            if collected:
                leg_info = 'Leg. ' + translit(collected, 'ru', reversed=True)
            else:
                leg_info = ''

            if coldate:
                leg_info += ' (%s)' % coldate

            latlon_info = ''

            if latitude:
                latlon_info += 'Lat.: ' + lat_repr(latitude) + ' '

            if longitude:
                latlon_info += 'Lon.: ' + lon_repr(longitude) + ' '

            if altitude:
                latlon_info += ' Alt.: %s m a.s.l.' % translit(altitude, 'ru', reversed=True)

            if (latitude or longitude or altitude) and gpsbased:
                latlon_info += ' [GPS-based]'

            if identifiedby:
                det_info = 'Det. ' + translit(identifiedby[0], 'ru', reversed=True)
                if detdate:
                    det_info += ' (%s)' % detdate
            else:
                det_info = ''

            self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
            self.pdf.set_font('DejaVubi', '', self._sfs)
            self.pdf.multi_cell(label_width,
                                self._lh, smartify_language(country, lang='en'))
            self.pdf.set_font('DejaVu', '', self._sfs)



            pos_info = '. '.join([x.strip() for x in [smartify_language(region, lang='en'),
                                               smartify_language(district, lang='en'),
                                               latlon_info] if x])

            self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA)

            self.smarty_print(pos_info, self._lh,
                              left_position=BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA,
                              first_indent=0,
                              right_position=BRYOPHYTE_LEFT_MARGIN + label_width,
                              font_size=self._sfs)

            # TODO: Comments should be removed !
            # self.pdf.multi_cell(label_width -
            #                     BRYOPHYTE_MARGIN_EXTRA, self._lh, pos_info)
            if note.strip():
                if note.strip()[-1] == '.':
                    _aux = ' '
                else:
                    _aux = '. '
            else:
                _aux = ' '
            main_info = _aux.join([x.strip() for x in [smartify_language(note, lang='en'),
                                     smartify_language(place, lang='en')
                                     ] if x])

            self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA)
            if main_info:
                self.smarty_print(main_info, self._lh,
                              left_position=BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_MARGIN_EXTRA,
                              first_indent=0,
                              right_position=BRYOPHYTE_LEFT_MARGIN + label_width,
                              font_size=self._sfs)

            # TODO: Comments should be removed!
            # self.pdf.multi_cell(label_width -
            #                     BRYOPHYTE_MARGIN_EXTRA, self._lh, main_info)

            # check if the block above is overlapped with the barcode
            if self.pdf.get_y() >= (DEFAULT_PAGE_HEIGHT - BARCODE_ITEM_HEIGHT - 11):
                resize_required.append(True)

            self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
            if leg_info:
                self.pdf.set_font('DejaVu', '', self._sfs)
                resize_required.append(
                    self.check_resize_required(
                        self.pdf.get_string_width(leg_info),
                        barcode_width))
                self.pdf.multi_cell(label_width, self._lh,
                                leg_info)

            self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
            if det_info:
                self.pdf.set_font('DejaVu', '', self._sfs)
                resize_required.append(
                    self.check_resize_required(self.pdf.get_string_width(det_info),
                                               barcode_width))
                self.pdf.multi_cell(label_width,
                                    self._lh, det_info)

            if addinfo:
                self.pdf.set_font('DejaVu', '', self._nnfs)
                self.pdf.set_x(BRYOPHYTE_LEFT_MARGIN)
                _y = self.pdf.get_y()
                self.pdf.line(BRYOPHYTE_LEFT_MARGIN, _y,
                              BRYOPHYTE_LEFT_MARGIN + BRYOPHYTE_LINE_LENGTH, _y)
                _y += 4
                for ind, _note in addinfo:
                    self.pdf.set_font('DejaVu', '', self._nnfs)
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN, _y - 1)
                    self.pdf.cell(0, 0, '(' + str(ind) + ')')
                    self.pdf.set_xy(BRYOPHYTE_LEFT_MARGIN + 5, _y - 2)
                    self.pdf.set_font('DejaVu', '', self._nfs)
                    resize_required.append(
                        self.check_resize_required(
                            self.pdf.get_string_width(_note),
                            barcode_width))
                    self.smarty_print(_note, self._lh * 0.6,
                                      left_position=BRYOPHYTE_LEFT_MARGIN + 5,
                                      first_indent=0,
                                      right_position=BRYOPHYTE_LEFT_MARGIN + label_width - 4,
                                      font_size=self._nfs)
                    # TODO: Comments should be removed;
                    # self.pdf.multi_cell(label_width - 4,
                    #                     self._lh * 0.6, _note)
                    _y = self.pdf.get_y()
                    _y += 3


            if ((self.pdf.get_y() < DEFAULT_PAGE_HEIGHT) or (self._sfs < BRYOPHYTE_MIN_FSIZE)) and not any(resize_required):
                done = True
            else:
                self._sfs -= 0.25

            # Barcode insertion
            self.put_barcode(acronym, itemid, institute,
                                DEFAULT_PAGE_WIDTH - barcode_width - BRYOPHYTE_LEFT_MARGIN,
                                DEFAULT_PAGE_HEIGHT - 15)

    def generate_labels(self, labels):
        for label in labels:
            self.generate_label(**label)
            if label != labels[-1]:
                self.pdf.add_page()


if __name__ == '__main__':
    def test_bryophyte():
        test_pars = {'allspecies': [('Genus specimen%s'%x, 'auth%s'%x, 'subsp%s'%x,
                                     'long_subspecies_name%s'%x, 'iauthorhip%s'%x, '<i>Note</i> what about <b>sdf</b> '*7)
                         for x in map(str, range(3))],
                     'coldate': '20 Jul 2000',
                     'latitude': '12.1232',
                     'longitude': '-43.243212',
                     'place': 'Unknown  은신문',
                     'country': 'Russia',
                     'region': 'Just test data',
                     'collected': '12 Jan 2018',
                     'altitude': '1100',
                     'identifiedby': ['Kislov', 'Firsov', 'Anotonov'],
                     'number': '12315',
                     'itemid': '144',
                     'fieldid': 'fox-3',
                     'acronym': 'VBGI',
                     'institute': 'Botanical Garden Institute',
                     'note': 'Th<ig>is</ig> spe<b>ciem</b>en <i>never</i> <i>been</i> collected, be アプリ明朝 '*2,
                     'detdate': '13 Feb 2018 - 13 Feb 2018 -13 Feb 2018',
                     'district': 'Dirty place behind in the yard',
                     'gpsbased': 'True',
                     'dethistory': [],
                     'type_status': 'HOLOTYPUS'}
        p = PDF_BRYOPHYTE()
        labels= []
        for ind,label in enumerate(range(4)):
            tp = test_pars.copy()
            tp['fieldid'] += str(ind)
            labels.append(tp)
        p.generate_labels(labels)
        p.create_file('bryophyte_label.pdf')


    def test_barcode():
        my = BARCODE()
        my.put_barcode('VBGI', 1231231, 10, 10)
        my.create_file('barcode.pdf')


    def test_fpdf_bold():
        pdf = StyledPDF()
        pdf.add_font('sazanami-mincho', '', 'sazanami-mincho.ttf', uni=True)
        pdf.set_margins(5, 5, 5)
        pdf.set_auto_page_break(0, 0)
        pdf.add_page()
        pdf.set_font('sazanami-mincho', '', 12)
        pdf.cell(0, 0, 'アプリ明朝')
        pdf.set_font('sazanami-mincho', '', 12)
        pdf.output('boldtest.pdf', dest='F')

    def test_smarty_cell():
        pdf = PDF_DOC()
        pdf.smarty_print('s<b>a<i>m</i>p</b>le <i>t</i>ext <b>oa </b>' * 15, 20, left_position=20,
                     first_indent=30, right_position=100)
        pdf.create_file('sm.pdf')

    test_bryophyte()







