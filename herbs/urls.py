# -*- coding: utf-8 -*-

from django.conf.urls import *

from .views import (get_item_data, advice_select, show_herbs,
                    make_label, show_herbitem, json_api,
                    make_barcodes, make_bryophyte_label,
                    upload_image, validate_image, bulk_changes
                    )
from . import init_herbs


init_herbs()

urlpatterns = patterns('',
   url(r'^gi/', get_item_data),
   url(r'^as/', advice_select),
   url(r'^sh/', show_herbs),
   url(r'^pdf/([,\d]{1,1500})', make_label, name='herbiteminfo'),
   url(r'^envpdf/([,\d]{1,1500})', make_bryophyte_label, name='herbitembryo'),
   url(r'^bars/([,\d]{1,1500})', make_barcodes, name='herbitembarcodes'),
   url(r'^[a-zA-Z]*(\d{1,15})', show_herbitem),
   url(r'^json/', json_api),
   url(r'^imload/', upload_image, name="image_uploader"),
   url(r'^valim/', validate_image, name="image_validator"),
   url(r'^change/', bulk_changes, name="change_herbitems")
                       )
