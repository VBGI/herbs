
from imagekit.models import ProcessedImageField
from django.utils.text import capfirst

from django.db import models
from django.conf import settings
from geoposition.fields import GeopositionField
from django.utils.encoding import python_2_unicode_compatible

# Geopositionfield need to be imported!

# where image files will be uploaded 
HERB_UPLOADPATH = 'herbimgs/%Y/%m/%d/'


def get_taxonomy_string(obj, fieldname):
    result = obj.__dict__[fieldname]
    authors = obj.authorship.all().order_by('priority')
    howmany = authors.count()
    if authors.count() > 1:
        inside = [item for item in authors[:howmany-1]]
    else: 
        inside = None
    # order by priority : the older is put into bracets
    if inside:
        result += ' (%s) ' % (' '.join([str(x) for x in inside]), )
    if howmany:
        result += '%s' % str(authors[howmany-1])
    return result


class MetaDataMixin(models.Model):
    '''
    Common item properties
    '''
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    createdby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='+',
                                  editable=False)
    updatedby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='+',
                                  editable=False)
    public = models.BooleanField(default=False)
    class Meta:
        abstract = True 


@python_2_unicode_compatible
class Author(models.Model):
    '''Genus or Family inventor
    '''
    name = models.CharField(max_length=150, default='')

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super(Author, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrderedAuthor(models.Model):
    '''
    OrdereAuthor instances used to define priority of invention for the species/genus/family. 
    The lower priority, the older invention is made.
    '''
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.SET_NULL,
                               blank=True)
    priority = models.IntegerField(default=0)


@python_2_unicode_compatible
class Family(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Family, self).save(*args, **kwargs)

    def __str__(self):
        return get_taxonomy_string(self, 'name')


@python_2_unicode_compatible
class Genus(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Genus, self).save(*args, **kwargs)

    def __str__(self):
        return get_taxonomy_string(self, 'name')


@python_2_unicode_compatible
class Species(models.Model):
    name = models.CharField(max_length=30, default='')
    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super(Species, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class HerbSnapshot(models.Model):
    image = ProcessedImageField(upload_to=settings.HERB_UPLOADPATH,
                                      format='JPEG',
                                      options={'quality': 90})
    models.ForeignKey('HerbItem', null=True, on_delete=models.SET_NULL, related_name='snapshots')
    date = models.DateTimeField(auto_now=True)


@python_2_unicode_compatible
class HerbItem(MetaDataMixin):
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True)
    genus = models.ForeignKey(Genus, on_delete=models.SET_NULL, null=True)
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True)
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)

    # item specific codes (used in the herbarium store)
    gcode = models.CharField(max_length=10, default='')
    itemcode = models.CharField(max_length=15, default='')

    # position
    country = models.CharField(default='', blank=True, max_length=2)
    region = models.CharField(default='', blank=True, max_length=150)
    district = models.CharField(default='', blank=True, max_length=150)
    detailed = models.CharField(default='', max_length=300, blank=True)
    place = GeopositionField()

    # Ecological factors
    ecodescr = models.CharField(max_length=300, default='', blank=True)

    # Collection items
    collectors = models.CharField(max_length=500, default='', blank=True) 
    collected_s = models.DateField(blank=True)
    collected_e = models.DateField(blank=True)
    identifiers = models.CharField(max_length=500, default='', blank=True)
    identified_s = models.DateField(blank=True)
    identified_e = models.DateField(blank=True)

    def save(self, *args, **kwargs):
        self.collectors = self.collectors.strip()
        self.identifiers = self.identifiers.strip()
        self.gcode = self.gcode.strip()
        self.itemcode = self.itemcode.strip()
        super(HerbItem, self).save(*args, **kwargs)

    def __str__(self):
        return get_taxonomy_string(self, 'genus')
