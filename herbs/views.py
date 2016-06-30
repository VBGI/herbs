from django.shortcuts import render
from django.views.generic import ListView
 
 
from .models import Family, Genus, HerbItem
from .forms import SearchForm, ExtendedSearchForm


class ShowHerbitems(ListView):
    model = HerbItem
    template_name = 'herbs/herbitemtable.html'
    context_object_name = 'herbitem'
    paginate_by = 30

    def get_queryset(self):
        if not  self.request.is_ajax():
            return HerbItem.objects.all()
        page = self.request.POST.get('page','1')
        
        # basic search components
        family = request.POST.get('family','')
        genus = request.POST.get('genus','')
        species = request.POST.get('species','')
        
        # extended search components
        collectors = request.POST.get('collectors','')
        country = request.POST.get('country','')
        region = request.POST.get('region','')
        sortfields = request.POST.get('sortfield','default')
        gcode = request.POST.get('gcode','')
        itemcode = request.POST.get('itemcode','')
        
        object_filtered = HerbItem.objects.all()
        if family:
            object_filtered = object_filtered.filter(family__name__icontains=family)

        if genus:
            object_filtered = object_filtered.filter(genus__name__icontains=genus)
        
        if species:
            object_filtered = object_filtered.filter(species__name__icontains=species)

        if gcode:
            object_filtered = object_filtered.filter(gcode=gcode)
        if itemcode:
            object_filtered = object_filtered.filter(itemcode=itemcode)
        
        return object_filtered
 

