# coding: utf-8


from django.utils.dateformat import DateFormat
from transliterate.base import TranslitLanguagePack, registry
from transliterate import translit
from transliterate.contrib.languages.ru.translit_language_pack import RussianLanguagePack
from django.utils import translation
from .conf import settings

SIGNIFICANCE = settings.HERBS_SPECIES_SIGNIFICANCE

DELIMITER = settings.HERBS_BILINGUAL_DELIMITER

CYRILLIC_SYMBOLS = set(u"абвгдезиклмнопрстуфхцЦъыьАБВГДЕЗИКЛМНОПРСТУФХЪЫЬ")


def create_safely(model, fields=(), values=(), postamble='iexact'):
    post = '__%s' % postamble if postamble else ''
    kwargs = {'%s' % key + post: val for key, val in zip(fields, values)}
    query = model.objects.filter(**kwargs)
    if query.exists():
        return query[0]
    else:
        newobj = model(**{key: val for key, val in zip(fields, values)})
        newobj.save()
        return newobj


def _smartify_dates(item, prefix='collected'):
    date_s = getattr(item, prefix + '_s', None)
    date_e = getattr(item, prefix + '_e', None)
    if not (date_s or date_e):
        return ''
    if date_s:
        if date_e:
            fdate_s = DateFormat(date_s)
            fdate_e = DateFormat(date_e)
            if (date_e.month == date_s.month) and\
                    (date_s.day == 1) and (date_e.day in
                                           [30, 31]):
                return fdate_s.format('M Y')
            else:
                if date_s < date_e:
                    return fdate_s.format('d M Y') +\
                       u'\N{EM DASH}' + fdate_e.format('d M Y')
                else:
                    return fdate_s.format('d M Y')
        else:
            fdate_s = DateFormat(date_s)
            return fdate_s.format('d M Y')
    elif date_e:
        fdate_e = DateFormat(date_e)
        return fdate_e.format('d M Y')


def _smartify_altitude(alt):
    if not alt:
        return ''
    alt = alt.strip()
    alt.replace(u' м.', ' m.')
    alt.replace(u' м ', ' m.')
    alt = alt[:30]  # Altitude couldn't be very long?!
    return alt


# ------------------ HerbItem to Json ------------------

def get_family_or_genus_name(obj, genus=False, attr='name'):
    if hasattr(obj, 'species'):
        if obj.species is None:
            return ''
        if hasattr(obj.species, 'genus'):
            if obj.species.genus is None:
                return ''
            elif genus:
                res = getattr(obj.species.genus, attr)
                return res.title() if attr == 'name' else res
            else:
                if hasattr(obj.species.genus, 'family'):
                    if obj.species.genus.family is None:
                        return ''
                    res = getattr(obj.species.genus.family, attr)
                    return res.upper() if attr == 'name' else res
        else:
            return ''
    else:
        return ''


def prefill_related_species(hitem, attr):
    store = []
    if hasattr(hitem, attr):
        for item in getattr(hitem, attr).all():
            dataitem = {'identifiers': item.identifiedby,
                        'valid_from': str(item.identified_s) if item.identified_s else '',
                        'valid_to': str(item.identified_e) if item.identified_e else ''}
            if item.species:
                dataitem.update({'family': get_family_or_genus_name(item),
                                 'family_authorship': get_family_or_genus_name(item, attr='authorship'),
                                 'genus': get_family_or_genus_name(item, genus=True),
                                 'genus_authorship': get_family_or_genus_name(item, genus=True, attr='authorship'),
                                 'species_epithet': item.species.name,
                                 'species_authorship': item.species.authorship,
                                 'species_id': item.species.pk,
                                 'infraspecific_rank': item.species.get_infra_rank_display(),
                                 'infraspecific_epithet': item.species.infra_epithet,
                                 'infraspecific_authorship': item.species.infra_authorship,
                                 'species_status': item.species.get_status_display(),
                                 'species_fullname': item.species.get_full_name(),
                                 'significance': item.significance if item.significance else ''
                                 })

                if attr == 'additionals':
                    dataitem.update({'note': item.note})
            else:
                dataitem.update({'family': '',
                                 'family_authorship': '',
                                 'genus': '',
                                 'genus_authorship': '',
                                 'species_epithet': '',
                                 'species_authorship': '',
                                 'species_id': '',
                                 'species_status': '',
                                 'species_fullname': '',
                                 'significance': '',
                                 'infraspecific_rank': '',
                                 'infraspecific_epithet': '',
                                 'infraspecific_authorship': ''
                                 })
            store.append(dataitem)
    return store


