
from imagekit.models import ProcessedImageField
from django.utils.text import capfirst
from django.db import models
from django.conf import settings
from geoposition.fields import GeopositionField
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import gettext as _
from django.utils.functional import cached_property

# Geopositionfield need to be imported!

# where image files will be uploaded 
HERB_UPLOADPATH = 'herbimgs/%Y/%m/%d/'


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
    '''Genus/Family/Species inventor
    '''
    name = models.CharField(max_length=150, default='')

    def save(self, *args, **kwargs):
        self.name = self.name.lower().strip()
        super(Author, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_name(self):
        return capfirst(self.name)


@python_2_unicode_compatible
class FamilyAuthorship(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True)
    family = models.ForeignKey('Family', on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name)


@python_2_unicode_compatible
class GenusAuthorship(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True)
    genus = models.ForeignKey('Genus', on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name)


@python_2_unicode_compatible
class SpeciesAuthorship(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.CASCADE,
                               blank=True)
    herbitem = models.ForeignKey('HerbItem', on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return str(self.author) + (' %s' % self.priority if self.priority > 0 else '') 

    def get_name(self):
        return capfirst(self.author.name)


@python_2_unicode_compatible
class Family(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(Author, blank=True, null=True, through=FamilyAuthorship)

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


@python_2_unicode_compatible
class Genus(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(Author, blank=True, null=True, through=GenusAuthorship)
    
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
    authorship = models.ManyToManyField(Author, blank=True,
                                        null=True, through=SpeciesAuthorship)

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
        return capfirst(self.get_full_name())

    def get_full_name(self):
        authors = [x for x in  SpeciesAuthorship.objects.filter(herbitem=self).order_by('priority')]
        if len(authors) > 0:
            author_string = ' ' + get_authorship_string(authors)
        else:
            author_string = ''
        return capfirst(self.genus.name) + ' ' + self.species.name + author_string
    
