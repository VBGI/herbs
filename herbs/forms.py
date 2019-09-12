#coding: utf-8

import re
from ajax_select.fields import (AutoCompleteSelectField,
                                AutoCompleteField)
from django import forms
from django.forms.models import ModelFormMetaclass
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta, date
from .models import (Family, Genus, HerbItem, Species,
                     DetHistory, HerbAcronym, Additionals)
from django.db.models.fields import FieldDoesNotExist
from django.forms.util import ErrorList
from .conf import settings, HerbsAppConf

try:
    from captcha.fields import ReCaptchaField
except ImportError:
    ReCaptchaField = None

from six import with_metaclass

# ---------- tinymce integration

try:
    from tinymce.widgets import TinyMCE
except ImportError:
    TinyMCE = None

tinymce_fieldset = {
    'theme': 'advanced',
    'theme_advanced_buttons1': "bold,italic,sub,sup",
    'theme_advanced_buttons2': "",
    'theme_advanced_buttons3': "",
    'cleanup_on_startup' : True,
    'width':'50%',
    'height':'400px',
    'theme_advanced_text_colors' : "000000,ff0000,0000ff",
    'force_br_newlines': False,
    'force_p_newlines': False,
    'forced_root_block' : '',
    'formats': {
                'bold': {'inline': 'b'},
                'italic': {'inline': 'i'}
                },
    'invalid_elements' : "strong,em",
    'valid_elements' : "b,i,sub,sup"

}

# ------------------------------

CS = getattr(settings,
             '%s_CH_SIZE' % HerbsAppConf.Meta.prefix.upper(), 80)

taxon_name_pat = re.compile(r'[a-z]+')
itemcode_pat = re.compile(r'^\d+$')
duplicates_pat = re.compile(r'^[A-Z,\s]+$')




def remove_spaces(*args):
    def wrapped(name):
        def _clean_spaces(self, _name=name):
            data = self.cleaned_data[_name]
            return data.strip()
        return _clean_spaces

    class StripSpaces(ModelFormMetaclass):
        def __new__(cls, name, bases, attrs):
            for arg in args:
                attrs['clean_' + arg ] = wrapped(arg)
            return super(StripSpaces, cls).__new__(cls, name, bases, attrs)
    return StripSpaces


class TaxonCleanerMixin(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name']
        data = data.lower().strip()
        mainquery = self.Meta.model.objects.filter(name=data)
        if self.instance:
            mainquery = mainquery.exclude(id=self.instance.id)
        if mainquery.exists():
            raise forms.ValidationError(_("имя должно быть уникально"))
        if len(data.split()) > 1:
            raise forms.ValidationError(_("название таксона не должно содержать пробелов"))
        if not taxon_name_pat.match(data):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))
        return data


class HerbItemFormSimple(forms.ModelForm):
    class Meta:
        model = HerbItem


