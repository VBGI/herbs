import re
from datetime import date



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
            for auth in flist[0].split():
                auth_array.append(auth)
    else:
        auth_array.append(_auth_str)

    return (err_msg, list(enumerate(reversed(auth_array))))


def evaluate_taxons(taxons, count=1):
    result = []
    for item in taxons:
        splitted = item.split()
        if len(splitted) == 1:
            result.append((splitted[0].strip().lower(),
                           get_authors('')))
        else:
            family = ' '.join(splitted[:count]).lower()
            authors = get_authors(' '.join(splitted[count:]))
            result.append((family, authors))
    return result


def evaluate_dates(dates):
    '''Convert dates from strings to Python-date objects or leave unchanged if errors found.
    '''
    result = []
    for item in dates:
        item_ = ' ' + item + ' '
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
        day = int(day)
        month = int(month)
        year = int(year)
        if not (0 < day < 32): 
            result.append('Day not in range', item_)
            continue 
        if year > 2050 or year < 1500:
            result.append('Strange year', item_)
            continue
        cdate = date(year=year, day=day, month=month)
        result.append(('', cdate))
    return result
