from django.db import models
from django.conf import settings


class MetaDataMixin(models.Model):
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    createdby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True)
    updatedby = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True)
    class Meta:
        abstract = True 


class Author(models.Model):
    name = models.CharField(max_length=150, default='')


class OrderedAuthor(models.Model):
    author = models.ForeignKey(Author,
                               null=True,
                               on_delete=models.SET_NULL,
                               blank=True)
    priority = models.IntegerField(default=0)


class Family(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)


class Genus(models.Model):
    name = models.CharField(max_length=30, default='')
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)

class Species(models.Model):
    name = models.CharField(max_length=30, default='')


class HerbItem(MetaDataMixin):
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True)
    genus = models.ForeignKey(Genus, on_delete=models.SET_NULL, null=True)
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True)
    authorship = models.ManyToManyField(OrderedAuthor, blank=True, null=True)
    