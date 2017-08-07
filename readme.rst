===============================================
Herbarium Management App with Multiuser support
===============================================

This web application provides multiuser 
and distributed access for 
manipulating (creating, editing, updating, deleting, i.e. basic CRUD-operations)
digital herbarium records with 
flexible permission management possibilities.

It is built on top of the Django Web Framework.

Features
--------

* automatic label generation (as a pdf-file);
* automatic QR-code embedding;
* label's barcode generation;
* per-user permission management;
* arbitrary number of herbarium groups;
* flexible per-group permission management;
* HTTP API: a service for query automatization allowing easy integration with
  Python/R-based environments for data evaluation;
 

Docs
----

- Basic search features
  http://botsad.ru/herbarium/docs/en/search_basics.html
- Public HTTP API:
  http://botsad.ru/herbarium/docs/en/http_api.html
- Making search queries using Python:
  https://nbviewer.jupyter.org/github/VBGI/herbs/blob/master/herbs/docs/tutorial/Python/en/Python.ipynb
- Making search queries using R:
  https://nbviewer.jupyter.org/github/VBGI/herbs/blob/master/herbs/docs/tutorial/R/en/R.ipynb


Where is it used?
-----------------

http://botsad.ru/herbarium/


Author
------
Dmitry E. Kislov (kislov@easydan.com)

