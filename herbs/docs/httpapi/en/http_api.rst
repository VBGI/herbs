=========================================================================
Making automatic queries to the Herbarium Database. HTTP-API Description.
=========================================================================


.. contents:: :local:

.. |---| unicode:: U+2014  .. em dash

.. |--| unicode:: U+2013   .. en dash

-----
Intro
-----

This document describes HTTP-API (Automative Programming Interface over HTTP protocol) for working 
with the Herbarium Database.

HTTP-API is working in readonly mode only. There is no way to make changes in the database using this API.


Description of request parameters
---------------------------------

Only GET-requests are allowed when talking with the HTTP-API. To establish connection with the service,
one can use either HTTP or HTTPS protocols.

Requests with multiple parameters, e.g. `colstart=01.01.2016` and `collectedby=Bak`, are treated as `AND`-type queries:
in this example, all records collected after `01.01.2016` and including `bak` (case insensetive inclusion is checked) as a substring in `Collectors` field of the main table of the database will be returned.


`OR`-type query behaviour can be emulated by series of consequent queries to the database and isn't natively implemented
in the current version of the API.

List of allowed GET-parameters:

- **family** |---| family name (case insensetive, records should have the same family name as provided);

- **genus** |---|  genus name (case insensetive, records should have the same gunus name as provided), note: if its value contradicts with the family name provided in the same request, an error will be returned as a part of json-response;
- **species_epithet** |---| species epithet (case insensetive, records should have the provided value as a substring in the correspongin field of the database);
- **place** |---|  place of collection (case insensetive, 
 records should have the provided value as a substring in the correspongin field of the database), if the parameter is given, searching is performed over the following fields: **Place**, **region**, **district**, **note**;
- **collectedby** |---| collectors (case insensetive, 
 records should have the provided value as a substring in the correspongin field of the database);
- **identifiedby** |---| identifiers; (case insensetive, 
 records should have the provided value as a substring in the correspongin field of the database);
- **country** |---| country name (case insensetive, records should have the provided value as a substring in the correspongin field of the database); the system knows country names according to standards ISO31661-1-ru_ and ISO3166-1-en_; Russian Federation is replaced with Russia for short;
- **colstart** |---| date when collection was started (yyyy-mm-dd);
- **colend** |---|  date when collection was finished (yyyy-mm-dd);
- **acronym** |---| name of the herbarium acronym (case insensetive, records should have exactly the same acronym as provided);
- **subdivision** |---| name of the herbarium subdivision/branch (case insensetive, 
 records should have the provided value as a substring in the correspongin field of the database);
- **latl** |---| lower bound of latitude, should be in (-90, 90);
- **latu** |---| upper bound of latitude, should be in (-90, 90);
- **lonu** |---| upper bound of longitude, should be in (-180, 180);
- **lonl** |---| lower bound od longitude, should be in (-180, 180);
- **synonyms** |---| boolean parameter, allowed values are `false` or `true`; absence of the parameter in GET-request is treated as its false value; true value (e.g. `synonyms=true`) tells the system to search records taking into account the table of species synonyms; *note:* when performing search including known (known by the system) species synonyms one should provide both **genus** and **species_epithet** values, if only one of these is provided or both are leaved empty, a warning will be shown and this search condition will be ignored;
  
- **additionals** |---| boolean parameter, allowed values are `false` or `true`; absence of the parameter in GET-request is treated as its false value; true value (e.g. `additionals=true`) tells the system to search within additionals species (if such exist); some herbarium records include more than one species, e.g. bryophyte records;
- **id** |---| record's **ID** ; if this parameter is provided in GET-request, 
  all the other search parameters are ignored and the only one record (if it exists and is published) 
 with the requested ID is returned;
  
- **fieldid** |---| field number;
- **itemcode** |---| storage number (used in the herbarium storage);
- **authorship** |---| authorship of the main species (case insensetive, 
 records should have the provided value as a substring in the correspongin field of the database);

.. _ISO3166-1-en: https://en.wikipedia.org/wiki/ISO_3166-1
.. _ISO3166-1-ru: https://ru.wikipedia.org/wiki/ISO_3166-1


Description of server's response
--------------------------------

The server's response is a `JSON-formatted`_ text transferred via HTTP-protocol and having the following attributes:

.. _JSON-formatted: http://www.json.org

- **errors** |---| array of errors (strings) occurred during search request evaluation;
- **warnings** |---| array of warnings (strings) occurred during search request evaluation; note: warnings are informative messages used to tell the user whats happened in an unexpected way: e.g. which search parameters contradict each other, which parameters were ignored, which parameters weren't recognized by the system etc.
- **data** |---| array of structured data, i.e. result of the search query.


Structured data format
~~~~~~~~~~~~~~~~~~~~~~

**data** attribute is a json-formatted array, 

Параметр **data** представляет собой массив данных, удовлетворяющих текущему поисковому зарпосу.

Он имеет следующую структуру, описывающую текущий гербарный сбор:

