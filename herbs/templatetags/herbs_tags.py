# -*- coding: utf-8 -*-

from django import template
from django.conf import settings
from django.utils import translation
from ..models import Country


register = template.Library()

DELIMITER = settings.HERBS_BILINGUAL_DELIMITER

CYRILLIC_SYMBOLS = set(u"абвгдезиклмнопрстуфхцЦъыьАБВГДЕЗИКЛМНОПРСТУФХЪЫЬ")


@register.filter
def smart_language(value):
    if isinstance(value, Country):
        if translation.get_language() == 'ru':
            return value.name_ru
        else:
            return value.name_en
    try:
        value = str(value)
    except UnicodeEncodeError:
        pass
    if DELIMITER in value:
        if value.count(DELIMITER) > 1:
            return value
        a, b = value.split(DELIMITER)
        a = a.strip()
        b = b.strip()
        if len(a) == 0 or len(b) == 0:
            return value
        _cya = len(set(a).intersection(CYRILLIC_SYMBOLS))
        _cyb = len(set(b).intersection(CYRILLIC_SYMBOLS))
        if _cya > _cyb:
            ru_value = a
            en_value = b
        elif _cya < _cyb:
            ru_value = b
            en_value = a
        else:
            return value
        if translation.get_language() == 'ru':
            return ru_value
        else:
            return en_value
    else:
        return value
