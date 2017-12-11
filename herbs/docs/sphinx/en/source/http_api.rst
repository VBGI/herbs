========================================
Digital Herbarium's HTTP-API Description
========================================

.. contents:: :local:

.. |---| unicode:: U+2014  .. em dash

.. |--| unicode:: U+2013   .. en dash


Intro
-----

This document describes HTTP-API (Application Programming Interface over HTTP protocol)
which can be used to get access to Digital Herbarium Database of the BGI.

HTTP-API works in read-only mode.
There is no way to make changes in the database using the API.


Description of HTTP request parameters
--------------------------------------

Only GET-requests are allowed when reffering to the HTTP API service.
To establish connection with the service, one can use HTTP or HTTPS protocols.

Requests with multiple parameters, e.g. `colstart=2016-01-01` and `collectedby=bak`,
are treated as components of `AND`-type queries:
in this example, all records collected
after `2016-01-01` and including `bak`
(case insensitive matching is performed)
as a sub-string of `Collectors` field will be returned.

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
  a sub-string occurring in one of the listed fields: **Place**, **Region**, **District**, **Note**;);
- **collectedby** |---| collectors (matching condition: case insensitive, a sub-string of the record corresponding field);
  if the field's value is given in Cyrillic, search will be performed (additionally) using its transliterated copy;
- **identifiedby** |---| identifiers; (matching condition: case insensitive, a sub-string of the record corresponding field);
  if the field's value is given in Cyrillic, search will be performed (additionally) using its transliterated copy;
- **country** |---| country's name (matching condition: case insensitive, a sub-string of the record corresponding field);
- **colstart** |---| date when herbarium sample collection was started (yyyy-mm-dd);
- **colend** |---|  date when herbarium sample collection was finished (yyyy-mm-dd);
- **acronym** |---| acronym of the herbarium (matching condition:
  case insensitive, the same name as provided);
- **subdivision** |---| subdivision of the herbarium (matching condition:
  case insensitive, the same name as provided);
- **latl** |---| latitude lower bound, should be in (-90, 90);
- **latu** |---| latitude upper bound, should be in (-90, 90);
- **lonl** |---| longitude lower bound, should be in (-180, 180);
- **lonu** |---| longitude upper bound, should be in (-180, 180);
- **synonyms** |---| Boolean parameter, allowed values are `false` or `true`; absence of the parameter
  in GET-request is treated as its `false` value; `true` value (e.g. `synonyms=true`)
  tells the system to search records taking into account the table of species synonyms;
  *Note:* when performing search including known
  (known by the system) species synonyms one should provide
  both **genus** and **species_epithet** values,
  if only one of them is provided or both are leaved empty,
  a warning will be shown and the search condition will be ignored;
- **additionals** |---| Boolean parameter, allowed values are `false` or `true`;
  absence of the parameter in GET-request is treated as its `false` value;
  `true` value (e.g. `additionals=true`) tells the system to
  search within additional species (if such is provided);
  some herbarium records could include more than one species (such records are
  referred as multispecies records);
- **id** |---| record's **ID** (matching condition: the same value as provided);
  if this parameter is provided in GET-request,
  all other search parameters are ignored and the only one record
  with the requested ID is returned (if it exists and is published);
- **fieldid** |---| field code/number; (matching condition: case insensitive, a sub-string of the record corresponding field);
- **itemcode** |---| storage number (matching condition: case insensitive, a sub-string of the record corresponding field);
- **authorship** |---| authorship of the main species (matching condition: case insensitive, a sub-string of the record corresponding field);
- **imonly** |---| allowed values are false or true; absence of the parameter in GET-request is treateda as its `false` value;
                   when filtering with **imonly=true** records having images will be shown only.

.. _ISO3166-1-en: https://en.wikipedia.org/wiki/ISO_3166-1
.. _ISO3166-1-ru: https://ru.wikipedia.org/wiki/ISO_3166-1

