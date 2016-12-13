#coding: utf-8

#import os

from django.conf import settings
from django.db import models
#from django.db.models.signals import post_save, pre_delete
#from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from geoposition.fields import GeopositionField
#import pandas as pd
from .utils import  _smartify_dates



UPLOAD_MAX_FILE_SIZE = 5 * 10 ** 6 # 5 MB defualt

_fields_to_copy = ('family', 'genus',  'species',
                   'itemcode', 'identified_s',
                   'identified_e', 'identifiedby',
                   'collected_s', 'collected_e',
                   'country', 'region', 'district',
                   'coordinates', 'ecodescr',
                   'detailed', 'altitude', 'note')


class HerbItemMixin(models.Model):
    '''
    Common item properties
    '''
    BIOMORPHS = (('D', 'Development stage'),
                 ('G', 'Growth form')
                 )

    species = models.ForeignKey('Species', on_delete=models.SET_NULL, null=True,
                                verbose_name=_('вид'))

    # item specific codes (used in the herbarium store)
    itemcode = models.CharField(max_length=15, default='', null=True,
                                verbose_name=_('код образца'),
                                blank=True)

    acronym = models.ForeignKey('HerbAcronym', on_delete=models.SET_NULL,
                                verbose_name='Acronym',
                                blank=True, null=True)

    devstage = models.CharField(max_length=1, default='', null=True, blank=True,
                                verbose_name=_('Биоморф. статус'),
                                choices=BIOMORPHS)

    # position
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True,
                                blank=True, verbose_name=_('страна'))
    region = models.CharField(default='', blank=True, max_length=150,
                              verbose_name=_('регион'))
    district = models.CharField(default='', blank=True, max_length=150,
                                verbose_name=_('район'))
    detailed = models.CharField(default='', max_length=300, blank=True,
                                verbose_name=_('дополнительно'))
    coordinates = GeopositionField(verbose_name=_('координаты'), blank=True)
    altitude = models.CharField(default='', blank=True, max_length=50,
                                verbose_name=_('высота'))

    # Ecological factors
    ecodescr = models.CharField(max_length=300, default='', blank=True,
                                verbose_name=_('экоусловия'))

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

    note = models.CharField(max_length=1000, blank=True, default='')

    uhash =  models.CharField(blank=True, default='',
                              max_length=32, editable=False)

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
        return self.genus.name + ' ' + self.species.get_full_name()
    get_full_name.short_description = _('полное имя вида')

    @property
    def colldate(self):
        return _smartify_dates(self)

    @property
    def detdate(self):
        return _smartify_dates(self)


    class Meta:
        abstract = True


@python_2_unicode_compatible
class Country(models.Model):
    """Base class  for Country"""
    name_ru = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)
    def __str__(self):
        return '{}|{}'.format(self.name_ru, self.name_en)

    class Meta:
        ordering = ('name_ru',)
        verbose_name = _('страна')
        verbose_name_plural = _('страны')


