#coding: utf-8

import re

import pandas as pd

from datetime import date

from django.utils.text import capfirst


# --------------- Author string validation and extraction --------
validate_auth_str_pat = re.compile(r'^[\sa-zA-Z\.\-\(\)]+$')
parenthesis_pat = re.compile(r'\(([\sa-zA-Z\.\-]+)\)')
after_parenthesis_pat = re.compile(r'\)([\sa-zA-Z\.\-]+)$')
unique_code_pat = re.compile(r'\d{1,10}')
# ----------------------------------------------------------------

# ----------------Date manipulations -----------------------------

monthes = {'янв': 1,
           'фев': 2,
           'мар': 3, 
           'апр': 4, 
           'май': 5,
           'мая': 5,
           'июн': 6,
           'июл': 7,
           'авг': 8,
           'сен': 9,
           'окт': 10,
           'ноя': 11,
           'дек': 12
           }
year_pat = re.compile('\d{4}')
day_pat = re.compile('[\D]+(\d{1,2})[\D]+')

NECESSARY_DATA_COLUMNS = 'family    genus    species    country    region    district    place    coordinates    height    ecology    collected    collectedby    identified    identifiedby itemcode  gcode note'.split()

# ----------------------------------------------------------------

def smart_unicode(s):
    # TODO: This should be checked for infinite recursion in Django
    res = ''
    if type(s) is unicode:
        res = s.encode('utf-8')
    else:
        res = str(s)
    if 'nan' == res.lower().strip():
        res = ''
    return res


def get_authors(auth_str):
    '''Evaluates an `author string` and returns list of authors and priorities 
    '''

    _auth_str = auth_str.strip()
    err_msg = ''
    auth_array = []

    if not _auth_str:
        err_msg = 'Author not provided'
        return (err_msg, [(0, '')])
    elif not validate_auth_str_pat.match(_auth_str):
        err_msg = 'Invalid author string'
        return (err_msg, [(0, _auth_str)])

    if _auth_str.count('(') != _auth_str.count(')'):
        err_msg = 'Unbalanced parenthesis'
        return (err_msg, [(0, _auth_str)])

    if _auth_str.count('(') > 0:
        flist = parenthesis_pat.findall(_auth_str)
        if len(flist) != 1:
            err_msg = 'Auxiliary author string is empty'
            return (err_msg, [(0, _auth_str)])
        else:
            try:
                after_auth = after_parenthesis_pat.findall(_auth_str).pop().strip()
            except IndexError:
                err_msg = 'Auxiliary authors without primary authors are given'
                return (err_msg, [(0, _auth_str)])
            if after_auth:
                auth_array.append(after_auth)
            auth_array.append(flist[0])
    else:
        auth_array.append(_auth_str)

    return (err_msg, list(enumerate(reversed(auth_array))))


def evaluate_family(taxon):
    '''Could be changed in future; we don't follow dry principle here!'''
    res = taxon.split()
    authors = get_authors(' '.join(res[1:]))
    family = res[0]
    return (family, authors)


def evaluate_genus(taxon):
    '''Could be changed in future; we don't follow dry principle here!'''
    res = taxon.split()
    authors = get_authors(' '.join(res[1:]))
    genus = res[0]
    return (genus, authors)


def evaluate_species(taxon):
    '''Could be changed in future; we don't follow dry principle here!'''
    res = taxon.split()
    authors = get_authors(' '.join(res[2:]))
    species = res[1]
    return (species, authors)        


def evaluate_date(item):
    '''Make str to date convertion.
    '''
    item_ = ' ' + item + ' '
    year = year_pat.findall(item_)
    if len(year) != 1:
        result = ('Year not found', item_)
        return result
    cmonth = None
    for month in monthes.keys():
        if month in item_:
            cmonth = monthes[month]
    if not cmonth:
        result = ('Month not found', item_)
        return result 
    day = day_pat.findall(item_)
    if len(day) != 1:
        result = ('Day not found', item_)
        return result 
    day = int(day.pop())
    year = int(year.pop())
    if not (0 < day < 32): 
        result = ('Day not in range', item_)
        return result 
    if year > 2050 or year < 1500:
        result = ('Strange year', item_)
        return result
    cdate = date(year=year, day=day, month=cmonth)
    return ('', cdate)


