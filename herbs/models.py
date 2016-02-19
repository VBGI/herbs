from imagekit.models import ProcessedImageField

from django.db import models
from django.conf import settings

# Geopositionfield need to be imported!

# where image files will be uploaded 
HERB_UPLOADPATH = 'herbimgs/'


class MetaDataMixin(models.Model):
    '''
    Common item properties
    '''
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    createdby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True)
    updatedby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True)
    public = models.BooleanField(default=False)
    class Meta:
        abstract = True 


class Author(models.Model):
    name = models.CharField(max_length=150, default='')


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


class Family(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super(Model, self).save(*args, **kwargs)

class Genus(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super(Model, self).save(*args, **kwargs)

class Species(models.Model):
    name = models.CharField(max_length=30, default='')
    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super(Model, self).save(*args, **kwargs)

class HerbSnapshot(models.Model):
    image = ProcessedImageField(upload_to=settings.HERB_UPLOADPATH,
                                      format='JPEG',
                                      options={'quality': 90})
    models.ForeignKey('HerbItem', null=True, on_delete=SET_NULL, related_name='snapshots')
    date = models.DateTimeField(auto_now=True)



class HerbItem(MetaDataMixin):
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True)
    genus = models.ForeignKey(Genus, on_delete=models.SET_NULL, null=True)
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True)
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)

    # item specific codes (used in the herbarium store)
    gcode = models.CharField(max_length=10, default='')
    itemcode = models.CharField(max_length=15, default='')

    # position
    country = models.CharField(default='', blank=True, max_length=2, choices)
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
        super(Model, self).save(*args, **kwargs)

