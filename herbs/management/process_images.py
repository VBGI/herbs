# coding: utf-8

import re
import os
import pandas as pd
import subprocess
import shutil
from PIL import Image
import numpy as np

# ------------- Common constants ------------

IMAGE_FILE_PATTERN = re.compile(r'[A-Z]{1,10}\d+(_?\d{1,2})\.[tT][iI][fF]{1,2}')

ACRONYM_PATTERN = re.compile(r'^([A-Z]{1,10})\d+.*')

IMAGE_CONVERSION_OPTS = {
#                        'fs': {'size': '', 'format': 'png', 'extra': []},
                        'fs': {'size': r'', 'format': 'jpg',
                               'extra': ['-strip', '-interlace', 'Plane',
                                         '-sampling-factor', r'4:2:0',
                                         '-quality',
                                         r'90%']}
                        # 'ss': {'size': '300x300^', 'format': 'jpg',
                        #        'extra': ['-strip', '-interlace', 'Plane',
                        #                  '-sampling-factor', r'4:2:0',
                        #                  '-quality',
                        #                  r'90%']}
                        }

SOURCE_IMAGE_PATHS = ['/home/dmitry/workspace/herbs/herbs/management/source',
                      ]

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


# def get_images(source=OUTPUT_IMAGE_PATH):
#     _all_folders = []
#     for dir_, dirnames, filenames in os.walk(source):
#         for _dir in dirnames:
#             if ACRONYM_PATTERN.match(_dir):
#                 _all_folders.append(os.path.join(dir_, _dir))
#     data = pd.DataFrame({'filename' : [],
#                          'md5': []})
#     for folder in _all_folders:
#         _ = os.path.join(folder, 'data.csv')
#         if os.path.isfile(_):
#             new_data = pd.read_csv(_)
#             try:
#                 data = pd.concat([data, new_data], axis=0, ignore_index=True)
#             except:
#                 print('Illegal file format: ', _)
#     return data


def create_folder_safely(folder ='', source=OUTPUT_IMAGE_PATH):

    if not folder: return

    if os.path.isdir(os.path.join(source, folder)):
        pass
    else:
        os.mkdir(os.path.join(source, folder))


def get_acronym_name(x):
    res = ACRONYM_PATTERN.findall(x)
    return res[-1] if res else ''


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
        print('Copying the file:', imfile)
        bname = os.path.basename(imfile)
        tmp_image = os.path.join(TMP_FOLDER, bname)
        shutil.copyfile(imfile, tmp_image,
                        follow_symlinks=False)
        tiffstack = Image.open(tmp_image)
        if tiffstack.n_frames > 1:
            tfw_array = []
            tfw_frames = []
            for k in range(tiffstack.n_frames):
                try:
                    tiffstack.seek(k)
                    tfw_array.append(tiffstack.width)
                    tfw_frames.append(k)
                except EOFError:
                    pass
            tiffstack.seek(tfw_frames[np.argmax(tfw_array)])
        else:
            tiffstack.seek(0)
        print('Appropriate tiff layer extracted...')
        temp_image_name = bname.split('.')[0]
        tiffstack.save(os.path.join(TMP_FOLDER, temp_image_name + '.png'))
        print('Temporary image file is created: ', os.path.join(TMP_FOLDER,
                                                                temp_image_name))
        cmd_stack = ['convert']
        cmd_stack.append(os.path.join(TMP_FOLDER, temp_image_name + '.png'))

        # check if rotation needed
        rotation = tiffstack.width >= tiffstack.height
        tiffstack.close()

        for subim in IMAGE_CONVERSION_OPTS:
            cmd_stack_cur = cmd_stack.copy()
            if rotation:
                cmd_stack_cur.append('-rotate')
                cmd_stack_cur.append('270')

            if IMAGE_CONVERSION_OPTS[subim]['size']:
                cmd_stack_cur.append('-resize')
                cmd_stack_cur.append(IMAGE_CONVERSION_OPTS[subim]['size'])

            if IMAGE_CONVERSION_OPTS[subim]['extra']:
                cmd_stack_cur.extend(IMAGE_CONVERSION_OPTS[subim]['extra'])

            cmd_stack_cur.append(os.path.join(OUTPUT_IMAGE_PATH,
                                              get_acronym_name(temp_image_name),
                                              subim, temp_image_name + '.' +
                                              IMAGE_CONVERSION_OPTS[subim]['format']
                                              ))
            _p = subprocess.Popen(cmd_stack_cur)
            _p.wait()
            print('Generating ', subim, 'image for', temp_image_name)

      # delete processed image
        try:
            os.remove(os.path.join(TMP_FOLDER, temp_image_name + '.png'))
            os.remove(tmp_image)
            print('Temporary files were removed...')
        except IOError:
            pass



easy_process()

