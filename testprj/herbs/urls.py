# -*- coding: utf-8 -*-

from django.conf.urls import *

urlpatterns = patterns('',
   url(r'^gi/', 'herbs.views.get_item_data'),
   url(r'^as/', 'herbs.views.advice_select'),
   url(r'^sh/', 'herbs.views.show_herbs'),
   url(r'^pdf/([,\d]+)', 'herbs.views.make_label')
)
