#coding: utf-8

import os
from django.conf import settings
from django.utils.translation import ugettext as _
from appconf import AppConf

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, 'fixtures/herbaria.dat'), 'r') as f:
    KNOWN_HERBARIA = f.read()

class HerbsAppConf(AppConf):

    SPECIES_SIGNIFICANCE = (('aff.', 'affinis'),
                            ('cf.', 'confertum')
                            )

    # Allowed tags when the herbitem is showed
    ALLOWED_TAGS = ('b', 'i')

    # Bulk changes settings
    ALLOWED_FOR_BULK_CHANGE = ('region', 'district', 'collectedby',
                               'identifiedby', 'detailed', 'note')
    MAX_BULK_CONTAIN_CHARS = 5

    # Tracking changes feature
    TRACKED_FIELDS = ('collectedby', 'identifiedby', 'region', 'district', 'species')
    NOTIFICATION_MAILS = ('kislov@easydan.com', 'vabakalin@gmail.com',
                          'pimenova_garden@mail.ru', 'stupnikovat@yandex.ru') # allowed emails
    NOTIFICATION_USERS = ('scidam', 'bryophyte', 'labcrypto', 'pimenova',
                          'stupnikova') # user's allowed for email sending

    # Objects edited by these user's aren't tracked by the system
    EXCLUDED_FROM_NOTIFICATION = ('', ) # User's excluded from notification;

    #The number of days to remember when forming pop-up hints
    DAYS_TO_REMEMBER = 180

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

    APPROVED_SPECIES_FREEZE = 30 #in days

    SEARCHFORM_ORDERING_FIELDS = [('species__name', _(u'Видовой эпитет')),
                                  ('collected_s', _(u'Дата сбора')),
                                  ('identified_s', _(u'Дата определения')),
                                  ('id', _(u'Порядковый номер')),
                                  ('collectedby', _(u'Собрали')),
                                  ('identifiedby', _(u'Определили')),
                                  ('country', _(u'Страна')),
                                  ('herbcounter__count', _(u'Число просмотров'))
                                  ]

    SOURCE_IMAGE_PATHS = None
    SOURCE_IMAGE_FILE = '/home/scidam/tmp/herbsnapshots/herbimages.txt'
    SOURCE_IMAGE_FILE_LIST = 'http://herbstatic.botsad.ru/herbimages.txt'
    SOURCE_IMAGE_FILE_LIST_TIMEOUT = 5
    SOURCE_IMAGE_THUMB = 'ts'
    SOURCE_IMAGE_URL = 'http://herbstatic.botsad.ru/snapshots'
    SOURCE_IMAGE_VIEWER = 'http://herbstatic.botsad.ru/'
    SOURCE_IMAGE_URL_RELATIVE = 'snapshots'
    SOURCE_IMAGE_LIST_KEY = 'herbimages_key'
    SOURCE_IMAGE_LIST_KEY_TIMEOUT = 5
    SOURCE_IMAGE_PATTERN = r'^[A-Z]{1,10}\d+(_?\d{1,2})\.([tT][iI][fF]{1,2}$|[jJ][pP][eE]?[gG]$)'
    IMAGE_SESSION_NAME = 'herbimage'
    IMAGE_SOURCE_TMP = '/home/scidam/tmp/herbsnapshots'


    INDEX_HERBARIORUM = KNOWN_HERBARIA

    class Meta:
        prefix = 'herbs'
