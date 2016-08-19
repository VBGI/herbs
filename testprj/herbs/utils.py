import re

validate_auth_str_pat = re.compile(r'^[\sa-zA-Z\.\-\(\)]+$')
parenthesis_pat = re.compile(r'\(([\sa-zA-Z\.\-]+)\)')
after_parenthesis_pat = re.compile(r'\)([\sa-zA-Z\.\-]+)$')


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



