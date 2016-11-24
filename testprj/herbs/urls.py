# -*- coding: utf-8 -*-

from django.conf.urls import *

from herbs.views import (get_item_data, advice_select, show_herbs,
                         make_label)

urlpatterns = patterns('',
   url(r'^gi/', get_item_data),
   url(r'^as/', advice_select),
   url(r'^sh/', show_herbs),
   url(r'^pdf/([,\d]{1,50})', make_label, name='herbiteminfo')
)
