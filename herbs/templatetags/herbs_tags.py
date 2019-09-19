# -*- coding: utf-8 -*-

from django import template
from ..utils import smartify_language, translit
from ..models import Country
from django.utils import translation
from django.utils.encoding import smart_text
from six import string_types
from django.conf import settings
from bs4 import BeautifulSoup

register = template.Library()

@register.filter
def smart_language(value):
    if isinstance(value, Country):
        if translation.get_language() == 'ru':
            return value.name_ru
        else:
            return value.name_en
    return smartify_language(value)


@register.filter
def force_translit(value):
    if translation.get_language() != 'ru':
        if isinstance(value, string_types):
            return translit(value, 'ru', reversed=True)
    return value


@register.filter
def is_allowed_for_changing(name):
    return name in getattr(settings, 'HERBS_ALLOWED_FOR_BULK_CHANGE', tuple())


@register.filter
def add_point(value):
    if value.strip()[-1] == '.':
        return value
    else:
        return value + '.'


@register.filter(is_safe=True)
def sanitize(value):
    allowed_tags = getattr(settings, 'HERBS_ALLOWED_TAGS', ('b', 'i'))
    content = BeautifulSoup(value, 'html.parser')
    tags = [tag.name for tag in content.find_all()]
    for tag in [tag for tag in tags if tag not in allowed_tags]:
        for match in content.findAll(tag):
            match.unwrap()
    for match in content.find_all():
        for item in match.contents:
            fixed_text = unicode(item)
            if fixed_text.endswith(' '):
                item.replace_with(fixed_text[:-1] + '&nbsp;')
            if fixed_text.startswith(' '):
                item.replace_with('&nbsp;' + fixed_text[1:])
    return smart_text(str(content))
