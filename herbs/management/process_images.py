# coding: utf-8

import re
import os
import subprocess
import shutil
from PIL import Image
import numpy as np
import shelve


dbcache = shelve.open("herbcache.dat")

# ------------- Common constants ------------
IMAGE_FILE_PATTERN = re.compile(r'^[A-Z]{1,10}\d+(_?\d{1,2})\.([tT][iI][fF]{1,2}$|[jJ][pP][eE]?[gG]$)')

ACRONYM_PATTERN = re.compile(r'^([A-Z]{1,10})\d+.*')

DEFAULT_TMP_FORMAT = '.jpg'


IMAGE_CONVERSION_OPTS = {
                        'fs': {'size': r'', 'format': 'jpg',
                               'extra': ['-strip', '-interlace', 'Plane',
                                         '-sampling-factor', r'4:2:0',
                                         '-quality',
                                         r'90%'],
                               'overwrite': False},
                         'ms': {'size': r'60%', 'format': 'jpg',
                                'extra': ['-strip', '-interlace', 'Plane',
                                          '-sampling-factor', r'4:2:0',
                                          '-quality',
                                          r'90%'],
                                'overwrite': False
                                },
                         'ss': {'size': r'30%', 'format': 'jpg',
                                'extra': ['-strip', '-interlace', 'Plane',
                                          '-sampling-factor', r'4:2:0',
                                          '-quality',
                                          r'90%'],
                                'overwrite': False},
                         'ts': {'size': '150', 'format': 'jpg',
                                'extra': ['-strip', '-interlace', 'Plane',
                                          '-sampling-factor', r'4:2:0',
                                          '-quality',
                                          r'80%'],
                                'overwrite': False}

                        }

SOURCE_IMAGE_PATHS = ['/home/dmitry/workspace/herbs/herbs/management/source',
                      ]
SOURCE_REMOTE_PATTERN = 'source/remote'

OUTPUT_IMAGE_PATH = '/home/dmitry/workspace/herbs/herbs/management/output'
TMP_FOLDER = '/home/dmitry/workspace/herbs/herbs/management/tmp'
# --------------------------------------------



def get_all_image_files(sources=SOURCE_IMAGE_PATHS):
    for dirpath in sources:
        for dir_, dirnames, filenames in os.walk(dirpath):
            for filename in filenames:
                if IMAGE_FILE_PATTERN.match(filename):
                    abspath = os.path.join(dir_, filename)
                    yield abspath


def create_folder_safely(folder ='', source=OUTPUT_IMAGE_PATH):

    if not folder: return

    if os.path.isdir(os.path.join(source, folder)):
        pass
    else:
        os.mkdir(os.path.join(source, folder))


def get_acronym_name(x):
    res = ACRONYM_PATTERN.findall(x)
    return res[-1] if res else ''


def check_image_exists(image_name, overwrite={s: IMAGE_CONVERSION_OPTS[s]['overwrite'] for s in IMAGE_CONVERSION_OPTS}):
    '''Check for existence of the image

    :param image_name:
    :return: true if image_name already exists
    '''
    if image_name in dbcache:
        return dbcache[image_name]

    res = []
    image_name = '.'.join(image_name.split('.')[:-1])
    for subim in IMAGE_CONVERSION_OPTS:
        destination_file = os.path.join(OUTPUT_IMAGE_PATH,
                                    get_acronym_name(image_name),
                                    subim, image_name + '.' +
                                    IMAGE_CONVERSION_OPTS[subim]['format']
                                    )
        res.append(os.path.isfile(destination_file) and not overwrite[subim])

    if all(res):
        dbcache[image_name] = all(res)
    else:
        if image_name in dbcache:
            del dbcache[image_name]

    return all(res)


def easy_process():
    source_images = list(get_all_image_files())

    available_acronyms = set(map(get_acronym_name,
                             map(os.path.basename, source_images)))

    print('Available acronims:', available_acronyms)

    for acro in available_acronyms:
        create_folder_safely(acro)

    print("Acronym folders created successfully...")
    for subf in IMAGE_CONVERSION_OPTS:
        for acro in available_acronyms:
            create_folder_safely(subf,
                                 source=os.path.join(OUTPUT_IMAGE_PATH,
                                                     acro))
    print("Image sub-folders created successfully...")

    for imfile in source_images:
        bname = os.path.basename(imfile)
        tmp_image = os.path.join(TMP_FOLDER, bname)

        if not check_image_exists(bname):
            try:
                shutil.copyfile(imfile, tmp_image, follow_symlinks=False)
            except:
                print("Image %s was dropped." % imfile)
                continue

            imagestack = Image.open(tmp_image)
            if hasattr(imagestack, 'n_frames'):
                if imagestack.n_frames > 1:
                    tfw_array = []
                    tfw_frames = []
                    for k in range(imagestack.n_frames):
                        try:
                            imagestack.seek(k)
                            tfw_array.append(imagestack.width)
                            tfw_frames.append(k)
                        except EOFError:
                            pass
                    imagestack.seek(tfw_frames[np.argmax(tfw_array)])
                else:
                    imagestack.seek(0)
                
            print('Appropriate tiff layer extracted...')
            temp_image_name = bname.split('.')[0]

            imagestack.save(os.path.join(TMP_FOLDER, temp_image_name + DEFAULT_TMP_FORMAT))
            print('Temporary image file is created: ', os.path.join(TMP_FOLDER,
                                                                    temp_image_name))
            cmd_stack = ['convert']
            cmd_stack.append(os.path.join(TMP_FOLDER, temp_image_name + DEFAULT_TMP_FORMAT))

            # check if rotation needed
            rotation = imagestack.width >= imagestack.height
            imagestack.close()
            copyflag = False
            for subim in IMAGE_CONVERSION_OPTS:
                destination_file = os.path.join(OUTPUT_IMAGE_PATH,
                                                get_acronym_name(temp_image_name),
                                                subim, temp_image_name + '.' +
                                                IMAGE_CONVERSION_OPTS[subim]['format']
                                                )
                if not os.path.isfile(destination_file) or IMAGE_CONVERSION_OPTS[subim]['overwrite']\
                        or SOURCE_REMOTE_PATTERN in imfile:
                    cmd_stack_cur = cmd_stack.copy()
                    if rotation:
                        cmd_stack_cur.append('-rotate')
                        cmd_stack_cur.append('270')

                    if IMAGE_CONVERSION_OPTS[subim]['size']:
                        cmd_stack_cur.append('-resize')
                        cmd_stack_cur.append(IMAGE_CONVERSION_OPTS[subim]['size'])

                    if IMAGE_CONVERSION_OPTS[subim]['extra']:
                        cmd_stack_cur.extend(IMAGE_CONVERSION_OPTS[subim]['extra'])

                    cmd_stack_cur.append(destination_file)
                    _p = subprocess.Popen(cmd_stack_cur)
                    _p.wait()
                    copyflag = True
                else:
                    print("The file ", destination_file, "already exists.")

            if copyflag:
                print("Image is created and uploaded (%s)." % temp_image_name)
                try:
                    print("Trying to remove original file...")
                    os.remove(imfile)
                    print("The file is successfully removed (%s)." % os.path.basename(imfile))
                except:
                    print("Couldn't remove the file: ", imfile)
            try:
                os.remove(os.path.join(TMP_FOLDER, temp_image_name + DEFAULT_TMP_FORMAT))
                os.remove(tmp_image)
                print('Temporary files were deleted...')
            except IOError:
                pass
        else:
            print('The file %s alredy exists' % bname)


easy_process()
dbcache.close()
