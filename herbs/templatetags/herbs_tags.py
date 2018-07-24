# -*- coding: utf-8 -*-

from django import template
from ..utils import smartify_language, translit
from ..models import Country
from django.utils import translation
from six import string_types
from django.conf import settings

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
def sanitize_tags(value):
    return value
    #TODO: remove all html tags from a string except some specific tags .