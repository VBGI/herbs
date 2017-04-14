# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from .forms import SearchForm
from django.conf import settings

class PrintHerbitemObjects(CMSPluginBase):
    model = CMSPlugin
    name = _(u"Отображение гербарных образцов")
    render_template = "render_herb_plugin.html"

    def render(self, context, instance, placeholder):
        context.update({'searchform': SearchForm(),
                        'herbitem_personal_url': settings.HERBS_HERBITEM_PAGE
                        })
        return context

plugin_pool.register_plugin(PrintHerbitemObjects)
