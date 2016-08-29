#coding: utf-8

import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from geoposition.fields import GeopositionField
import pandas as pd

from .utils import (NECESSARY_DATA_COLUMNS, evluate_herb_dataframe, smart_unicode,
                   create_safely, get_authorship_string)


# Geopositionfield need to be imported!
# where image files will be uploaded 
# HERB_IMG_UPLOADPATH = 'herbimgs/%Y/%m/%d/'
# HERB_DATA_UPLOADPATH = 'herbdata/%Y/%m/%d/'
UPLOAD_MAX_FILE_SIZE = 5 * 10 ** 6 # 5 MB defualt

_fields_to_copy = ('family', 'genus',  'species',
                   'gcode', 'itemcode', 'identified_s',
                   'identified_e', 'identifiedby',
                   'collected_s', 'collected_e',
                   'country', 'region', 'district',
                   'coordinates', 'ecodescr',
                   'detailed', 'height', 'note')



class HerbItemMixin(models.Model):
    '''
    Common item properties
    '''
    
    family = models.ForeignKey('Family',
                               on_delete=models.SET_NULL,
                               null=True,
                               verbose_name=_('семейство'))
    genus = models.ForeignKey('Genus', on_delete=models.SET_NULL, null=True,
                              verbose_name=_('род'))
    species = models.ForeignKey('Species', on_delete=models.SET_NULL, null=True,
                                verbose_name=_('вид'))

    # item specific codes (used in the herbarium store)
    gcode = models.CharField(max_length=10, default='', verbose_name=_('код подраздела'))
    itemcode = models.CharField(max_length=15, default='', verbose_name=_('код образца'))

    # position
    country = models.CharField(default='', blank=True, max_length=255, verbose_name=_('страна'))
    region = models.CharField(default='', blank=True, max_length=150, verbose_name=_('регион'))
    district = models.CharField(default='', blank=True, max_length=150, verbose_name=_('район'))
    detailed = models.CharField(default='', max_length=300, blank=True, verbose_name=_('дополнительно'))
    place = GeopositionField(verbose_name=_('координаты'), blank=True)
    coordinates = models.CharField(default='', blank=True, verbose_name=_('Координаты (строка)'), max_length=30)
    height = models.CharField(default='', blank=True, max_length=50, verbose_name=_('высота'))

    # Ecological factors
    ecodescr = models.CharField(max_length=300, default='', blank=True, verbose_name=_('экоусловия'))

    # Collection items
    collectedby = models.CharField(max_length=500, default='', blank=True, verbose_name=_('сборщики')) 
    collected_s = models.DateField(blank=True, verbose_name=_('начало сбора'), null=True)
    collected_e = models.DateField(blank=True, verbose_name=_('конец сбора'), null=True)
    identifiedby = models.CharField(max_length=500, default='', blank=True, verbose_name=_('определил(и)'))
    identified_s = models.DateField(blank=True, verbose_name=_('начало определения'), null=True)
    identified_e = models.DateField(blank=True, verbose_name=_('конец определения'), null=True)

    note = models.CharField(max_length=1000, blank=True, default='')

    uhash =  models.CharField(blank=True, default='', max_length=32, editable=False)

    
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

    def save(self, *args, **kwargs):
        self.collectedby = self.collectedby.strip()
        self.identifiedby = self.identifiedby.strip()
        self.gcode = self.gcode.strip()
        self.itemcode = self.itemcode.strip()
        super(HerbItemMixin, self).save(*args, **kwargs)

    def __unicode__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        authors = [x for x in SpeciesAuthorship.objects.filter(species=self.species,
                                                               species__genus=self.genus).order_by('priority')]
        if len(authors) > 0:
            author_string = ' ' + get_authorship_string(authors)
        else:
            author_string = ''
        return (capfirst(self.genus.name) if self.genus else '') +\
            ' ' + (self.species.name if self.species else '') + author_string
    get_full_name.short_description = _('полное имя вида')

    class Meta:
        abstract = True
        verbose_name = _('гербарный образeц')
        verbose_name_plural = _('гербарные образцы')
        ordering = ('family', 'genus', 'species')    
 

@python_2_unicode_compatible
class AuthorshipMixin(models.Model):
    author = models.ForeignKey('Author',
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True,
                               verbose_name=_('автор'))
    priority = models.IntegerField(default=0, verbose_name=_('приоритет'))

    def __str__(self):
        return self.author.name + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name) if self.author else ''

    class Meta:
        verbose_name = _('авторство')
        verbose_name_plural = _('авторство')    
        abstract = True

