#coding: utf8
from bs4 import BeautifulSoup, NavigableString, Comment
from copy import deepcopy

html = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title></title>
</head>
<body>
<div id="test">
Пример  не <div>самый</div>
обычный.
</div>
</body>
</html>'''


def item_contains_word(item, word):
    splits = unicode(item).strip().split()
    try:
        ind = splits.index(word)
    except ValueError:
        return None, None
    return ' '.join(splits[:ind]), ' '.join(splits[ind+1:])


z = BeautifulSoup(html)
res = z.find(id='test')
newres = BeautifulSoup()
word = u'Пример'

for item  in res:
    print item
    newres.append(item)
    #if isinstance(item, NavigableString) and not isinstance(item, Comment):
        ## разбиение фрагментов текста на слова, если нужно...
        #a, b = item_contains_word(item, word)
        #if a or b:
            #new_tag = z.new_tag('sup')
            #new_tag.string = '1'
            #to_insert = [NavigableString(a), NavigableString(word), new_tag, NavigableString(b)]
            #for nn in to_insert:
                #res.insert(ind-1, nn)
            
        

print res, '=============\n'
print newres