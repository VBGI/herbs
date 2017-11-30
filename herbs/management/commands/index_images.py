from django.core.management.base import BaseCommand

try:
    from herbs.models import HerbItem
except ImportError:
    from bgi.herbs.models import HerbItem

import re, os

from django.conf import settings

image_path_ = getattr(settings, 'HERBS_SOURCE_IMAGE_PATHS', None)
image_pat_ = re.compile(r'[A-Z]{1,10}\d+(_?\d{1,2})\.[jJ][pP][gG]')

image_comp_pat_ = re.compile(r'([A-Z]{1,10})(\d+)')


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
        HerbItem.objects.all().update(has_images=False)
        for image in map(str.strip, map(os.path.basename,
                                        get_all_image_files())):
            try:
                acronym, id = image_comp_pat_.findall(image)[-1]
                items = HerbItem.objects.filter(id=id,
                                                acronym__name__exact=acronym)
            except (HerbItem.DoesNotExist, IndexError):
                items = None
            if items:
                items.update(has_images=True)