.. note::

    The search engine performs only one-way transliteration of
    **collectedby** and **identifiedby** fields into English language.
    So, if you try to search, e.g. **collectedby=боб** (that corresponds to `bob` in English),
    the system will find  records including (in the collectedby field)
    both `боб` and `bob` sub-strings.
    On the contrary, If you try to send **collectedby=bob** search query, only
    records that include `bob` will be found  (regardless the text case).

.. warning::

    Transliteration from Cyrillic (Russian) to Latin (English)
    is fully automatic
    and could be quite straightforward,
    e.g. `Джон` will be transliterated into something like `Dzhon`,
    instead of `John`, as it would expected.


Description of server response
------------------------------

The server response is a `JSON-formatted`_ text transferred via HTTP-protocol
and having the following attributes:

.. _JSON-formatted: http://www.json.org

- **errors** |---| array of errors (each error is a string) occurred during search request processing;
- **warnings** |---| array of warnings (each warning is a string) occurred during search request processing;
- **data** |---| array of structured data, i.e. result of the search query.


.. note::

    Warnings are informative messages that are intended to tell
    the user what went in an unexpected way during interaction with the database:
    e.g. which search parameters contradict each other,
    which parameters were ignored, which parameters weren't
    recognized by the system etc.



Format of the **data** attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **data** attribute is a JSON-formatted array.
Each item of this array describes a herbarium record and
has the following attributes:

- **family** |---| family name (Latin uppercase letters);
- **family_authorship** |---| self explanatory parameter;
- **genus** |---| genus name;
- **genus_authorship** |---| self explanatory parameter;
- **species_epithet** |---| self explanatory parameter;
- **species_id** |---| **ID** of the species-level taxon (unique integer value); don't mix with **ID** of the
  herbarium record. **ID**  of the herbarium record is unique among
  all herbarium records, **ID** of the species-level taxon is unique
  among all species-level taxa;
- **infraspecific_rank** |---| allowed values:  subsp., subvar., f., subf., var. or null (i.e. left blank);
- **infraspecific_epithet** |---| self explanatory parameter;
- **infraspecific_authorship** |---| self explanatory parameter;
- **short_note** |---| used in multispecies herbarium records;
  the field provides important information about the main species
  of the herbarium record (it could be empty);
- **species_authorship** |---| self explanatory parameter;
- **species_status** |---| current species status;
  the term "species status" is related to species-level taxon not
  herbarium record; it describes a degree of acceptance of
  species by scientific community (current state);
  possible values of **species_status** are 'Recently added' |---|
  the species was recently included to the database and wasn't
  checked by an expert, 'Approved' |---| the species was approved by
  an expert (a user having some privileges),
  'Deleted' |---| the species name is probably obsolete and should be avoided,
  'From plantlist' |---| the species was imported from the http://theplantlist.org;
- **type_status** |---| type status of the collection;
- **species_fullname** |---| full species name, e.g. Genus + species epithet + species authorship;
- **significance** |---| measure of ambiguity regarding the main species (possible values: "", aff., cf.);
- **id** |---| integer identifier of a herbarium record, it is unique;
- **gpsbased** |---| Boolean parameter, its true value means that a herbarium record
  position is obtained via the GNSS (GPS/GLONASS);
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
- **country** |---|  country name;
- **country_id** |---| unique (integer) id of the country internally assigned by the system;
- **altitude** |---| altitude (sea level is treated as zero),
  this parameter is a string, therefore its form of altitude's
  representation might be quite fuzzy: '100-300', '100-300 m', '100', '100 m' etc.; it is assumed that altitude value is given in meters;
- **region** |---|  administrative region of collection;
- **district** |---| administrative district of collection;
- **details** |---| environmental conditions of collection, additional info;
- **note** |---| everything that wasn't yet included
  in the previous fields (this field could include information about the place of collection,
  details on environmental conditions etc.);
