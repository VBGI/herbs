from django.core.management.base import BaseCommand
import numpy as np
from herbs.models import SpeciesSynonym, Species

class Command(BaseCommand):
    args = ''
    help = 'Rebuild index of species synonym tables'

    def handle(self, *args, **options):
        SpeciesSynonym.objects.all().delete()

        arrays = [[]]
        for sp in Species.objects.all().exclude(synonym__isnull=True).exclude(
                                                status='D').iterator():
            cur = sp.pk
            syn = sp.synonym.pk
            narrays = np.array(arrays, dtype=long)
            wcur = np.where(narrays==cur)
            wsyn = np.where(narrays==syn)
            if any(wcur[0]) and any(wsyn[0]):
                pass
            elif any(wcur[0]) and not any(wsyn[0]):
                arrays[wcur[0]].append(syn)
            elif not any(wcur[0]) and any(wsyn[0]):
                arrays[wsyn[0]].append(cur)
            else:
                arrays.append([cur, syn])
        count = 0
        for arr in arrays:
            SpeciesSynonym.objects.get_or_create(rebuild_scheduled=False,
                                                 json_content=','.join(map(str, arr)) + ',')
            count += 1
        self.stdout.write('Successfully created %s index tables' % count)
