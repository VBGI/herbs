from django.core.management.base import BaseCommand

try:
    from herbs.models import HerbItem
    from herbs.management.process_images import IMAGE_CONVERSION_OPTS
except ImportError:
    from bgi.herbs.models import HerbItem
    from bgi.herbs.management.process_images import IMAGE_CONVERSION_OPTS

import re, os

from django.conf import settings

image_path_ = getattr(settings, 'HERBS_SOURCE_IMAGE_PATHS', '.')
image_thumb_ = getattr(settings, 'HERBS_SOURCE_IMAGE_THUMB', 'ts')
image_url_ = getattr(settings, 'HERBS_SOURCE_IMAGE_URL', '')

image_pat_ = re.compile(r'[A-Z]{1,10}\d+(_?\d{1,2})\.[jJ][pP][gG]')

image_comp_pat_ = re.compile(r'([A-Z]{1,10})(\d+)')

check_path_ = re.compile(r'^[^,]+$')

def get_all_image_files(sources=[image_path_]):
    for dirpath in sources:
        for dir_, dirnames, filenames in os.walk(dirpath):
            for filename in filenames:
                if image_pat_.match(filename):
                    abspath = os.path.join(dir_, filename)
                    yield abspath


class Command(BaseCommand):
    args = ''
    help = 'Index all herbarium images'
    def handle(self, *args, **options):
        HerbItem.objects.all().update(has_images=None)
        result = {}
        for image in get_all_image_files():
            bname = os.path.basename(image)
            acronym, id = image_comp_pat_.findall(bname.strip())[-1]
            if (id, acronym) in result:
                if bname not in result[(id, acronym)]:
                    result[(id, acronym)].extend([bname])
            else:
                result[(id, acronym)] = [bname]

        for id_, ac_ in result:
            try:
                items = HerbItem.objects.filter(id=id_,
                                                acronym__name__exact=ac_)
            except HerbItem.DoesNotExist:
                items = None

            if items:
                images = []
                for key in IMAGE_CONVERSION_OPTS.keys():
                    baseurl = '/'.join(s.strip('/') for s in [image_url_,
                                                          ac_, key])
                    images.extend(map(lambda x: baseurl + '/' + x, result[(id_, ac_)]))
                items.update(has_images=','.join(images))