- **dethistory** |---| an array; history of species identifications for this herbarium record;
- **additionals** |---| some herbarium records could include more than one species, this array describes them;
- **images** |---| a list of images related to the herbarium record ([] |--| an empty list, means that no images
  attached to the herbarium record were found);


.. note::

    Images from the **images** array are provided in several resolutions.
    Currently, the system stores images of different resolutions in directories
    named `ss` |--| small size (30% of original size); `ms` |--| medium size (60% original size);
    `fs` |--| full size (original size).

    Therefore, each image url includes one of the following components
    ` /ts/ `,` /ss/ `, ` /ms/ ` или ` /fs/ `. These components point to
    resolution of the image available from this url.


.. note::

    All images are saved as jpeg via `ImageMagick`_ image processing utilities with the following parameters:

    .. code:: python

        '-strip', '-interlace', 'Plane',
        '-sampling-factor', r'4:2:0',
        '-quality',
        r'90%'

    It comes from practice that such compression don't significantly impact on images.
    In the save time, compression is very important and allows to save a lot of storage space.


.. _ImageMagick: http://imagemagick.org


.. the list is formatted as follows:
        - *http://...* |--| first field of image record; it is a path (link), where the image could be downloaded;
        - *image type* |--| allowed values are either 'p' or 's'; 'p' = 'place' |--| the image is related to the place of collection (e.g. snapshot of the surrounding ecosystem etc.);
                            's' = 'sheet' |--| snapshot of the herbarium sheet;
        - *meta information* |--| json-formatted string including auxiliary information about the image; e.g. snapshot authorship, snapshot date, etc.
          In case of snapshot authorship, sample meta-string would be "{'photographer': 'Pavel Krestov', 'organization': 'Vladivostok Botanical Garden Institute'}"
          There is no restriction about names of meta-fields, such as 'photographer' or 'organization'; meta-fields could be
          arbitrary, but ones having intuitive names are preferred.


List of images attached to the herbarium record (example):

.. code:: python

    ['http://botsad.ru/herbarium/view/snapshots/VBGI/ss/VBGI32618_1.jpg',
     'http://botsad.ru/herbarium/view/snapshots/VBGI/ts/VBGI32618_1.jpg',
     'http://botsad.ru/herbarium/view/snapshots/VBGI/ms/VBGI32618_1.jpg',
     'http://botsad.ru/herbarium/view/snapshots/VBGI/fs/VBGI32618_1.jpg'
    ...
    ]


.. _field_reference_label:

.. note::

    Attributes **region**, **district**, **details**, **note**, **altitude**
    could be filled in bilingual mode:
    English first, than – Russian (or vice versa),
    with special symbol "|"
    separating two spellings
    (for instance, region’s value"Russian Far East|Дальний Восток России").
    Removing unnecessary sub-strings from the left or
    the right side of the "|"  symbol couldn’t be done
    in the current implementation of the API service,
    it should be performed by the user.


.. note::

    Unpublished records are excluded from the search results.


Structure of **dethistory** and **additionals** arrays are described below.


