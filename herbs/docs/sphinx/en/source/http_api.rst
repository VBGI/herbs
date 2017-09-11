========================================
Digital Herbarium's HTTP-API Description
========================================

.. contents:: :local:

.. |---| unicode:: U+2014  .. em dash

.. |--| unicode:: U+2013   .. en dash


Intro
-----

This document describes HTTP-API (Application Programming Interface over HTTP protocol) used
to get access Digital Herbarium Database of the BGI.

HTTP-API works in read-only mode.
There is no way to make changes in the database using the API.


Description of HTTP request parameters
--------------------------------------

Only GET-requests are allowed when talking with the HTTP API service.
To establish connection with the service, one can use either HTTP or HTTPS protocols.

Requests with multiple parameters, e.g. `colstart=2016-01-01` and `collectedby=bak`,
are treated as components of `AND`-type queries:
in this example, all records collected
after `2016-01-01` and including `bak`
(case insensitive matching is performed)
as a sub-string of `Collectors` field of the herbarium record will be returned.

`OR`-type querying behavior can be emulated by a series of
consequent queries to the database and isn't natively implemented
in the current version of the HTTP API.

List of allowed GET-parameters:

- **family** |---| family name (matching condition: case insensitive, the same family name as provided);
- **genus** |---|  genus name (matching condition:  case insensitive, the same genus name as provided),
   note: if the value contradicts with the family name provided in the same request,
   an error will be returned;
- **species_epithet** |---| species epithet (matching condition:
  case insensitive, a sub-string of the record corresponding field);
- **place** |---|  place of collection (matching condition: case insensitive,
  a sub-string occurring in the one of listed fields: **Place**, **Region**, **District**, **Note**;);
- **collectedby** |---| collectors (matching condition: case insensitive, a sub-string of the record corresponding field);
  if the field's value is given in Cyrillic, search will be performed (additionally) on its transliterated copy;
- **identifiedby** |---| identifiers; (matching condition: case insensitive, a sub-string of the record corresponding field);
  if the field's value is given in Cyrillic, search will be performed (additionally) on its transliterated copy;
- **country** |---| country's name (matching condition: case insensitive, a sub-string of the record corresponding field);
- **colstart** |---| date when collection process of the herbarium object was started (yyyy-mm-dd);
- **colend** |---|  date when collection process of the herbarium object was finished (yyyy-mm-dd);
- **acronym** |---| acronym of the herbarium (matching condition:
  case insensitive, the same name as provided);
- **subdivision** |---| subdivision of the herbarium (matching condition:
  case insensitive, the same name as provided);
- **latl** |---| latitude lower bound, should be in (-90, 90);
- **latu** |---| latitude upper bound, should be in (-90, 90);
- **lonu** |---| longitude upper bound, should be in (-180, 180);
- **lonl** |---| longitude lower bound, should be in (-180, 180);
- **synonyms** |---| Boolean parameter, allowed values are `false` or `true`; absence of the parameter
  in GET-request is treated as its `false` value; `true` value (e.g. `synonyms=true`)
  tells the system to search records taking into account the table of species synonyms;
  *Note:* when performing search including known
  (known by the system) species synonyms one should provide
  both **genus** and **species_epithet** values,
  if only one of these is provided or both are leaved empty,
  a warning will be shown and the search condition will be ignored;
- **additionals** |---| Boolean parameter, allowed values are `false` or `true`;
  absence of the parameter in GET-request is treated as its `false` value;
  `true` value (e.g. `additionals=true`) tells the system to
  search within additional species (if such is provided);
  some herbarium records could include more than one species (such records referred as multispecies records);
- **id** |---| record's **ID** (matching condition: the same value as provided);
  if this parameter is provided in GET-request,
  all the other search parameters are ignored and the only one record
  with the requested ID is returned (if it exists and is published);
