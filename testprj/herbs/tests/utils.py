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

    if _auth_str.count('(') != _auth_str.count(')'):
        err_msg = 'Unbalanced parenthesis'
        return (err_msg, (_auth_str, 0))
    
    
    if _auth_str.count('(') > 0:
        flist = parenthesis_pat.findall(_auth_str)
        if len(flist) != 1:
            err_msg = 'Auxiliary author string is empty'
            return (err_msg, (_auth_str, 0))
        else:
            try:
                after_auth = after_parenthesis_pat.findall(_auth_str).pop().strip()
            except IndexError:
                err_msg = 'Auxiliary authors without primary authors are given'
            if after_auth:
                auth_array.append(after_auth)
            for auth in _auth_str.split():
                auth_array.append(auth)
    else:
        auth_array.append(_auth_str)

    return (err_msg, list(enumerate(reversed(auth_array))))

# def evaluate_taxons(taxons, count=1):
#     
#     for item in taxons:
#         item.split()
        