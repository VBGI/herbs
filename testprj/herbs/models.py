#coding: utf-8
from hashlib import md5
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

from .utils import NECESSARY_DATA_COLUMNS, evluate_herb_dataframe, smart_unicode


# Geopositionfield need to be imported!
# where image files will be uploaded 
# HERB_IMG_UPLOADPATH = 'herbimgs/%Y/%m/%d/'
# HERB_DATA_UPLOADPATH = 'herbdata/%Y/%m/%d/'
UPLOAD_MAX_FILE_SIZE = 5 * 10 ** 6 # 5 MB defualt

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


class AuthorshipMixin(models.Model):
    author = models.ForeignKey('Author',
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True,
                               verbose_name=_('автор'))
    priority = models.IntegerField(default=0, verbose_name=_('приоритет'))

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

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
        return self.name

    def get_name(self):
        return capfirst(self.name) if self.name else ''

    class Meta:
        verbose_name = _('автор')
        verbose_name_plural = _('авторы')


@python_2_unicode_compatible
class FamilyAuthorship(AuthorshipMixin):
    family = models.ForeignKey('Family', on_delete=models.CASCADE, verbose_name=_('семейство'))


@python_2_unicode_compatible
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
        print self.name
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

    uhash =  models.CharField(blank=True, default='', max_length=32, editable=False)

    def _hash(self):
        tohash = self.family.name +\
                 str(self.species) + self.country +\
                 self.region + self.district + self.detailed +\
                 self.ecodescr + self.collectedby + str(self.collected_s) +\
                 str(self.identified_s) + self.identifiedby
        return md5(tohash.encode('utf8')).hexdigest()

    def save(self, *args, **kwargs):
        self.collectedby = self.collectedby.strip()
        self.identifiedby = self.identifiedby.strip()
        self.gcode = self.gcode.strip()
        self.itemcode = self.itemcode.strip()
        self.uhash = self._hash()
        super(HerbItem, self).save(*args, **kwargs)

    def __str__(self):
        return capfirst(self.get_full_name())

    def get_full_name(self):
        print self.genus.name
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
    if 'xls' in file_extension:
        try:
            data = pd.read_excel(os.path.join(settings.MEDIA_ROOT, herbfile.name))
        except:
            ErrorLog.objects.create(message=u'Не удалось прочитать файл %s' % (herbfile.name,))
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
            if len(err) > 0:
                resmsg = ';'.join(err)
                ErrorLog.objects.create(message=resmsg)

        if len(result) > 0:
            # chekign hash for uniquess
            for item in result:
                familyobj, cc_ = Family.objects.get_or_create(name=item['family'])
                for ind, auth in item['family_auth'][1]:
                    authorobj, cc_ = Author.objects.get_or_create(name=auth) 
                    FamilyAuthorship.objects.get_or_create(author=authorobj,
                                                           priority=ind,
                                                           family=familyobj)

                genusobj, cc_ = Genus.objects.get_or_create(name=item['genus'])
                for ind, auth in item['genus_auth'][1]:
                    authorobj, cc_ = Author.objects.get_or_create(name=auth) 
                    GenusAuthorship.objects.get_or_create(author=authorobj,
                                                          priority=ind,
                                                          genus=genusobj)

                speciesobj, cc_ = Species.objects.get_or_create(name=item['species'],
                                                                genus=genusobj)
                for ind, auth in item['species_auth'][1]:
                    authorobj, cc_ = Author.objects.get_or_create(name=auth)
                    SpeciesAuthorship.objects.get_or_create(author=authorobj,
                                                            priority=ind,
                                                            species=speciesobj)
            pobj = PendingHerbs(family=familyobj,
                                genus=genusobj,
                                species=speciesobj,
                                gcode=item['gcode'],
                                itemcode=item['itemcode'],
                                identified_s=item['identified'],
                                identified_e=item['identified'],
                                identifiedby=item['identifiedby'],
                                collectedby=item['collectedby'],
                                collected_s=item['collected'],
                                collected_e=item['collected'],
                                country=item['country'],
                                region=item['region'],
                                district=item['district'],
                                coordinates=item['coordinates'],
                                ecodescr=item['ecology'],
                                detailed=item['detailed'],
                                height=item['height'])
            if HerbItem.objects.filter(itemcode=pobj.itemcode).exists():
                pobj.err_msg += 'Запись с номером %s уже существует;' % pobj.itemcode
            pobj.save()

        # Create items that are validated (primarily state)

        # data evaluation step
    elif 'zip' in file_extension:
        # Evluation of a zip file, do nothing .. yet
        pass
         
     
#     tempdir = tempfile.mkdtemp()
#     zipfile = ZipFile()
        