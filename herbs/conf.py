#coding: utf-8

from django.conf import settings
from django.utils.translation import gettext as _

from appconf import AppConf


class HerbsAppConf(AppConf):
    PAGINATION_COUNT = 20
    AUTOSUGGEST_NUM_TO_SHOW = 50
    AUTOSUGGEST_NUM_ADMIN = 30
    AUTOSUGGEST_CHAR = 3
    HERBITEM_PAGE = '//botsad.ru/hitem/'

    ALLOWED_FIELDID_SYMB_IN_GET = 30
    ALLOWED_AUTHORSHIP_SYMB_IN_GET = 100
    ALLOWED_ITEMCODE_SYMB_IN_GET = 30

    JSON_API_SIMULTANEOUS_CONN = 2
    JSON_API_CONN_KEY_NAME = 'herbs_json_connections'
    JSON_API_CONN_KEY_FLAG = 'herbs_json_conn_flag'
    JSON_API_CONN_TIMEOUT = 3

    BILINGUAL_DELIMITER = "|"

    SEARCHFORM_ORDERING_FIELDS = [('species', _('Видовой эпитет')),
                                  ('collected_s', _('Дата сбора')),
                                  ('identified_s', _('Дата определения')),
                                  ('ID', _('Порядковый номер')),
                                  ('collectedby', _('Собрали')),
                                  ('identifiedby', _('Определили')),
                                  ('country', _('Страна')),
                                  ]

    class Meta:
        prefix = 'herbs'
