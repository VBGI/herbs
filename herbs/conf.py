#coding: utf-8

from django.conf import settings
from django.utils.translation import ugettext as _

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

    SEARCHFORM_ORDERING_FIELDS = [('species__name', _(u'Видовой эпитет')),
                                  ('collected_s', _(u'Дата сбора')),
                                  ('identified_s', _(u'Дата определения')),
                                  ('id', _(u'Порядковый номер')),
                                  ('collectedby', _(u'Собрали')),
                                  ('identifiedby', _(u'Определили')),
                                  ('country', _(u'Страна')),
                                  ('herbcounter__count', _(u'Число просмотров'))
                                  ]

    class Meta:
        prefix = 'herbs'
