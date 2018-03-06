#coding: utf-8

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from geoposition.fields import GeopositionField
from django.core.exceptions import PermissionDenied
from .utils import  _smartify_dates

SIGNIFICANCE = (('aff.', 'affinis'),
                ('cf.', 'confertum')
                )




class BasicNameMixin(object):

    def get_basic_name(self):
        if self.species:
            genus_name = self.species.genus.name
            species_name = self.species.name
            siglevel = self.significance + ' ' if self.significance else ''
            name = capfirst(genus_name) + ' ' + siglevel + species_name
            return name
        else:
            return 'No species name'

class HerbItemMixin(models.Model, BasicNameMixin):
    '''
    Common item properties
    '''
    BIOMORPHS = (('D', 'Development stage partly'),
                 ('G', 'Life form')
                 )


    TYPE_STATUSES = (('H', 'HOLOTYPUS'),
                     ('I', 'ISOTYPUS'),
                     ('P', 'PARATYPUS'),
                     ('L', 'LECTOTYPUS')
                     )

    species = models.ForeignKey('Species', on_delete=models.SET_NULL, null=True,
                                verbose_name=_('вид'), related_name='herbitem')

    short_note = models.CharField(max_length=300, default='', blank=True,
                                  verbose_name=_('Примечание к виду'))

    type_status = models.CharField(max_length=1, blank=True, null=True,
                                   choices=TYPE_STATUSES,
                                   verbose_name=_('типовой статус'))

    significance = models.CharField(max_length=5, default='',
                                    blank=True, choices=SIGNIFICANCE,
                                    verbose_name=_('сходство'), help_text=_('степень сходства: aff. или cf.'))

    # item specific codes (used in the herbarium store)
    itemcode = models.CharField(max_length=15, default='', null=True,
                                verbose_name=_('код образца'),
                                blank=True,
                                help_text=_('заполняется куратором гербария'))
    fieldid = models.CharField(max_length=20, default='',
                               verbose_name=_('полевой код'),
                               help_text=_('заполняется сборщиком'),
                               blank=True)

    acronym = models.ForeignKey('HerbAcronym', on_delete=models.SET_NULL,
                                verbose_name=_('Акроним'),
                                blank=True, null=True)

    # -------- position -------------
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True,
                                blank=True, verbose_name=_('страна'))
    region = models.CharField(default='', blank=True, max_length=150,
                              verbose_name=_('регион'))
    district = models.CharField(default='', blank=True, max_length=150,
                                verbose_name=_('район'))
    detailed = models.CharField(default='', max_length=600, blank=True,
                                verbose_name=_('место сбора'),
                                help_text=_('локализация, экоусловия'))

    # -------- Geolocation, precision ------------
    coordinates = GeopositionField(verbose_name=_('координаты'), blank=True)
    altitude = models.CharField(default='', blank=True, max_length=50,
                                verbose_name=_('высота'),
                                help_text=_('высота над уровнем моря в метрах'))

    gpsbased = models.BooleanField(default=False, verbose_name=_('GPS-Based'),
                                   help_text=_('получены ли измерения при помощи GPS, отметьте, если да'))

    # Collection items
    collectedby = models.CharField(max_length=500, default='', blank=True,
                                   verbose_name=_('коллектор(ы)'))
    collected_s = models.DateField(blank=True, verbose_name=_('начало сбора'),
                                   null=True)
    collected_e = models.DateField(blank=True, verbose_name=_('конец сбора'),
                                   null=True)
    identifiedby = models.CharField(max_length=500, default='', blank=True,
                                    verbose_name=_('определил(и)'))
    identified_s = models.DateField(blank=True,
                                    verbose_name=_('начало определения'),
                                    null=True)
    identified_e = models.DateField(blank=True,
                                    verbose_name=_('конец определения'),
                                    null=True)

    devstage = models.CharField(max_length=1, default='', null=True, blank=True,
                                verbose_name=_('Биоморф. статус'),
                                choices=BIOMORPHS)

    subdivision = models.ForeignKey('Subdivision', null=True, blank=True,
                                    verbose_name=_('подрзадел гербария'))


    note = models.CharField(max_length=1000, blank=True, default='')

    uhash =  models.CharField(blank=True, default='',
                              max_length=32, editable=False)

    has_images = models.TextField(editable=False, null=True)

    created = models.DateField(auto_now_add=True, verbose_name=_('создан'))
    updated = models.DateField(auto_now=True, verbose_name=_('сохранен'))
    createdby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='+',
                                  editable=False, verbose_name=_('создатель'))
    updatedby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='+',
                                  editable=False, verbose_name=_('обновил'))
    public = models.BooleanField(default=False, verbose_name=_('опубликовано'))

    def __unicode__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        if self.species:
            return ' '.join([self.get_basic_name(), self.species.authorship,
                             self.species.get_infra_rank_display(),
                             self.species.infra_epithet,
                             self.species.infra_authorship]).strip()
        else:
            return "Object #%s (The species isn't defined)" % self.pk
    get_full_name.short_description = _('название вида')

    @property
    def colldate(self):
        return _smartify_dates(self)

    @property
    def detdate(self):
        return _smartify_dates(self, prefix='identified')


    class Meta:
        abstract = True