@python_2_unicode_compatible
class Author(models.Model):
    '''Genus/Family/Species inventor
    '''
    name = models.CharField(max_length=150, default='', verbose_name=_('автор'))

    def save(self, *args, **kwargs):
        self.name = self.name.lower().strip()
        super(Author, self).save(*args, **kwargs)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return capfirst(self.name) if self.name else ''

    class Meta:
        verbose_name = _('автор')
        verbose_name_plural = _('авторы')


class FamilyAuthorship(AuthorshipMixin):
    family = models.ForeignKey('Family', on_delete=models.CASCADE, verbose_name=_('семейство'))

class GenusAuthorship(AuthorshipMixin):
    genus = models.ForeignKey('Genus', on_delete=models.CASCADE,
                              verbose_name=_('род'))

@python_2_unicode_compatible
class Family(models.Model):
    name = models.CharField(max_length=30, default='',
                            verbose_name=_('название'))
    authorship = models.ManyToManyField(Author, blank=True, null=True,
                                        through=FamilyAuthorship,
                                        verbose_name=_('авторство'))

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Family, self).save(*args, **kwargs)

    def __str__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        authors = [x for x in  FamilyAuthorship.objects.filter(family=self).order_by('priority')]
        if len(authors) > 0:
            author_string = ' ' + get_authorship_string(authors)
        else:
            author_string = ''
        return self.name + author_string
    get_full_name.short_description = _('полное имя семейства')

    class Meta:
        verbose_name = _('название семейства')
        verbose_name_plural = _('названия семейств')    


@python_2_unicode_compatible
class Genus(models.Model):
    name = models.CharField(max_length=30, default='', verbose_name=_('название'))
    authorship = models.ManyToManyField(Author, blank=True, null=True, through=GenusAuthorship, verbose_name=_('авторство'))

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Genus, self).save(*args, **kwargs)

    def __str__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        authors = [x for x in  GenusAuthorship.objects.filter(genus=self).order_by('priority')]
        if len(authors) > 0:
            author_string = ' ' + get_authorship_string(authors)
        else:
            author_string = ''
        return self.name + author_string
    get_full_name.short_description = _('полное имя рода')

    class Meta:
        verbose_name = _('название рода')
        verbose_name_plural = _('названия родов')



class SpeciesAuthorship(AuthorshipMixin):
    species = models.ForeignKey('Species', on_delete=models.CASCADE,
                                 verbose_name=_('вид'))
 
@python_2_unicode_compatible
class Species(models.Model):
    name = models.CharField(max_length=30, default='', verbose_name=_('название вида'))
    genus = models.ForeignKey(Genus, null=False, blank=False, verbose_name=_('род'))
    authorship = models.ManyToManyField(Author, blank=True, null=True,
                                        through=SpeciesAuthorship,
                                        verbose_name=_('авторство'))
    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Species, self).save(*args, **kwargs)

    def __str__(self):
        return capfirst(self.get_full_name())

    class Meta:
        verbose_name = _('название вида')
        verbose_name_plural = _('названия видов')

    def get_full_name(self):
        authors = [x for x in SpeciesAuthorship.objects.filter(species=self).order_by('priority')]
        if len(authors) > 0:
            author_string = ' ' + get_authorship_string(authors)
        else:
            author_string = ''
        return self.genus.name + ' ' + self.name + author_string
    get_full_name.short_description = _('полное имя вида')



class HerbItem(HerbItemMixin):
    pass
        
    
class PendingHerbs(HerbItemMixin):
    checked = models.BooleanField(default=False, verbose_name=_('проверено'))
    err_msg = models.TextField(blank=True, default='')

    class Meta:
        abstract = False
        verbose_name = _('загруженный гербарный образец') 
        verbose_name_plural = _('загруженные гербарные образцы')


@python_2_unicode_compatible
class LoadedFiles(models.Model):
    datafile = models.FileField(upload_to=settings.HERB_DATA_UPLOADPATH, verbose_name=_('Файл'))
    created = models.DateField(auto_now_add=True, verbose_name=_('загружен'))
    status = models.BooleanField(default=False, editable=False, verbose_name=_('cтатус'))
    createdby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='+',
                                  editable=False, verbose_name=_('создатель'))

    def __str__(self):
        return os.path.basename(self.datafile.name) 

    class Meta:
        verbose_name = _('Файл с данными')
        verbose_name_plural = _('Файлы с данными')
        ordering = ('created', 'status', 'createdby')