class HerbItemForm(with_metaclass(remove_spaces('collectedby',
                                                'identifiedby',
                                                'region',
                                                'district'),
                                  forms.ModelForm)):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(HerbItemForm, self).__init__(*args, **kwargs)

    def clean_itemcode(self):
        data = self.cleaned_data['itemcode']
        data = data.strip()
        if data:
            mainquery = HerbItem.objects.filter(itemcode=data)
            if self.instance:
                mainquery = mainquery.exclude(id=self.instance.id)
            if self.request:
                query = HerbAcronym.objects.filter(allowed_users__icontains=self.request.user.username)
            else:
                query = None
            if query:
                if mainquery.filter(acronym=query[0]).exclude(status='D').exists():
                    raise forms.ValidationError(_("запись с таким кодом уже существует"))
            if not itemcode_pat.match(data):
                raise forms.ValidationError(_("уникальный код должен либо отсутствовать, либо быть числовым"))
        return data

    def _verify_dates(self, d):
        if d:
            if d.month == timezone.now().date().month and d.day in [1, 28, 29, 30, 31]:
                return None
            if d > (timezone.now() + timedelta(days=2)).date():
                raise forms.ValidationError(_("Дата не может быть больше текущей календарной даты"))

            if d < date(year=1700, month=1, day=1):
                raise forms.ValidationError(_("Не ошибка ли это? Слишком древний образец."))

    def clean_identified_s(self):
        data = self.cleaned_data['identified_s']
        self._verify_dates(data)
        return data

    def clean_note(self):
        return self.cleaned_data['note'].replace('&nbsp;', ' ')

    def clean_detailed(self):
        return self.cleaned_data['detailed'].replace('&nbsp;', ' ')

    def clean_identified_e(self):
        data = self.cleaned_data['identified_e']
        self._verify_dates(data)
        return data

    def clean_collected_s(self):
        data = self.cleaned_data['collected_s']
        self._verify_dates(data)
        return data

    def clean_collected_e(self):
        data = self.cleaned_data['collected_e']
        self._verify_dates(data)
        return data

    def clean_duplicates(self):
        data = self.cleaned_data['duplicates']
        data = data.upper().strip()
        if data:
            all_acronyms = settings.HERBS_INDEX_HERBARIORUM.split(',')
            if not duplicates_pat.match(data):
                raise forms.ValidationError(_("Один или несколько гербарных акронимов не соответствуют принятому формату"))
            acronyms = map(lambda x: x.strip(),  data.split(','))
            for ac in acronyms:
                if ac not in all_acronyms:
                    raise forms.ValidationError(_("Акроним {} не зарегистрирован в Index Herbariorum".format(ac)))
        return data

    def clean(self):
        '''Checking consistency for dates '''
        formdata = self.cleaned_data
        d1 = formdata.get('identified_s')
        d2 = formdata.get('identified_e')
        if d1 and d2:
            if d2 < d1:
                self._errors.setdefault('identified_e', ErrorList())
                self._errors['identified_e'].append(_('дата окончания определения должна быть не раньше даты начала'))

        dc1 = formdata.get('collected_s')
        dc2 = formdata.get('collected_e')

        if dc1 and d1:
            if d1 < dc1 and d1.day == 1 and d2 and d2.day in [28, 29, 30, 31] and d2.month == d1.month and d2.year >= dc1.year and d2.month>=d1.month:
                pass
            elif d1 < dc1 and d1.day == 1 and d2 and d2.day == 31 and d1.month == 1 and d2.month == 12 and d2.year >= dc1.year:
                pass
            elif d1 < dc1:
                self._errors.setdefault('identified_s', ErrorList())
                self._errors['identified_s'].append(_('дата определения не может быть раньше даты сбора'))
        if dc1 and dc2:
            if dc2 < dc1:
                self._errors.setdefault('collected_e', ErrorList())
                self._errors['collected_e'].append(_('дата окончания сбора должна быть не раньше даты начала'))

        ispub = formdata.get('public')
        icode = formdata.get('itemcode')
        sp = formdata.get('species')
        if icode:
            icode = icode.strip()
        if ispub:
            if not icode:
                forms.ValidationError(_('публиковать можно только при непустом уникальном коде образца'))
            if sp:
                if sp.status not in ['A', 'P']:
                    raise forms.ValidationError(_('вид не одобрен куратором; опубликовать можно только одобренные виды'))
        return formdata

    class Meta:
        model = HerbItem

    species = AutoCompleteSelectField('species', required=True, help_text=None, label=_("Вид"))
    if TinyMCE:
        note = forms.CharField(widget=TinyMCE(mce_attrs=tinymce_fieldset),
                               required=False, label=_('Заметки'))
        detailed = forms.CharField(widget=TinyMCE(mce_attrs=tinymce_fieldset),
                                   required=False,
                                   label=_('Место сбора'))
    else:
        note = forms.CharField(widget=forms.Textarea, required=False, label=_('Заметки'))
        detailed = forms.CharField(widget=forms.Textarea, required=False,
                                   label=_('Место сбора'))
    detailed.help_text = _("локализация, экоусловия")
    country = AutoCompleteSelectField('country', required=False, help_text=None, label=_("Страна"))
    region = AutoCompleteField('region', required=False, help_text=None, label=_("Регион"), attrs={'size': CS})
    district = AutoCompleteField('district', required=False, help_text=None, label=_("Район"), attrs={'size': CS})
    collectedby = AutoCompleteField('collectedby', required=False, help_text=None, label=_("Собрали"), attrs={'size': CS})
    identifiedby = AutoCompleteField('identifiedby', required=False, help_text=None, label=_("Определили"), attrs={'size': CS})