def herb_as_dict(hitem):
    '''Get main herbitem properties as dictionary'''
    result = dict()
    if hitem.species:
        result.update({'family': get_family_or_genus_name(hitem)})
        result.update({'family_authorship': get_family_or_genus_name(hitem, attr='authorship')})
        result.update({'genus': get_family_or_genus_name(hitem, genus=True)})
        result.update({'genus_authorship': get_family_or_genus_name(hitem, genus=True, attr='authorship')})
        result.update({'species_epithet': hitem.species.name})
        result.update({'species_authorship': hitem.species.authorship})
        result.update({'infraspecific_epithet': hitem.species.infra_epithet})
        result.update({'infraspecific_rank': hitem.species.get_infra_rank_display()})
        result.update({'infraspecific_authorship': hitem.species.infra_authorship})
        result.update({'species_id': hitem.species.pk})
        result.update({'species_status': hitem.species.get_status_display()})
        result.update({'species_fullname': hitem.get_full_name()})
    result.update({'significance': hitem.significance if hitem.significance else ''})
    result.update({'short_note': hitem.short_note})
    result.update({'type_status': hitem.get_type_status_display()})
    result.update({'id': hitem.pk})
    result.update({'gpsbased': hitem.gpsbased})
    result.update({'latitude': hitem.latitude})
    result.update({'longitude': hitem.longitude})
    result.update({'fieldid': hitem.fieldid})
    result.update({'itemcode': hitem.itemcode})
    result.update({'acronym': hitem.acronym.name if hitem.acronym else ''})
    result.update({'branch': hitem.subdivision.name if hitem.subdivision else ''})
    result.update({'collectors': hitem.collectedby})
    result.update({'identifiers': hitem.identifiedby})
    result.update({'devstage': hitem.get_devstage_display() if hitem.devstage else ''})
    result.update({'updated': str(hitem.updated)})
    result.update({'created': str(hitem.created)})
    result.update({'identification_started': str(hitem.identified_s) if hitem.identified_s else ''})
    result.update({'identification_finished': str(hitem.identified_e) if hitem.identified_e else ''})
    result.update({'collection_started': str(hitem.collected_s) if hitem.collected_s else ''})
    result.update({'collection_finished': str(hitem.collected_e) if hitem.collected_e else ''})
    result.update({'country': hitem.country.name_en if hitem.country else ''})
    result.update({'country_id': hitem.country.pk if hitem.country else None})
    result.update({'altitude': hitem.altitude})
    result.update({'region': hitem.region})
    result.update({'district': hitem.district})
    result.update({'note': hitem.note})
    result.update({'details': hitem.detailed})
    dethistory = prefill_related_species(hitem, 'dethistory')
    result.update({'dethistory': dethistory})
    additionals = prefill_related_species(hitem, 'additionals')
    result.update({'additionals': additionals})
    result.update({'images': hitem.has_images.split(',') if hitem.has_images else []})
    return result

# -------------- Transliterate customization -------

registry.unregister(RussianLanguagePack)

# - new mappings (modified russian language pack)

new_mapping = (
    u"abvgdeziklmnoprstufhcC'y'ABVGDEZIKLMNOPRSTUFH'Y'",
    u"абвгдезиклмнопрстуфхцЦъыьАБВГДЕЗИКЛМНОПРСТУФХЪЫЬ",
)

new_reversed_specific_mapping = (
    u"йЙэЭъьЪЬ",
    u"иИeE''''"
)

new_pre_processor_mapping = {
    u"zh": u"ж",
    u"ts": u"ц",
    u"ch": u"ч",
    u"sh": u"ш",
    u"shch": u"щ",
    u"yu": u"ю",
    u"ya": u"я",
    u"yo": u"ё",
    u"Zh": u"Ж",
    u"Ts": u"Ц",
    u"Ch": u"Ч",
    u"Sh": u"Ш",
    u"Shch": u"Щ",
    u"Yu": u"Ю",
    u"Ya": u"Я",
    u"Yo": u"Ё"
}


class NewRussianLanguagePack(TranslitLanguagePack):
    language_code = "ru"
    language_name = "Russian"
    character_ranges = ((0x0400, 0x04FF), (0x0500, 0x052F))
    mapping = new_mapping
    reversed_specific_mapping = new_reversed_specific_mapping
    pre_processor_mapping = new_pre_processor_mapping
    detectable = True

registry.register(NewRussianLanguagePack)

# --------------------------------------------------


def smartify_language(value, lang=''):
    try:
        value = str(value)
    except UnicodeEncodeError:
        pass
    if DELIMITER in value:
        if value.count(DELIMITER) > 1:
            return value
        a, b = value.split(DELIMITER)
        a = a.strip()
        b = b.strip()
        if len(a) == 0 or len(b) == 0:
            return value
        _cya = len(set(a).intersection(CYRILLIC_SYMBOLS))
        _cyb = len(set(b).intersection(CYRILLIC_SYMBOLS))
        if _cya > _cyb:
            ru_value = a
            en_value = b
        elif _cya < _cyb:
            ru_value = b
            en_value = a
        else:
            ru_value, en_value = a, b

        if lang == 'ru':
            return ru_value
        elif lang == 'en':
            return en_value

        if translation.get_language() == 'ru':
            return ru_value
        else:
            return en_value
    else:
        return value