- **family** |---| название семейства (заглавными буквами, на латыни); 
- **family_authorship** |---| автор семейста; 
- **genus** |---| название рода;
- **genus_authorship** |---| автор рода;
- **species_epithet** |---| видовой эпитет;
- **species_id** |---| **ID** вида образца; не путать с **ID** текущей гербарной записи. **ID** текущей гербарной записи однозначно характеризует данную оцифрованную гербарную запись. **ID** вида образца, только вид. Гербарных записей, содержащих какой-либо вид может быть много.
- **species_authorship** |---| автор вида;
- **species_status** |---| текущий статус вида; определяет степень признанности данного вида, точнее триплета (род, видовой эпитет, авторство вида) в научном сообществе на настоящее время. Возможные значения данного параметра 1) "Recently added" |---| вид недавно добавлен и, скорее, не проверялся специалистом; название вида с таким статусом может быть устаревшим, либо содержатьошибки; 2) "Approved" |---| название вида подтверждено специалистом; 3) "Deleted" |---| вид имеет ошибку в записи, или его название устарело и не используется; 4) "From plantlist" |---| название импортировано из базы http://theplantlist.org.
- **species_fullname** |---| полное название вида, т.е. Род + видовой эпитет + авторство.
- **id** |---| уникальный идентификатор данной гербарной записи; всегда целое число;
- **gpsbased** |---| получены ли данные о географической привязки места сбора образца с помощью GPS (значение **true**), либо другим способом (**false**); следует иметь ввиду, что у многих образцов, даже при **gpsbased** равном **false**, координаты, если таковые заданы, были получены при помощи GPS; это связано с тем, что не все отмечают соответствующее поле (**gpsbased**) при заполнении электронной формы образца;  
- **latitude** |---|  широта, градусы; георафическая координата места сбора в системе WGS-84;
- **longitude** |---| долгота, градусы; географическая координата места сбора в системе WGS-84;
- **fieldid** |---| полевой номер образца;
- **itemcode** |---| инвентаризационный номер, используемый в гербарном хранилище;
- **acronym** |---| гербарный акроним, которому принадлежит данная гербарная запись (для большинства записей поле имеет значение **VBGI**);
- **branch** |---| подраздел гербария внутри акронима; иногда удобно иметь подразделы внутри общей гербарной базы: например, "гербарий грибов", "биоморфологический гербарий" и т.п.;
- **collectors** |---| текстовая строка: сборщики образца;
- **identifiers** |---| текстовая страка: те, кто определил вид гербарного сбора;
- **devstage** |---| стадия развития; определена для биоморфологического гербария; возможные значения: Development stage partly, Life form, или пустое поле;
- **updated** |---| дата последнего изменения записи в базе данных;
- **created** |---| дата создания записи (т.е. занесения её электронную базу данных);
- **identification_started** |---| дата начала определения вида;
- **identification_finished** |---| дата окончания определения вида; дата определения вида задана в виде интервала, поскольку не всегда может быть указана точная дата, а например,только месяц, или время проведения какой-либо экспедиции; 
- **country** |---|  название страны сбора образца;
- **country_id** |---| числовой идентификатор страны сбора образца;
- **altitude** |---| высота над уровнем моря места сбора образца; значение представляется собой строку, не всегда однозначно определяющую реальную высоту сбора. Возможны, например, варианты: 100-300 м, 120 м, 400, 300-400 и т.п. 
- **region** |---| регион сбора;
- **district** |---| район сбора;
- **details** |---| экологические условия сбора, дополнительные уточнения не вошедшие в поля регион и район;
- **note** |---| примечание; может содержать информацию о месте сбора, экологических условиях и т.п.;
- **dethistory** |---| представляет собой массив |---| историю переопределений вида гербарного сбора;
- **additionals** |---| некоторые гербарные сборы могут содержать более одного вида; данный массив описывает характеристики каждого из них.


Поля **region**, **district**, **details**, **note**, **altitude** могут быть заполнены с поддержкой двуязычности с использованием спецсимвола "|". Например, строка, возвращаемая в поле **region**, может быть такой "Russian Far East|Дальний Восток России". Это означает, что относительно символа "|" даётся русско- и англоязычный варианты строки. Дальнейшая обработка значений таких строк ложится на пользователя системы, которому решать
какую из компонент строки относительно символа "|" оставить, а какую |--| удалить. Система HTTP-API не принимает таких решений.


Структура массивов **dethistory** и **additionals** приводитcя ниже.


История переопределений и дополнительные сборы
``````````````````````````````````````````````

**История переопределений**

Каждый элемент массива "История переопределений" (**dethistory**) представляет собой описание
попытки определения (переопределения) вида в текущем гербарном сборе и имеет
следующие поля (значения полей, характеризующих вид, аналогично описанным выше):