- **fieldid** |---| field code/number; (matching condition: case insensitive, a sub-string of the record corresponding field);
- **itemcode** |---| storage number (matching condition: case insensitive, a sub-string of the record corresponding field);
- **authorship** |---| authorship of the main species (matching condition: case insensitive, a sub-string of the record corresponding field);

.. _ISO3166-1-en: https://en.wikipedia.org/wiki/ISO_3166-1
.. _ISO3166-1-ru: https://ru.wikipedia.org/wiki/ISO_3166-1

.. note::

    The search engine performs only one-way transliteration of fields
    **collectedby** and **identifiedby** to Englsh language.
    So, if you will try to search, e.g. **collectedby=боб** (that corresponds to `bob` in English),
    the system will find  records including (in the collectedby field)
    either `боб` or `bob` sub-strings.
    On the contrary, If you will try to send **collectedby=bob** search query, only
    records include `bob` will be found
    (regardless the text case).

.. warning::

    Transliteration from Cyrillic (Russian) to Latin (English)
    is fully automatic
    and could be quite straightforward,
    e.g. `Джон` will be transliterated into something like `Dzhon`,
    instead of `John`, as it would expected.


Description of server response
------------------------------

The server response is a `JSON-formatted`_ text transferred via HTTP-protocol and having the following attributes:

.. _JSON-formatted: http://www.json.org

- **errors** |---| array of errors (each error is a string) occurred during search request evaluation;
- **warnings** |---| array of warnings (each warning is a string) occurred during search request evaluation;
- **data** |---| array of structured data, i.e. result of the search query.


.. note::

    Warnings are informative messages used to tell
    the user whats happened during interaction with the database
    in an unexpected way:
    e.g. which search parameters contradict each other,
    which parameters were ignored, which parameters weren't
    recognized by the system etc.



Format of the **data** attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **data** attribute is a JSON-formatted array.
Each item of this array describes a herbarium record and
has the following attributes:

- **family** |---| family name (Latin uppercase letters);
- **family_authorship** |---| family authorship; 
- **genus** |---| genus name;
- **genus_authorship** |---| genus authorship;
- **species_epithet** |---| species epithet;
- **species_id** |---| **ID** of species instance (unique integer value); don't mix with **ID** of the
  herbarium record. **ID**  of the herbarium record is unique among
  all herbarium records, **ID** of the species instance is unique
  among all species instances;
- **short_note** |---| used in multispecies herbarium records;
  the field provides important information about the main species
  of the herbarium record (it could be empty);
- **species_authorship** |---| species authorship;
- **species_status** |---| current species status;
  the term species status is related to species instance not
  herbarium record; it describes a degree of acceptance the
  species by scientific community (current state);
  Possible values of **species_status** are 'Recently added' |---|
  the species was recently included to the database and wasn't
  checked by an expert, 'Approved' |---| the species was approved by
  an expert (a user having some privileges),
  'Deleted' |---| the species name is probably obsolete and should be avoided,
  'From plantlist' |---| the species was imported from the http://theplantlist.org;
- **species_fullname** |---| full species name, e.g. Genus + species epithet + species authorship;
- **significance** |---| measure of ambiguity regard the main species (possible values: "", aff., cf.);
- **id** |---| integer identifier of a herbarium record, it is unique;
- **gpsbased** |---| Boolean parameter, its true value means that a herbarium record
  position is obtained via the GNSS (GPS/GLONASS); `true` value |---|
  guaranties that coordinates were obtained via GNSS.
- **latitude** |---|  latitude, degrees (WGS84);
- **longitude** |---| longitude, degrees (WGS84);
- **fieldid** |---| field number; an arbitrary string assigned by a collector;
- **itemcode** |---| inventory (storage) number, a string assigned by the herbarium's curator;
  it is used to identify the place of the record in the herbarium storage;
