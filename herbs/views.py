# from django.shortcuts import render
# 
# # Create your views here.
# from dal import autocomplete
# 
# from .models import Family, Genus
# 
# 
# class FamilyAutocomplete(autocomplete.Select2QuerySetView):
# 
#     def get_queryset(self):
#         if not self.request.user.is_authenticated():
#             return Family.objects.none()
#         qs = Family.objects.all()
#         if self.q:
#             qs = qs.filter(name__istartswith=self.q)
# 
#         return qs
# 
# 
# class GenusAutocomplete(autocomplete.Select2QuerySetView):
# 
#     def get_queryset(self):
#         if not self.request.user.is_authenticated():
#             return Family.objects.none()
#         qs = Genus.objects.all()
#         if self.q:
#             qs = qs.filter(name__istartswith=self.q)
# 
#         return qs