- **valid_from** |---| дата валидности определения;
- **valid_to** |---| дата окончания валидности определения; поле может быть не задано, что означает, что предполагает, что определение актуально в настоящее время;
- **family** |---| название семейства;
- **family_authorship** |---| авторство семейства;
- **genus** |---| название рода;
- **genus_authorship** |---| автор рода;
- **species_epithet** |---| видовой эпитет;
- **species_id** |---| **ID** вида образца; 
- **species_authorship** |---| автор вида;
- **species_status** |---| текущий статус вида;
- **species_fullname** |---| полное название вида;

Сроки валидности вида (**valid_from**, **valid_to**) позволяют корректно описать любые его последующие переопределения.

**Примечание** Если в гербарном сборе представлен не один вид, то массив "История переопределений" представляет собой историю переопределений основного вида.


**Дополнительные виды**

Каждый элемент массива "Дополнительные виды" (**additionals**) представляет собой 
описание вида, находящегося в данном гербарном сборе. Каждое из таких описаний имеет
поля, аналогичные записям из **Истории переопределений**:

- **valid_from** |---| дата валидности определения;
- **valid_to** |---| дата окончания валидности определения; поле может быть не задано, что означает, что предполагает, что определение актуально в настоящее время;
- **family** |---| название семейства;
- **family_authorship** |---| авторство семейства;
- **genus** |---| название рода;
- **genus_authorship** |---| автор рода;
- **species_epithet** |---| видовой эпитет;
- **species_id** |---| **ID** вида образца; 
- **species_authorship** |---| автор вида;
- **species_status** |---| текущий статус вида;
- **species_fullname** |---| полное название вида;

Таким образом, массив "Дополнительные виды" позволяет хранить информацию о видах в герарном сборе,
cопутствующих данному основному виду (выделенному из эксперных соображений в качестве основного),
а указание валидности позволяет описать переопределения (если таковые имеются) каждого из таких видов.

*Пояснение и интерпретация*

Рассмотрим для примера следующий массив "Дополнительных видов" (для краткости выписаны не все поля):

.. code:: Python

    [
    {'genus': 'Quercus', 'species_epithet': 'mongolica', ... ,'valid_from': '2015-05-05', 'valid_to': '2016-01-01'},
    {'genus': 'Quercus', 'species_epithet': 'dentata', ... ,'valid_from': '2016-01-01', 'valid_to': ''},
    {'genus': 'Betula', 'species_epithet': 'manshurica', ... ,'valid_from': '2015-05-05', 'valid_to': ''},
    {'genus': 'Betula', 'species_epithet': 'davurica', ... ,'valid_from': '2015-05-05', 'valid_to': ''},
    ]

Если сегодня, например, 1 сентября 2015 года (2015-09-01), то массив дополнительных видов состоит из
*Quercus mongolica*, *Betula manshurica* и *Betula davurica*, а *Quercus dentata* является неактуальным определением
на данный момент времени.

Если сегодня 2017 год, например, 2017-01-01, то неактуальным оказывается *Quercus mongolica*,  и, таким образом,
актуальными видовыми составляющими сбора являются *Quercus dentata*, *Betula manshurica* и *Betula davurica*


**Примечание** Массив "Дополнительные виды" предназначен только для описания дополнительных видов; основной вид не указывается в дополнительных видах.


Ограничения
-----------

Поскольку поисковому запросу пользователя может удовлетворять большой объём данных,
для формирования ответа сервера может потребоваться значительное время. 

Чтобы снизить нагрузку на сервер, вызванную вероятно долгими 
keep-alive HTTP-соединениями, действуют ограничения. 

Количество одновременно возможных
соединений для сервиса автоматизированного опроса гербарной базы определяется текущим значением параметра JSON_API_SIMULTANEOUS_CONN_.

.. _JSON_API_SIMULTANEOUS_CONN:  https://github.com/VBGI/herbs/blob/master/herbs/conf.py

По превышении этого количества, сервер не обрабатывает поисковые запросы, а возвращает
сообщение об ошибке.

На запросы, содержащие  **id**, данное ограничение не действует, поскольку получение информации об объекте 
по его **ID**  |---| не ёмкая в плане ресурсов операция. 

Информация о  **неопубликованных** образцах не выводится; при попытке получить информацию о неопубликованном образце по его **ID** 
выводится ошибка.


Примеры
-------

Для проверки работы системы и получения json-ответа сервера достаточно передать поисковый запрос в url браузера.


Например, переход по ссылке

http://botsad.ru/hitem/json/?genus=riccardia&collectedby=bakalin

приведет к появлению на экране браузера json-ответа, содержащего информацию о всех сборах |--| представителей рода *Riccardia*, 
в строке, содержащей информацию о сборщиках которых встречается `bakalin`.

При указании **id** в **GET** запросе, все остальные поисковые поля игнорируеются и выводится информация
о гербарном образце с указанным **id**:

http://botsad.ru/hitem/json?id=500

http://botsad.ru/hitem/json?id=44

http://botsad.ru/hitem/json?id=5
