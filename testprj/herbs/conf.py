from appconf import AppConf

class HerbsAppConf(AppConf):
    PAGINATION_COUNT = 100
    
    class Meta:
        prefix = 'herbs'