- **acronym** |---| herbarium acronym (e.g. VBGI);
- **branch** |---| herbarium branch/subdivision (e.g. "Herbarium of Fungi", "Bryophyte Herbarium" etc.);
- **collectors** |---| collectors;
- **identifiers** |---| identifiers;
- **devstage** |---| development stage; available values: Development stage partly, Life form or empty string;
- **updated** |---| the date the record was saved/updated;
- **created** |---|  the date the record was created;
- **identification_started** |---| the date the species identification was stаrted;
- **identification_finished** |---| the date the species identification was finished;
- **collection_started** |---| the date the herbarium item was collected (first day or null if no information provided);
- **collection_finished** |---| the date the herbarium item was collected (last day or null);
- **country** |---|  country;
- **country_id** |---| unique id of the country;
- **altitude** |---| altitude (sea level is treated as zero),
  this parameter is a string, therefore its form of altitude's
  representation might be quite fuzzy: '100-300', '100-300 m', '100', '100 m' etc.
- **region** |---|  region of collection;
- **district** |---| district of collection;
- **details** |---| environmental conditions of collection, additional info;
- **note** |---| everything that wasn't yet included
  in the previous fields (this field could include information about the place of collection,
  details on environmental conditions etc.);
- **dethistory** |---| an array; history of species identifications for this herbarium record;
- **additionals** |---| some herbarium records could include more than one species, this array describes all of these;
- **images** |---| a list of images related to the herbarium record ([] |--| an empty list, means that no images
  attached to the herbarium record were found); the list is formatted as follows:

        - *http://...* |--| first field of image record; it is a path (link), where the image coulde be downloaded from;
        - *image type* |--| allowed values are either 'p' or 's'; 'p' = 'place' |--| the image is related to the place of collection (e.g. snapshot of nature from top of the mountain etc.);
                            's' = 'sheet' |--| snapshot of the herbarium sheet;
        - *meta information* |--| json-formatted string including auxiliary information about the image; e.g. snapshot authorship, snapshot date, etc.
          In case of snapshot authorship, sample meta-string would be "{'photographer': 'Pavel Krestov', 'organization': 'Vladivostok Botanical Garden Institute'}"
          There is no restriction about names of meta-fields, such as 'photographer' or 'organization'; meta-fields could be
          arbitrary, but ones having intuitive values are preferred.


List of images attached to the herbarium record (example):

.. code:: python

              [
              ('http://someresource.com/path/to/image1', 'image1 type', 'meta information1'),
              ('http://someresource.com/path/to/image2', 'image2 type', 'meta information2'),
              ...
              ]


.. _field_reference_label:

.. note::

    Attributes **region**, **district**, **details**, **note**, **altitude** could be filled
    in bilingual mode, that means it could include special symbol "|".
    For instance, let's consider **region** and its value "Russian Far East|Дальний Восток России".
    The **region** string consist of two parts English and Russian separated by "|".
    In current implementation the API service doesn't care about what part of
    the string is really needed to the user and returns the entire string.
    Handling such cases, e.g. removing unnecessary sub-strings from left or right side of the "|" symbol,
    should be performed by the user.


.. note::

    Unpublished records are excluded from search results.


Structure of **dethistory** and **additionals** arrays are described below.


