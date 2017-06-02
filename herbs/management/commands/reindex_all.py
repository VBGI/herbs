from django.core.management.base import BaseCommand

try:
    from herbs.models import SpeciesSynonym, Species
except ImportError:
    from bgi.herbs.models import SpeciesSynonym, Species


class Command(BaseCommand):
    args = ''
    help = 'Rebuild index of species synonym tables'

    def handle(self, *args, **options):
        SpeciesSynonym.objects.all().delete()

        arrays = [[]]
        array_names = [[]]
        for sp in Species.objects.all().exclude(synonym__isnull=True).exclude(
                                                status='D').iterator():
            cur = sp.pk
            syn = sp.synonym.pk
            cur_ind = [ind for ind, el in enumerate(arrays) if cur in el] or None
            syn_ind = [ind for ind, el in enumerate(arrays) if syn in el] or None
            if cur_ind and syn_ind:
                pass
            elif cur_ind and not syn_ind:
                arrays[cur_ind[0]].append(syn)
                array_names[cur_ind[0]].append(sp.get_full_name())
            elif not cur_ind and syn_ind:
                arrays[syn_ind[0]].append(cur)
                array_names[syn_ind[0]].append(sp.synonym.get_full_name())
            else:
                arrays.append([cur, syn])
                array_names.append([sp.synonym.get_full_name(),
                                    sp.get_full_name()])
        count = 0
        for arr, arrn in zip(arrays, array_names):
            SpeciesSynonym.objects.get_or_create(rebuild_scheduled=False,
                                                 json_content=','+','.join(map(str, arr)) + ',',
                                                 string_content=','.join(arrn)
                                                 )
            count += 1
        self.stdout.write('Successfully created %s index tables' % count)
