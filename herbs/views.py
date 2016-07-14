from django.shortcuts import render
from django.http import HttpResponse
 
 
from .models import Family, Genus, HerbItem
from .forms import SearchForm, ExtendedSearchForm

from django.template.loader import render_to_string



def showitem(request):
    objid = request.POST.get('objectid', '')
    result = ''
    if objid:
        try:
            hobj = HerbItem.objects.get(id=objid)
            result = render_to_string('herbitem.html', {'herbitem': hobj, error: ''})
        except HerbItem.DoesNotExists:
            result = render_to_string('herbitem.html', {'herbitem': None, error: 'Object not found'})
    return  HttpResponse(result) 


def showherbs(request):
    '''
    Answer on quries about herbs
    '''
    if request.is_ajax():
        
        # basic search components
        family = request.POST.get('family', '')
        genus = request.POST.get('genus', '')
        species = request.POST.get('species', '')
        gcode = request.POST.get('gcode', '')  # Search by internal code (assigned by this system)
        collectors = request.POST.get('collectors', '')
        country = request.POST.get('country', '')
        region = request.POST.get('region', '')

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
        
        # Form a herbs list according to request
        pass
    else:
        # Request isn't ajax
        pass




class ShowHerbitems(ListView):
    model = HerbItem
    template_name = 'herbs/herbitemtable.html'
    context_object_name = 'herbitem'
    paginate_by = 30

    def get_queryset(self):
        if not  self.request.is_ajax():
            return HerbItem.objects.all()
        page = self.request.POST.get('page','1')
        

        
        # extended search components
        sortfields = request.POST.get('sortfield', 'default')
        gcode = request.POST.get('gcode', '')
        itemcode = request.POST.get('itemcode', '')
        
        

        
        return object_filtered
 