@python_2_unicode_compatible
class Subdivision(models.Model):
    name = models.CharField(max_length=300, blank=True, default='',
                            verbose_name=_('название подраздела'))
    description = models.CharField(max_length=1000, blank=True, default='',
                                   verbose_name=_('описание'))
    allowed_users = models.CharField(max_length=1000, default='',blank=True,
                                     verbose_name=_('пользователи'))

    parent = models.ForeignKey('self', null=True, blank=True,
                               verbose_name=_('родительский раздел'),
                               related_name='child')
    def __str__(self):
        return self.name

    def get_all_children(self):
        result = list()
        result.append(self)
        for c in Subdivision.objects.filter(parent=self):
            _r = c.get_all_children()
            if 0 < len(_r):
                result.extend(_r)
        return result

    class Meta:
        ordering = ('name',)
        verbose_name = _('подраздел')
        verbose_name_plural = _('подразделы')


@python_2_unicode_compatible
class Country(models.Model):
    """Base class  for Country"""
    name_ru = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)
    def __str__(self):
        return u'{}|{}'.format(self.name_ru, self.name_en)

    class Meta:
        ordering = ('name_ru',)
        verbose_name = _('страна')
        verbose_name_plural = _('страны')



@python_2_unicode_compatible
class SpeciesSynonym(models.Model):
    json_content = models.TextField(default='', editable=False)
    string_content = models.TextField(default='', editable=False)
    rebuild_scheduled = models.BooleanField(default=True, editable=False)

    def __str__(self):
        return self.string_content or self.json_content

    class Meta:
        verbose_name = _('Синоним вида')
        verbose_name_plural = _('Синонимы видов')



