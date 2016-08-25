#coding: utf-8

import re
from datetime import date
import pandas as pd

# --------------- Author string validation and extraction --------
validate_auth_str_pat = re.compile(r'^[\sa-zA-Z\.\-\(\)]+$')
parenthesis_pat = re.compile(r'\(([\sa-zA-Z\.\-]+)\)')
after_parenthesis_pat = re.compile(r'\)([\sa-zA-Z\.\-]+)$')
# ----------------------------------------------------------------

# ----------------Date manipulations -----------------------------

monthes = {u'янв': 1,
           u'фев': 2,
           u'мар': 3, 
           u'апр': 4, 
           u'май': 5,
           u'мая': 5,
           u'июн': 6,
           u'июл': 7,
           u'авг': 8,
           u'сен': 9,
           u'окт': 10,
           u'ноя': 11,
           u'дек': 12
           }
year_pat = re.compile('\d{4}')
day_pat = re.compile('[\D]+(\d{1,2})[\D]+')

NECESSARY_DATA_COLUMNS = 'family    genus    species    country    region    district    place    coordinates    height    ecology    collected    collectedby    determined    determinedby    note    code1    code2    images'.split()

# ----------------------------------------------------------------


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

def evaluate_family(taxons):
    '''Could be changed in future; we don't follow dry principle here!'''
    res = taxon.split()
    authors = get_authors(' '.join(res[1:]))
    family = res[0]
    return (family, authors)

def evaluate_genus(taxons):
    '''Could be changed in future; we don't follow dry principle here!'''
    res = taxon.split()
    authors = get_authors(' '.join(res[1:]))
    genus = res[0]
    return (genus, authors)

def evaluate_species(taxons):
    '''Could be changed in future; we don't follow dry principle here!'''
    res = taxon.split()
    authors = get_authors(' '.join(res[2:]))
    species = res[1]
    return (species, authors)        
        
def evaluate_dates(dates):
    '''Convert dates from strings to Python-date objects or leave unchanged if errors found.
    '''
    result = []
    for item in dates:
        item_ = ' ' + unicode(item, 'utf-8') + ' '
        year = year_pat.findall(item_)
        if len(year) != 1:
            result.append(('Year not found', item_))
            continue
        cmonth = None
        for month in monthes.keys():
            if month in item_:
                cmonth = monthes[month]
        if not cmonth:
            result.append(('Month not found', item_))
            continue
        day = day_pat.findall(item_)
        if len(day) != 1:
            result.append(('Day not found', item_))
            continue
        day = int(day.pop())
        year = int(year.pop())
        if not (0 < day < 32): 
            result.append(('Day not in range', item_))
            continue 
        if year > 2050 or year < 1500:
            result.append(('Strange year', item_))
            continue
        cdate = date(year=year, day=day, month=cmonth)
        result.append(('', cdate))
    return result


def evluate_herb_dataframe(df):
    '''It is assumed the dataframe has valid set of column names'''
    errmsgs = [[]]
    newdf = pd.DataFrame.from_dict([{key: None for key in df.columns}])
    for ind, item in df.iterrows():
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

        # -------- Unconditioned evaluations -------------
        item['country'][:255]
        item['region'][:255]
        item['district'][:255]
        item['place'][:255]
        item['ecology'][:255]
        item['height'][:255]
        item['collectedby'][:255]
        item['determinedby'][:255]
        item['note'][:255]
        
        # conditioned fields.. .
        #coordinates  height collected determined code1 code2 images        
        
        
            
    # TODO: Not completed;