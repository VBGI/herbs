# -*- coding: utf-8 -*-

from django.conf.urls import *
from .views import get_item_data, show_herbs, advice_select

urlpatterns = patterns('',
   url(r'^gi/', get_item_data),
   url(r'^as/', advice_select),
   url(r'^sh/', show_herbs),
)