@python_2_unicode_compatible
class HerbAcronym(models.Model):
    name = models.CharField(max_length=10, default='', blank=True,
                            verbose_name=_('название'))
    institute = models.CharField(max_length=300, default='', blank=True,
                                 verbose_name=_('институт'))
    address = models.CharField(max_length=100, default='', blank=True,
                               verbose_name=_('адрес'))
    allowed_users = models.CharField(max_length=1000, default='', blank=True,
                                     verbose_name=_('пользователи'))
    logo = models.FileField(blank=True, null=True, verbose_name=_('эмблема'),
                            upload_to='herbs/logos')
    url = models.URLField(blank=True, default='http://botsad.ru', verbose_name=_('вебсайт организации'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('акроним гербария')
        verbose_name_plural = _('акронимы гербария')

    def __str__(self):
        return u'{}:{}'.format(self.name, self.institute)


class DetHistory(models.Model, BasicNameMixin):
    herbitem = models.ForeignKey('HerbItem', blank=False,
                                 related_name='dethistory')
    identifiedby = models.CharField(max_length=500, default='', blank=True,
                                    verbose_name=_('определил(и)'))
    identified_s = models.DateField(blank=True,
                                    verbose_name=_('начало определения'),
                                    null=True)
    identified_e = models.DateField(blank=True,
                                    verbose_name=_('конец определения'),
                                    null=True)
    species = models.ForeignKey('Species', blank=True, null=True,
                                verbose_name=_('вид'))
    significance = models.CharField(max_length=5, default='', null=True,
                                    blank=True, choices=SIGNIFICANCE,
                                    verbose_name=_('сходство'), help_text=_('степень сходства: aff. или cf.'))
    class Meta:
        verbose_name = _('переопределение')
        verbose_name_plural = _('переопределения')


class Additionals(models.Model, BasicNameMixin):
    herbitem = models.ForeignKey('HerbItem', blank=False,
                                 related_name='additionals')
    identifiedby = models.CharField(max_length=500, default='', blank=True,
                                    verbose_name=_('определил(и)'))
    identified_s = models.DateField(blank=True,
                                    verbose_name=_('валиден с'),
                                    null=True)
    identified_e = models.DateField(blank=True,
                                    verbose_name=_('валиден по'),
                                    null=True)
    species = models.ForeignKey('Species', blank=True, null=True,
                                verbose_name=_('вид'))
    significance = models.CharField(max_length=5, default='', null=True,
                                    blank=True, choices=SIGNIFICANCE,
                                    verbose_name=_('сходство'), help_text=_('степень сходства: aff. или cf.'))
    note = models.CharField(max_length=300, blank=True, default='',
                            verbose_name=_('примечение'))

    class Meta:
        verbose_name = _('Дополнительные виды')
        verbose_name_plural = _('Дополнительные виды')


class TaxonMixin(models.Model):
    name = models.CharField(max_length=70, default='',
                            verbose_name=_('название'))
    authorship = models.CharField(max_length=250, blank=True, default='',
                                        verbose_name=_('авторство'))
    def __str__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        if self.name:
            return self.name + ((' ' + self.authorship) if self.authorship else '')
        else:
            return 'Noname taxon #%s' % self.pk

    class Meta:
        ordering = ('name',)
        abstract = True

@python_2_unicode_compatible
class Family(TaxonMixin):
    class Meta:
        verbose_name = _('семейство')
        verbose_name_plural = _('семейства')

    def get_full_name(self):
        return super(Family, self).get_full_name()
    get_full_name.short_description = _('название семейства')


@python_2_unicode_compatible
class Genus(TaxonMixin):
    family = models.ForeignKey(Family, related_name='genus', null=True,
                               blank=False)
    gcode = models.CharField(max_length=6, default='',
                             verbose_name=_('De la Torre ID'),
                             blank=True)
    def get_full_name(self):
        return super(Genus, self).get_full_name()
    get_full_name.short_description = _('название рода')

    class Meta:
        verbose_name = _('род')
        verbose_name_plural = _('рода')


@python_2_unicode_compatible
class Species(TaxonMixin):
    SP_STATUSES = (('A', 'Approved'),
                   ('P', 'From plantlist'),
                   ('N', 'Recently added'),
                   ('D', 'Deleted')
                   )
    INFRA_RANKS = (('V', 'var.'),
                   ('S', 'subsp.'),
                   ('F',  'f.'),
                   ('P', 'subf.'),
                   ('W', 'subvar.'),
                   ('G', 'subg.')
                   )
    genus = models.ForeignKey(Genus, null=True, blank=False,
                              verbose_name=_('род'),
                              related_name='species')

    infra_rank  = models.CharField(choices=INFRA_RANKS, blank=True, default='',
                                   verbose_name=_("подвидовой ранг"),
                                   max_length=1)
    infra_epithet = models.CharField(max_length=100, default='', blank=True,
                                     verbose_name=_('подвидовой эпитет'))
    infra_authorship = models.CharField(max_length=100, default='', blank=True,
                                        verbose_name=_('автор подвидового эпитета'))
    status = models.CharField(max_length=1, default=SP_STATUSES[2][0], choices=SP_STATUSES,
                              blank=False, verbose_name=_('cтатус'))
    synonym = models.ForeignKey('self', null=True, blank=True, verbose_name=_('cиноним'), related_name='synrel')
    updated = models.DateField(auto_now=True, verbose_name=_('изменен'), blank=True)

    def get_full_name(self):
        if not self.infra_rank:
            return ' '.join([capfirst(self.genus.name),
                              super(Species, self).get_full_name()])
        else:
            return ' '.join([capfirst(self.genus.name), self.name,
                              self.authorship,
                              self.get_infra_rank_display(),
                              self.infra_epithet,
                              self.infra_authorship]).strip()

    get_full_name.short_description = _('название вида')

    class Meta:
        verbose_name = _('вид')
        verbose_name_plural = _('виды')
        permissions = (('can_change_status', 'Can change taxon status'),)


class HerbItem(HerbItemMixin):
    user = models.ForeignKey(get_user_model(),
                             blank=True, null=True, related_name='+',
                             editable=False)

    latitude = models.FloatField(blank=True, null=True, editable=False)
    longitude = models.FloatField(blank=True, null=True, editable=False)

    class Meta:
        abstract = False
        verbose_name = _('гербарный образeц')
        verbose_name_plural = _('гербарные образцы')
        ordering = ['-created']
        permissions = (('can_set_publish', _('может публиковать и назначать код')),
                       ('can_see_additionals', _('видит дополнительные виды')),
                       ('can_set_code', _('может назначать гербарный код')),
                       )

    def get_absolute_url(self):
        return  'http:' + getattr(settings, 'HERBS_HERBITEM_PAGE') + '%s' % self.id

    def delete(self, *args, **kwargs):
        if self.public:
            raise PermissionDenied(_('нельзя удалить опубликованные объекты'))
        else:
            super(HerbItem, self).delete(*args, **kwargs)



class HerbCounter(models.Model):
    herbitem = models.ForeignKey(HerbItem, null=True, blank=True,
                                 related_name='herbcounter')
    count = models.PositiveIntegerField(default=0)
