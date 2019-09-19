from django.core.management.base import BaseCommand

try:
    from herbs.models import HerbItem
except ImportError:
    from bgi.herbs.models import HerbItem


class Command(BaseCommand):
    args = ''
    help = 'Compute and fill latitude and longitude auxiliary fields'

    def handle(self, *args, **options):
        count = 0
        for obj in HerbItem.objects.all().exclude(coordinates__isnull=True):
            try:
                obj.latitude = float(obj.coordinates.latitude)
                obj.longitude = float(obj.coordinates.longitude)
                obj.save()
                count += 1
            except (ValueError, AttributeError, TypeError):
                pass
        self.stdout.write('Successfully updated %s herbarium records' % count)
