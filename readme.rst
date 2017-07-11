===============================================
Herbarium Management App with Multiuser support
===============================================

This web application provides multiuser 
and distributed access for 
manipulating (creating, editing, deleting) 
digital herbarium records with 
flexible permission management tools.

It is built on top of the Django Web Framework.

Features
--------

* automatic label generation (as a pdf-file);
* QR-code embegging;
* label's barcode generation;
* per-user permission management;
* arbitrary number of herbarium groups;
* HTTP API: a service for query automatization, allowing easy integration with 
  Python/R-based environments for data evaluations;
 

Docs
----

- Public HTTP API:
  https://github.com/VBGI/herbs/blob/master/herbs/docs/httpapi/en/http_api.rst
- Making search queries using Python:
  https://github.com/VBGI/herbs/blob/master/herbs/docs/tutorial/Python/en/Python.ipynb
- Making search queries using R:
  [isn't yet completed...]
  https://github.com/VBGI/herbs/blob/master/herbs/docs/tutorial/R/en/R.ipynb


Where is it used?
-----------------

http://botsad.ru/herbarium/


Author
------
Dmitry E. Kislov (kislov@easydan.com)