def create_safely(model, fields=(), values=(), postamble='iexact'):
    post = '__%s'%postamble if postamble else ''
    kwargs = {'%s' % key + post: val for key, val in zip(fields, values)}
    query = model.objects.filter(**kwargs)
    if query.exists():
        return query[0]
    else:
        newobj = model(**{key: val for key, val in zip(fields, values)})
        newobj.save()
        return newobj

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

def evluate_herb_dataframe(df):
    '''It is assumed the dataframe has valid set of column names'''
    errmsgs = []
    result = []
    for ind, item in df.iterrows():
        item = {key: smart_unicode(item[key])  for key in item.keys()}
        errmsgs.append([])
        # -------- Family evaluations -------------
        familyok = False
        try:
            cfamily, cfauthors = evaluate_family(item['family'])
            if cfauthors[0]:
                errmsgs[-1].append('Ошибка в строке %s в поле семейство: %s' % (ind + 1, cfauthors[0]))
            else:
                familyok = True    
        except: 
            errmsgs[-1].append('Ошибка в строке %s в поле семейство' % (ind + 1, ))
        # -----------------------------------------    

        # -------- Genus evaluations -------------
        genusok = False
        try:
            cgenus, cgauthors = evaluate_genus(item['genus'])
            if cgauthors[0]:
                errmsgs[-1].append('Ошибка в строке %s в поле род: %s' % (ind + 1, cgauthors[0]))
            else:
                genusok = True    
        except: 
            errmsgs[-1].append('Ошибка в строке %s в поле род' % (ind + 1, ))
        # -----------------------------------------                      

        # -------- Species evaluations -------------
        speciesok = False
        try:
            cspecies, cspauthors = evaluate_species(item['species'])
            if cspauthors[0]:
                errmsgs[-1].append('Ошибка в строке %s в поле вид: %s' % (ind + 1, cspauthors[0]))
            else:
                speciesok = True
        except:
            errmsgs[-1].append('Ошибка в строке %s в поле вид' % (ind + 1, ))
        # -----------------------------------------  


        # -------- Collected evaluations -------------
        try:
            colmsg, coldate = evaluate_date(item['collected'])
            if colmsg:
                errmsgs[-1].append('Ошибка в строке %s в поле "начало сбора": %s' % (ind + 1, colmsg))
                coldate = None
        except:
            errmsgs[-1].append('Ошибка в строке %s в поле "начало сбора"' % (ind + 1, ))
            coldate = None
        # -----------------------------------------

        # -------- Determined evaluations -------------
        try:
            detmsg, detdate = evaluate_date(item['identified'])
            if detmsg:
                errmsgs[-1].append('Ошибка в строке %s в поле дата определения: %s' % (ind + 1, detmsg))
                detdate = None
        except: 
            errmsgs[-1].append('Ошибка в строке %s в поле дата определения' % (ind + 1, ))
            detdate = None
        # -----------------------------------------

        # --------- Code1 is a string of digits only  --------
        itemcodeok = False
        if unique_code_pat.match(str(item['itemcode']).strip()):
            itemcodeok = True
            itemcode = str(item['itemcode']).strip()
        else:
            errmsgs[-1].append('Ошибка в строке %s в поле уникальный код' % (ind + 1, ))
        # -----------------------------------------

        # --------- Code2 is a string of digits only  --------
        gcodeok = False
        if unique_code_pat.match(str(item['gcode']).strip()):
            gcodeok = True
            gcode = str(item['gcode']).strip()
        else:
            errmsgs[-1].append('Ошибка в строке %s в поле код раздела' % (ind + 1, ))


        # -----------------------------------------
        if familyok & genusok & speciesok &\
            itemcodeok & gcodeok:
            result.append({'family': cfamily,
                       'family_auth': cfauthors,
                       'genus': cgenus,
                       'genus_auth': cgauthors,
                       'species': cspecies,
                       'species_auth': cspauthors,
                       'itemcode': itemcode, 
                       'gcode': gcode,
                       'identified': detdate,
                       'collected': coldate,
                       'country': item['country'].strip(), 
                       'region': item['region'].strip(),
                       'district': item['district'].strip(),
                       'coordinates': item['coordinates'].strip(),
                       'ecology': item['ecology'].strip(),
                       'height': item['height'].strip(),
                       'collectedby': item['collectedby'].strip(),
                       'identifiedby': item['identifiedby'].strip(),
                       'detailed': item['place'].strip(),
                       'height': item['height'].strip(),
                       'note': item['note'].strip(),
                       }
                      )
    return result, errmsgs