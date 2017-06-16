from django.conf import settings

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

    class Meta:
        prefix = 'herbs'