@python_2_unicode_compatible
class ErrorLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, default='', editable=False)
    
    def __str__(self):
        return self.message
    
    class Meta:
        verbose_name = _('Ошибки загрузки файлов')
        verbose_name_plural = _('Ошибки загрузки файлов')
        ordering = ('-created', 'message')


@receiver(post_save, sender=LoadedFiles)
def load_datafile(sender, instance, **kwargs):
    # Trying
    herbfile = instance.datafile
    filename, file_extension = os.path.splitext(herbfile.name)
    fsize = herbfile.size
    if fsize > UPLOAD_MAX_FILE_SIZE:
        ErrorLog.objects.create(message=u'Превышен допустимый размер файла (%s байт), файл: %s' % (fsize, filename))
        return
    if ('xls' in file_extension) or ('xlsx' in file_extension):
        try:
            data = pd.read_excel(os.path.join(settings.MEDIA_ROOT, herbfile.name))
        except:
            ErrorLog.objects.create(message=u'Не удалось прочитать файл %s' % (herbfile.name,))
            return
    elif 'csv' in file_extension:
        try:
            data = pd.read_csv(os.path.join(settings.MEDIA_ROOT, herbfile.name))
        except:
            ErrorLog.objects.create(message=u'Не удалось прочитать файл %s' % (herbfile.name,))
            return
    else:
        ErrorLog.objects.create(message=u'Неизвестный формат файла %s; Поддерживаемые форматы xls, csv.' % (herbfile.name,))
        return
    ccolumns = set(data.columns)
    ncolumns = set(NECESSARY_DATA_COLUMNS)
    res = ncolumns - ccolumns
    if len(res) > 0:
        fields = ','.join(['<%s>'%item for item in res])
        errlog = ErrorLog(message=u'Поля %s отсутствуют в файле %s' % (fields, herbfile.name))
        errlog.save()
        return
    result, errors = evluate_herb_dataframe(data)
    for err in errors:
        if err:
            ErrorLog.objects.create(message=';'.join([str(item) for item in err]))
    if len(result) > 0:
        indd=0
        for item in result:
            familyobj = create_safely(Family, ('name',), (item['family'],))
            if not familyobj.authorship.all().exists():
                for ind, auth in item['family_auth'][1]:
                    authorobj = create_safely(Author, ('name',), (auth,))
                    create_safely(FamilyAuthorship, ('author', 'priority', 'family'), 
                              (authorobj, ind, familyobj), postamble='')
                
            genusobj = create_safely(Genus, ('name',), (item['genus'],))
            if not genusobj.authorship.all().exists():
                for ind, auth in item['genus_auth'][1]:
                    authorobj = create_safely(Author, ('name',), (auth,))
                    create_safely(GenusAuthorship, ('author', 'priority', 'genus'), 
                              (authorobj, ind, genusobj), postamble='')

            speciesobj = create_safely(Species, ('name', 'genus'),
                                       (item['species'].strip().lower(), genusobj),
                                       postamble='')
            if not speciesobj.authorship.all().exists():
                for ind, auth in item['species_auth'][1]:
                    authorobj = create_safely(Author, ('name',), (auth,))
                    create_safely(SpeciesAuthorship, ('author', 'priority', 'species'), 
                              (authorobj, ind, speciesobj), postamble='')
            query_fields = {'family':familyobj,
                            'genus':genusobj,
                            'species':speciesobj,
                            'gcode':item['gcode'],
                            'itemcode':item['itemcode'],
                            'identified_s':item['identified'],
                            'identified_e':item['identified'],
                            'identifiedby':item['identifiedby'],
                            'collectedby':item['collectedby'],
                            'collected_s':item['collected'],
                            'collected_e':item['collected'],
                            'country':item['country'],
                            'region':item['region'],
                            'district':item['district'],
                            'coordinates':item['coordinates'],
                            'ecodescr':item['ecology'],
                            'detailed':item['detailed'],
                            'height':item['height'],
                            'note':item['note']}
            if not PendingHerbs.objects.filter(**query_fields).exists():
                pobj = PendingHerbs.objects.create(**query_fields)
                if HerbItem.objects.filter(itemcode=pobj.itemcode).exists():
                    pobj.err_msg += u'Запись с номером %s уже существует;' % pobj.itemcode
                    pobj.save()
            indd+=1
            