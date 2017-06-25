# -*- coding: utf-8 -*-

from django import template
from ..utils import smartify_language

register = template.Library()


@register.filter
def smart_language(value):
   return smartify_language(value)