History of species identifications and additional species
`````````````````````````````````````````````````````````

**History of species identifications**

Each item of the array "History of species identifications" (**dethistory**)
describes an attempt of identification/confirmation
of the main species related to the herbarium record.

History of species identifications (**dethistory**) is an array having the following fields:

- **valid_from** |---| start date of assignment validity to particular species name;
- **valid_to** |---| end date of assignment validity to particular species name; empty field means that species' name
                     assignment is actual since the **valid_from** date;
- **family** |---| family name;
- **family_authorship** |---| self explanatory parameter;
- **genus** |---| genus name;
- **genus_authorship** |---| self explanatory parameter;
- **species_epithet** |---| self explanatory parameter;
- **species_id** |---| **ID** of the species-level taxon;
- **species_authorship** |---| self explanatory parameter;
- **species_status** |---|  status of the species-level taxon;
- **species_fullname** |---| full species name (Genus name + species epithet + species authorship);
- **infraspecific_rank** |---| allowed values:  subsp., subvar., f., subf., var. or null (i.e. left blank);
- **infraspecific_epithet** |---| self explanatory parameter;
- **infraspecific_authorship** |---| self explanatory parameter;
- **significance** |---| measure of ambiguity regarding the current species (possible values: "", aff., cf.);

.. note::

    If herbarium record/sheet include more than one species,
    than "history of species identifications" is related to the main
    species of the record only.


**Additional species**


"Additional species" (**additionals**) is an array describing all the species
(except the main species) attached to the current herbarium record/sheet.
It is non-empty only for multispecies herbarium records.
Each element of the **additionals** array has the following fields
(fields have almost the same meaning as for **dethistory** array):

- **valid_from** |---| beginning date of validity of identification;
- **valid_to** |---| ending date of validity of identification;
      empty field means that species' name assignment to the herbarium record is actual since **valid_from** date;
- **family** |---| family name;
- **family_authorship** |---| self explanatory parameter;
- **genus** |---| genus name;
- **genus_authorship** |---| self explanatory parameter;
- **species_epithet** |---| self explanatory parameter;
- **species_id** |---| **ID** of the species-level taxon;
- **species_authorship** |---| self explanatory parameter;
- **species_status** |---|  status of the species-level taxon;
- **species_fullname** |---| full species name;
- **significance** |---| measure of ambiguity regard the current species (possible values: "", aff., cf.);
- **infraspecific_rank** |---| allowed values:  subsp., subvar., f., subf., var. or null (i.e. left blank);
- **infraspecific_epithet** |---| self explanatory parameter;
- **infraspecific_authorship** |---| self explanatory parameter;
- **note** |---| additional information about the current species;

.. note::
    The **note** field could be filled out bilingually (e.g. using the "|" symbol);
    So, it behaves like described :ref:`early <field_reference_label>`.


*Example*

Let us consider an example of **additionals** array (not all fields are shown for short):

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

If today is 2017,  1 Jan, than out-of-date status should be assigned to *Quercus mongolica*,
and, therefore, actual set of species includes 
*Quercus dentata*, *Betula manshurica* и *Betula davurica*.


Service usage limitations
-------------------------

Due to the long processing time needed to handle each HTTP-request,
there are some restrictions on creating
such (long running) keep-alive HTTP-connections (when using the HTTP API Service).

The number of allowed simultaneous connections to the service is determined by
JSON_API_SIMULTANEOUS_CONN_ value.

.. _JSON_API_SIMULTANEOUS_CONN:  https://github.com/VBGI/herbs/blob/master/herbs/conf.py

When the number of simultaneous connections is exceeded, the server doesn't process
search requests, but an error message  is returned.

This behavior isn't related to search-by-id queries.
Search-by-id queries are evaluated quickly and have no special limitations.

Attempt to get data for unpublished record by its **ID** leads to an error message.



Examples
--------

To test the service, one can build a search request
using web-browser (just follow the links below):

http://botsad.ru/hitem/json/?genus=riccardia&collectedby=bakalin

Following the link will lead to json-response that includes all known
(and published) herbarium records of genus *Riccardia* collected by `bakalin`.


Searching by **ID** (`colstart` will be ignored):

http://botsad.ru/hitem/json?id=500&colstart=2016-01-01

http://botsad.ru/hitem/json?id=44

http://botsad.ru/hitem/json?id=5



.. _search_httpapi_examples:


.. seealso::

    `Accessing Digital Herbarium using Python <https://nbviewer.jupyter.org/github/VBGI/herbs/blob/master/herbs/docs/tutorial/Python/en/Python.ipynb>`_

    `Accessing Digital Herbarium using R <https://nbviewer.jupyter.org/github/VBGI/herbs/blob/master/herbs/docs/tutorial/R/en/R.ipynb>`_