class DetHistoryForm(with_metaclass(remove_spaces('identifiedby'),forms.ModelForm)):
    class Meta:
        model = DetHistory
    species = AutoCompleteSelectField('species', required=False, label=_("Вид"))
    identifiedby = AutoCompleteField('identifiedby', required=False,
                                     label=_("Переопределелил(и)"),
                                     attrs={'size': CS})


class AdditionalsForm(with_metaclass(remove_spaces('identifiedby'),forms.ModelForm)):
    class Meta:
        model = Additionals
    species = AutoCompleteSelectField('species', required=True, label=_("Вид"))
    identifiedby = AutoCompleteField('identifiedby', required=False,
                                     label=_("Определелил(и)"),
                                     attrs={'size': CS})


class RectSelectorForm(forms.Form):
    latl = forms.FloatField(required=False)
    latu = forms.FloatField(required=False)
    lonl = forms.FloatField(required=False)
    lonu = forms.FloatField(required=False)


class SearchForm(forms.Form):
    '''Common search form for ajax requests'''

    family = forms.CharField(required=False, max_length=30)
    genus = forms.CharField(required=False, max_length=30)
    species_epithet = forms.CharField(required=False, max_length=50)
    itemcode = forms.CharField(required=False, max_length=15)
    collectedby = forms.CharField(required=False, max_length=100)
    identifiedby = forms.CharField(required=False, max_length=100)
    country = forms.CharField(required=False, max_length=100)
    place = forms.CharField(required=False, max_length=200)
    colstart = forms.DateField(required=False)
    colend = forms.DateField(required=False)

    # sorting parameters
    sortfield = forms.CharField(required=False, max_length=100)
    sortorder = forms.BooleanField(required=False)

    # extra parameters for validation
    acronym = forms.CharField(required=False, max_length=10)
    subdivision = forms.CharField(required=False, max_length=100)


class GenusForm(TaxonCleanerMixin):
    class Meta:
        model = Genus
    family = AutoCompleteSelectField('family', required=True, help_text=None, label=_("Семейство"))

    def clean_gcode(self):
        data = self.cleaned_data['gcode']
        data = data.strip()
        if data:
            if not itemcode_pat.match(data):
                return forms.ValidationError('уникальный код рода должен быть цифровой')
        return data


class FamilyForm(TaxonCleanerMixin):
    class Meta:
        model = Family


class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species

    genus = AutoCompleteSelectField('genus', required=True, help_text=None,
                                    label=_("Род"))
    synonym = AutoCompleteSelectField('species', label=_("Синоним вида"),
                                      required=False)

    name = forms.CharField(max_length=70, label=_('Название'), required=True,
                           help_text=_('видовой эпитет'))

    def clean(self):
        form_data = self.cleaned_data
        name = form_data.get('name', '').strip().lower()
        genus = form_data.get('genus', None)
        authorship = form_data.get('authorship', '').strip()
        status = form_data.get('status', 'N')
        infra_rank = form_data.get('infra_rank', '')
        infra_epithet = form_data.get('infra_epithet', '').strip()
        infra_authorship = form_data.get('infra_authorship', '').strip()

        if infra_epithet and not infra_rank:
            raise forms.ValidationError(_("нужно определить подвидовой ранг или оставить поле подвидовой эпитет пустым"))

        if infra_epithet:
            if infra_rank != 'G':
                infra_epithet = infra_epithet.lower()

        if name and genus and self.instance and status != 'D':
            if Species.objects.filter(name=name,
                                      genus=genus,
                                      authorship=authorship,
                                      infra_rank=infra_rank,
                                      infra_epithet=infra_epithet,
                                      infra_authorship=infra_authorship).exclude(id=self.instance.id).exclude(status='D').exists():
                raise forms.ValidationError(_('такой набор (род, вид, автор, подвидовой ранг, подвидовой эптитет, автор подвидового эпитета) уже существует'))
        if not taxon_name_pat.match(name):
            raise forms.ValidationError(_("название таксона должно состоять только из латинских букв"))

        if infra_epithet:
            if not taxon_name_pat.match(infra_epithet.lower()):
                raise forms.ValidationError(
                    _("название подвидового эпитета должно состоять только из латинских букв"))

        # TODO: Prevent fields changing if published herbitems exist; clarification needed
        form_data['name'] = name
        form_data['infra_epithet'] = infra_epithet
        return form_data