History of species identifications and additional species
`````````````````````````````````````````````````````````

**History of species identifications**

Each item of the array "History of species identifications" (**dethistory**)
describes an attempt of identification/confirmation
of the main species related to the herbarium record.

History of species identifications (**dethistory**) is an array having the following fields:

- **valid_from** |---| start date of species assignment validity;
- **valid_to** |---| start date of species assignment validity; empty field means that species assignment
  is actual since the **valid_from** date;
- **family** |---| family name;
- **family_authorship** |---| family authorship;
- **genus** |---| genus name;
- **genus_authorship** |---| genus authorship;
- **species_epithet** |---| species epithet;
- **species_id** |---| **ID** of species instance; 
- **species_authorship** |---| species authorship;
- **species_status** |---|  species instance status;
- **species_fullname** |---| full species name (Genus name + species epithet + species authorship);


.. note::

    If herbarium record/sheet include more than one species,
    than "history of species identifications" is related to the main
    species of the record only.


**Additional species**

Items of the array "Additional species" (**additionals**)
describe all species attached to the current herbarium record/sheet
and have the following fields
(fields have almost the same meaning as for **dethistory** array):

- **valid_from** |---| beginning date of validity of identification;
- **valid_to** |---| ending date of validity of identification; empty field means that species assignment to the herbarium record is actual since **valid_from** date;
- **family** |---| family name;
- **family_authorship** |---| family authorship;
- **genus** |---| genus name;
- **genus_authorship** |---| genus authorship;
- **species_epithet** |---| species epithet;
- **species_id** |---| **ID** of species instance; 
- **species_authorship** |---| species authorship;
- **species_status** |---|  species instance status;
- **species_fullname** |---| full species name;
- **significance** |---| measure of ambiguity regard the current species (possible values: "", aff., cf.);
- **note** |---| additional information about the current species;

.. note::
    The **note** field could be filled out with bilingual mode support (e.g. using the "|" symbol);
    So, it behaves like described :ref:`early <field_reference_label>`.


*Example*

Let us consider an example of **additionals** array of the following form (not all fields are shown for short):

.. code:: Python

    [
    {'genus': 'Quercus', 'species_epithet': 'mongolica', ... ,'valid_from': '2015-05-05', 'valid_to': '2016-01-01'},
    {'genus': 'Quercus', 'species_epithet': 'dentata', ... ,'valid_from': '2016-01-01', 'valid_to': ''},
    {'genus': 'Betula', 'species_epithet': 'manshurica', ... ,'valid_from': '2015-05-05', 'valid_to': ''},
    {'genus': 'Betula', 'species_epithet': 'davurica', ... ,'valid_from': '2015-05-05', 'valid_to': ''},
    ]

Interpretation:

So, if today is 2015, 1 Sept, than the array includes 
*Quercus mongolica*, *Betula manshurica* and *Betula davurica*, but *Quercus dentata* should be treated
as out-of-date for this date.

If today is 2017, e.g. 1 Jan 2017, than out-of-date status should be assigned to *Quercus mongolica*, 
and, therefore, actual set of species includes 
*Quercus dentata*, *Betula manshurica* и *Betula davurica*.


Service usage limitations
-------------------------

Due to long evaluation time needed to handle each HTTP-request,
there are some restrictions on creating
such long running keep-alive HTTP-connections (when using the HTTP API Service).

The number of allowed simultaneous connections to the service is determined by
JSON_API_SIMULTANEOUS_CONN_ value.

.. _JSON_API_SIMULTANEOUS_CONN:  https://github.com/VBGI/herbs/blob/master/herbs/conf.py

When the number of simultaneous connections is exceeded, the server doesn't evaluate
search requests, but an error message  is returned.

This behavior isn't related to search-by-id queries.
Search-by-id queries are evaluated quickly and have no special limitations.

Attempt to get data for unpublished record by its **ID** leads to an error message.



Examples
--------

To get tested with the service, one can build a search request
using web-browser (just follow the links below):

http://botsad.ru/hitem/json/?genus=riccardia&collectedby=bakalin

Follow through the link will lead to json-response that includes all known
(and published) herbarium records with genus *Riccardia* and collected by `bakalin`.


Searching by **ID** (`colstart` will be ignored):

http://botsad.ru/hitem/json?id=500&colstart=2016-01-01

http://botsad.ru/hitem/json?id=44

http://botsad.ru/hitem/json?id=5



.. _search_httpapi_examples:


.. seealso::

    `Accessing Digital Herbarium using Python <https://nbviewer.jupyter.org/github/VBGI/herbs/blob/master/herbs/docs/tutorial/Python/en/Python.ipynb>`_

    `Accessing Digital Herbarium using R <https://nbviewer.jupyter.org/github/VBGI/herbs/blob/master/herbs/docs/tutorial/R/en/R.ipynb>`_
