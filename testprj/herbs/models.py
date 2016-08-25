#coding: utf-8
import os
from imagekit.models import ProcessedImageField
from django.utils.text import capfirst
from django.db import models
from django.conf import settings
from geoposition.fields import GeopositionField
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import gettext as _
from django.utils.functional import cached_property
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import NECESSARY_DATA_COLUMNS


# Geopositionfield need to be imported!

# where image files will be uploaded 
# HERB_IMG_UPLOADPATH = 'herbimgs/%Y/%m/%d/'
# HERB_DATA_UPLOADPATH = 'herbdata/%Y/%m/%d/'

def get_authorship_string(authors):
    result = ''
    howmany = len(authors)
    if howmany > 1:
        inside = [item for item in authors[:howmany-1]]
    else: 
        inside = None
    # order by priority : the older is put into bracets
    if inside:
        result += ' (%s) ' % (' '.join([x.get_name() for x in inside]), )
    if howmany:
        result += ' %s' % authors[howmany-1].get_name()
    return capfirst(result)


class MetaDataMixin(models.Model):
    '''
    Common item properties
    '''
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
    
    class Meta:
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
        return self.name
    
    def get_name(self):
        return capfirst(self.name)

    class Meta:
        verbose_name = _('автор')
        verbose_name_plural = _('авторы')


@python_2_unicode_compatible
class FamilyAuthorship(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True,
                               verbose_name=_('автор'))
    family = models.ForeignKey('Family', on_delete=models.CASCADE, verbose_name=_('семейство'))
    priority = models.IntegerField(default=0, verbose_name=_('приоритет'), 
                                   help_text=_('низкий приоритет  соответствует более старой номенклатуре'))

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name)

    class Meta:
        verbose_name = _('авторство')
        verbose_name_plural = _('авторство')


@python_2_unicode_compatible
class GenusAuthorship(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True,
                               verbose_name=_('автор'))
    genus = models.ForeignKey('Genus', on_delete=models.CASCADE,
                              verbose_name=_('род'))
    priority = models.IntegerField(default=0, verbose_name=_('приоритет'))

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name)

    class Meta:
        verbose_name = _('авторство')
        verbose_name_plural = _('авторство')


@python_2_unicode_compatible
class SpeciesAuthorship(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True,
                               verbose_name=_('автор'))
    herbitem = models.ForeignKey('HerbItem', on_delete=models.CASCADE,
                                 verbose_name=_('гербарный образец'))
    priority = models.IntegerField(default=0, verbose_name=_('приоритет'))

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name)

    class Meta:
        verbose_name = _('авторство')
        verbose_name_plural = _('авторство')


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


@python_2_unicode_compatible
class Species(models.Model):
    name = models.CharField(max_length=30, default='')
    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Species, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('название вида')
        verbose_name_plural = _('названия видов')


class HerbSnapshot(models.Model):
    image = ProcessedImageField(upload_to=settings.HERB_IMG_UPLOADPATH,
                                      format='JPEG',
                                      options={'quality': 90})
    models.ForeignKey('HerbItem', null=True, on_delete=models.SET_NULL, related_name='snapshots')
    date = models.DateTimeField(auto_now=True)


@python_2_unicode_compatible
class HerbItem(MetaDataMixin):
    family = models.ForeignKey(Family,
                               on_delete=models.SET_NULL,
                               null=True,
                               verbose_name=_('семейство'))
    genus = models.ForeignKey(Genus, on_delete=models.SET_NULL, null=True,
                              verbose_name=_('род'))
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True,
                                verbose_name=_('вид'))
    authorship = models.ManyToManyField(Author, blank=True,
                                        null=True, through=SpeciesAuthorship,
                                        verbose_name=_('авторство'))

    # item specific codes (used in the herbarium store)
    gcode = models.CharField(max_length=10, default='', verbose_name=_('код подраздела'))
    itemcode = models.CharField(max_length=15, default='', verbose_name=_('код образца'))

    # position
    country = models.CharField(default='', blank=True, max_length=255, verbose_name=_('страна'))
    region = models.CharField(default='', blank=True, max_length=150, verbose_name=_('регион'))
    district = models.CharField(default='', blank=True, max_length=150, verbose_name=_('район'))
    detailed = models.CharField(default='', max_length=300, blank=True, verbose_name=_('дополнительно'))
    place = GeopositionField(verbose_name=_('координаты'), blank=True)

    # Ecological factors
    ecodescr = models.CharField(max_length=300, default='', blank=True, verbose_name=_('экоусловия'))

    # Collection items
    collectors = models.CharField(max_length=500, default='', blank=True, verbose_name=_('сборщики')) 
    collected_s = models.DateField(blank=True, verbose_name=_('начало сбора'))
    collected_e = models.DateField(blank=True, verbose_name=_('конец сбора'))
    identifiers = models.CharField(max_length=500, default='', blank=True, verbose_name=_('определил(и)'))
    identified_s = models.DateField(blank=True, verbose_name=_('начало определения'))
    identified_e = models.DateField(blank=True, verbose_name=_('конец определения'))

    def save(self, *args, **kwargs):
        self.collectors = self.collectors.strip()
        self.identifiers = self.identifiers.strip()
        self.gcode = self.gcode.strip()
        self.itemcode = self.itemcode.strip()
        super(HerbItem, self).save(*args, **kwargs)

    def __str__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        authors = [x for x in  SpeciesAuthorship.objects.filter(herbitem=self).order_by('priority')]
        if len(authors) > 0:
            author_string = ' ' + get_authorship_string(authors)
        else:
            author_string = ''
        return capfirst(self.genus.name) + ' ' + self.species.name + author_string
    get_full_name.short_description = _('полное имя вида')
    
    class Meta:
        abstract = False
        verbose_name = _('гербарный образeц')
        verbose_name_plural = _('гербарные образцы')
        ordering = ('family', 'genus', 'species')


@python_2_unicode_compatible    
class PendingHerbs(HerbItem):
    checked = models.BooleanField(default=False, verbose_name=_('проверено'))
    err_msg = models.TextField(blank=True, default=True)

    class Meta:
        db_table = 'herbs_loadpendingherbs' # TODO: Should be changed!!!
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
        return self.datafile.name
    
    class Meta:
        verbose_name = _('Ошибки загрузки файлов')
        verbose_name_plural = _('Ошибки загрузки файлов')


@receiver(post_save, sender=LoadedFiles)
def load_datafile(sender, instance, **kwargs):
    herbfile = instance.datafile.open(mode='rb')
    # Trying
    filename, file_extension = os.path.splitext(herbfile.name)
    if 'xls' in file_extension:
        data = pd.read_xls(herbfile.name) # TODO: if error, try catch... 
        ccolumns = set(data.columns)
        ncolumns = set(NECESSARY_DATA_COLUMNS)
        res = ncolumns - ccolumns
        if len(res) > 0:
            fields = ','.join(['<%s>'%item for item in res])
            errlog = ErrorLog(message='Поля %s отсутствуют в файле %s' % (fields, filename))
            errlog.save()
            return
    elif 'zip' in file_extension:
        # Evluation of a zip file
        pass
         
     
#     tempdir = tempfile.mkdtemp()
#     zipfile = ZipFile()
        