class SendImage(forms.Form):
    image = forms.FileField(label=_("Выберите гербарное изображение"),
                            required=False)
    overwrite = forms.BooleanField(label=_("Перезаписать"), required=False)


class ReplyForm(forms.Form):
    email = forms.EmailField(required=False, label="E-mail")
    description = forms.CharField(widget=forms.Textarea, required=False, label=_('Описание'),
                                  max_length=2000)
    if ReCaptchaField:
        captcha = ReCaptchaField(attrs={'lang': 'en'})


class BulkChangeForm(forms.Form):
    field = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}),
                            required=False, label=_('Поле'), max_length=50)
    old_value = forms.CharField(widget=TinyMCE(mce_attrs=tinymce_fieldset),
                                required=False, label=_('Текущее значение'))
    as_subs = forms.BooleanField(required=False, label=_('Искать как включение (подстроку)'))
    case_insens = forms.BooleanField(required=False, label=_('Не учитывать регистр'))
    new_value = forms.CharField(widget=TinyMCE(mce_attrs=tinymce_fieldset),
                                required=False, label=_('Новое значение'))
    captcha = forms.CharField(max_length=50, label=_('Название поля (повторить)'),
                              required=True)

    def clean(self):
        cleaned_data = self.cleaned_data
        cleaned_data['field'] = field_name = cleaned_data.get('field', '').strip()
        cleaned_data['captcha'] = captcha = cleaned_data.get('captcha', '').strip()
        cleaned_data['new_value'] = cleaned_data.get('new_value', '').strip()
        if captcha != field_name:
            raise forms.ValidationError(
                _("название изменяемого поля и введеное название не совпадают"))
        try:
             fobj = HerbItem._meta.get_field(cleaned_data['field'])
        except FieldDoesNotExist:
             return cleaned_data
        allowed_length = getattr(fobj, 'max_length', 0)
        if len(cleaned_data['new_value']) > allowed_length and allowed_length is not 0:
            raise forms.ValidationError(_(u'Новое значение поля превосходит'
                                          u' его допустимую длину.'
                                          u' Допустимая длина составляет %s символов.' % allowed_length))
        max_chars = getattr(settings,
                            '%s_MAX_BULK_CONTAIN_CHARS' % HerbsAppConf.Meta.prefix.upper(),
                            5)
        if cleaned_data['as_subs'] and len(cleaned_data['old_value']) < max_chars:
            raise forms.ValidationError(_('Запрещается выполнять поиск включения, '
                                          'если условие поиска содержит менее %s символов.' %
                                          max_chars
                                          ))
        return cleaned_data

    def clean_field(self):
        data = self.cleaned_data['field']
        allowed = getattr(settings, '%s_ALLOWED_FOR_BULK_CHANGE' % HerbsAppConf.Meta.prefix.upper(),
                          None)
        if data.strip() not in allowed:
            raise forms.ValidationError(_(u'Недопустимое имя поля. Допустимыми являются только поля:  ') + ','.join(allowed))
        return data