@python_2_unicode_compatible
class HerbAcronym(models.Model):
    name = models.CharField(max_length=10, default='', blank=True)
    institute = models.CharField(max_length=300, default='', blank=True)
    address = models.CharField(max_length=100, default='', blank=True)
    allowed_users = models.CharField(max_length=1000, default='', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('акроним гербария')
        verbose_name_plural = _('акронимы гербария')

    def __str__(self):
        return u'{}:{}|allowed:{}'.format(self.name, self.institute, self.allowed_users)



class HerbImage(models.Model):
    TYPE_CHOICES = (('H', 'Изображение гербария'),
                    ('P', 'Изображение места сбора'))
    user = models.ForeignKey(get_user_model(), blank=True, null=True, related_name='+')
    image = models.ImageField(upload_to="herbimages/%Y/%m/%d/", blank=True)
    type = models.CharField(max_length=1,
                            blank=False,
                            default=TYPE_CHOICES[0][0],
                            choices=TYPE_CHOICES)
    created = models.DateField(auto_now_add=True, verbose_name=_('создан'))
    updated = models.DateField(auto_now=True, verbose_name=_('изменен'))
    herbitem = models.ForeignKey('HerbItem', blank=False, related_name='images')

    class Meta:
        ordering = ('updated', )
        verbose_name = _('изображение')
        verbose_name_plural = _('изображения')


class TaxonMixin(models.Model):
    name = models.CharField(max_length=30, default='',
                            verbose_name=_('название'))
    authorship = models.CharField(max_length=250, blank=True, default='',
                                        verbose_name=_('авторство'))
    def __str__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
       return self.name + ((' ' + self.authorship) if self.authorship else '')

    class Meta:
        ordering = ('name',)
        abstract = True

@python_2_unicode_compatible
class Family(TaxonMixin):
    class Meta:
        verbose_name = _('название семейства')
        verbose_name_plural = _('названия семейств')

    def get_full_name(self):
        return super(Family, self).get_full_name()
    get_full_name.short_description = _('полное имя семейства')


@python_2_unicode_compatible
class Genus(TaxonMixin):
    family = models.ForeignKey(Family, related_name='genus', null=True,
                               blank=False)
    gcode = models.CharField(max_length=6, default='',
                             verbose_name=_('De la Torre ID'),
                             blank=True)
    def get_full_name(self):
        return super(Genus, self).get_full_name()
    get_full_name.short_description = _('полное имя рода')

    class Meta:
        verbose_name = _('название рода')
        verbose_name_plural = _('названия родов')


@python_2_unicode_compatible
class Species(TaxonMixin):
    genus = models.ForeignKey(Genus, null=True, blank=False,
                              verbose_name=_('род'),
                              related_name='species')
    def get_full_name(self):
        res = super(Species, self).get_full_name()
        return self.genus.name +' ' + res
    get_full_name.short_description = _('полное имя вида')

    class Meta:
        verbose_name = _('название вида')
        verbose_name_plural = _('названия видов')


class HerbItem(HerbItemMixin):
    user = models.ForeignKey(get_user_model(),
                             blank=True, null=True, related_name='+',
                             editable=False)

    class Meta:
        abstract = False
        verbose_name = _('гербарный образeц')
        verbose_name_plural = _('гербарные образцы')
        ordering = ['-created']

# ------------------------ This functionalyty doesn't needed ----------------
#class PendingHerbs(HerbItemMixin):
#    checked = models.BooleanField(default=False, verbose_name=_('проверено'))
#    err_msg = models.TextField(blank=True, default='')
#
#    class Meta:
#        abstract = False
#        verbose_name = _('загруженный гербарный образец')
#        verbose_name_plural = _('загруженные гербарные образцы')
#
#
#@python_2_unicode_compatible
#class LoadedFiles(models.Model):
#    datafile = models.FileField(upload_to=settings.HERB_DATA_UPLOADPATH, verbose_name=_('Файл'))
#    created = models.DateField(auto_now_add=True, verbose_name=_('загружен'))
#    status = models.BooleanField(default=False, editable=False, verbose_name=_('cтатус'))
#    createdby = models.ForeignKey(settings.AUTH_USER_MODEL,
#                                  on_delete=models.SET_NULL,
#                                  null=True, blank=True, related_name='+',
#                                  editable=False, verbose_name=_('создатель'))
#
#    def __str__(self):
#        return os.path.basename(self.datafile.name)
#
#    class Meta:
#        verbose_name = _('Файл с данными')
#        verbose_name_plural = _('Файлы с данными')
#        ordering = ('created', 'status', 'createdby')
#
#
#@python_2_unicode_compatible
#class ErrorLog(models.Model):
#    created = models.DateTimeField(auto_now_add=True)
#    message = models.TextField(blank=True, default='', editable=False)
#    who = models.CharField(default='', blank=True, max_length=255)
#
#    def __str__(self):
#        return self.message
#
#    class Meta:
#        verbose_name = _('Ошибки загрузки файлов')
#        verbose_name_plural = _('Ошибки загрузки файлов')
#        ordering = ('-created', 'message')
#
#
#@receiver(pre_delete, sender=LoadedFiles)
#def loadedfiles_delete(sender, instance, **kwargs):
#    try:
#        instance.datafile.delete(False)
#    except IOError:
#        pass
#
#
## NOTE: THIS FUNCTIONALITY DOESN"T NEEDED
#@receiver(post_save, sender=LoadedFiles)
#def load_datafile(sender, instance, **kwargs):
#    # Trying
#    herbfile = instance.datafile
#    filename, file_extension = os.path.splitext(herbfile.name)
#    fsize = herbfile.size
#    if fsize > UPLOAD_MAX_FILE_SIZE:
#        ErrorLog.objects.create(message=u'Превышен допустимый размер файла (%s байт), файл: %s' % (fsize, filename), who=filename)
#        return
#    if ('xls' in file_extension) or ('xlsx' in file_extension):
#        try:
#            data = pd.read_excel(os.path.join(settings.MEDIA_ROOT, herbfile.name))
#        except:
#            ErrorLog.objects.create(message=u'Не удалось прочитать файл %s' % (herbfile.name,), who=filename)
#            return
#    elif 'csv' in file_extension:
#        try:
#            data = pd.read_csv(os.path.join(settings.MEDIA_ROOT, herbfile.name))
#        except:
#            ErrorLog.objects.create(message=u'Не удалось прочитать файл %s' % (herbfile.name,), who=filename)
#            return
#    else:
#        ErrorLog.objects.create(message=u'Неизвестный формат файла %s; Поддерживаемые форматы xls, csv.' % (herbfile.name,), who=filename)
#        return
#    ccolumns = set(data.columns)
#    ncolumns = set(NECESSARY_DATA_COLUMNS)
#    res = ncolumns - ccolumns
#    if len(res) > 0:
#        fields = ','.join(['<%s>'%item for item in res])
#        errlog = ErrorLog(message=u'Поля %s отсутствуют в файле %s' % (fields, herbfile.name), who=filename)
#        errlog.save()
#        return
#    result, errors = evluate_herb_dataframe(data)
#    for err in errors:
#        if err:
#            ErrorLog.objects.create(message=';'.join([str(item) for item in err]), who=filename)
#    if len(result) > 0:
#        indd = 0
#        for item in result:
#            familyobj = create_safely(Family, ('name',), (item['family'],))
#            if not familyobj.authorship.all().exists():
#                for ind, auth in item['family_auth'][1]:
#                    authorobj = create_safely(Author, ('name',), (auth,))
#                    create_safely(FamilyAuthorship, ('author', 'priority', 'family'),
#                              (authorobj, ind, familyobj), postamble='')
#
#            genusobj = create_safely(Genus, ('name', ), (item['genus'],))
#            if not genusobj.family:
#                genusobj.family = familyobj
#            if not genusobj.gcode:
#                genusobj.gcode = item['gcode']
#            genusobj.save()
#            if not genusobj.authorship.all().exists():
#                for ind, auth in item['genus_auth'][1]:
#                    authorobj = create_safely(Author, ('name',), (auth,))
#                    create_safely(GenusAuthorship, ('author', 'priority', 'genus'),
#                              (authorobj, ind, genusobj), postamble='')
#
#            speciesobj = create_safely(Species, ('name', 'genus'),
#                                       (item['species'].strip().lower(), genusobj),
#                                       postamble='')
#            if not speciesobj.authorship.all().exists():
#                for ind, auth in item['species_auth'][1]:
#                    authorobj = create_safely(Author, ('name',), (auth,))
#                    create_safely(SpeciesAuthorship, ('author', 'priority', 'species'),
#                              (authorobj, ind, speciesobj), postamble='')
#            query_fields = {'family': familyobj,
#                            'genus': genusobj,
#                            'species': speciesobj,
#                            'itemcode': item['itemcode'],
#                            'identified_s': item['identified'],
#                            'identified_e': item['identified'],
#                            'identifiedby': item['identifiedby'],
#                            'collectedby': item['collectedby'],
#                            'collected_s': item['collected'],
#                            'collected_e': item['collected'],
#                            'country': item['country'],
#                            'region': item['region'],
#                            'district': item['district'],
#                            'coordinates': item['coordinates'],
#                            'ecodescr': item['ecology'],
#                            'detailed': item['detailed'],
#                            'altitude': item['altitude'],
#                            'note': item['note'],
#                            }
#            if not PendingHerbs.objects.filter(**query_fields).exists():
#                pobj = PendingHerbs.objects.create(**query_fields)
#                if HerbItem.objects.filter(itemcode=pobj.itemcode).exists():
#                    pobj.err_msg += u'Запись с номером %s уже существует;' % pobj.itemcode
#                    pobj.save()
#            indd += 1