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

ACRONYM_PATTERN = re.compile(r'[A-Z]{1,10}')

IMAGE_CONVERSION_OPTS = {
                        'fs': {'format': 'png'},
                        'ms': {'format': 'png', 'size': r'50%'},
                        'ss': {'format': 'png', 'size': r'300x300>'}
                        }

SOURCE_IMAGE_PATHS = ['/home/dmitry/workspace/herbs/herbs/management/source',
                      ]

OUTPUT_IMAGE_PATH = '/home/dmitry/workspace/herbs/herbs/management/output'
TMP_FOLDER = '/home/dmitry/workspace/herbs/herbs/management/tmp'
# --------------------------------------------



def _get_all_image_files(sources=SOURCE_IMAGE_PATHS):
    for dirpath in sources:
        for dir_, dirnames, filenames in os.walk(dirpath):
            for filename in filenames:
                if IMAGE_FILE_PATTERN.match(filename):
                    abspath = os.path.join(dir_, filename)
                    yield abspath


def _get_registered_images(source=OUTPUT_IMAGE_PATH):
    _all_folders = []
    for dir_, dirnames, filenames in os.walk(source):
        for _dir in dirnames:
            if ACRONYM_PATTERN.match(_dir):
                _all_folders.append(os.path.join(dir_, _dir))
    data = pd.DataFrame({'filename' : [],
                         'md5': []})
    for folder in _all_folders:
        _ = os.path.join(folder, 'data.csv')
        if os.path.isfile(_):
            new_data = pd.read_csv(_)
            try:
                data = pd.concat([data, new_data], axis=0, ignore_index=True)
            except:
                print('Illegal file format: ', _)
    return data


def easy_process():
    source_images = list(_get_all_image_files())
    print('Sources:', source_images)
    for imfile in source_images:
        print('Copying the file:', imfile)
        bname = os.path.basename(imfile)
        tmp_image = os.path.join(TMP_FOLDER, bname)
        shutil.copyfile(imfile, tmp_image,
                        follow_symlinks=False)
        print('Copying is finised.')
        print('Getting the file info...')
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
        temp_image_name = bname.split('.')[0] + '.png'
        tiffstack.save(os.path.join(TMP_FOLDER, temp_image_name))
        print('Temporary image file is created: ', os.path.join(TMP_FOLDER,
                                                                temp_image_name))
        cmd_stack = ['convert']
        cmd_stack.append(os.path.join(TMP_FOLDER, temp_image_name))

        # convert to appropriate sizes
        rotation = tiffstack.width >= tiffstack.height
        tiffstack.close()


        # full size image, do anything... just copy an image.
        if os.path.isdir(os.path.join(OUTPUT_IMAGE_PATH, 'fs')):
            pass
        else:
            os.mkdir(os.path.join(OUTPUT_IMAGE_PATH, 'fs'))

        if os.path.isdir(os.path.join(OUTPUT_IMAGE_PATH, 'ms')):
            pass
        else:
            os.mkdir(os.path.join(OUTPUT_IMAGE_PATH, 'ms'))

        if os.path.isdir(os.path.join(OUTPUT_IMAGE_PATH, 'ss')):
            pass
        else:
            os.mkdir(os.path.join(OUTPUT_IMAGE_PATH, 'ss'))


        if rotation:
            cmd_stack_fs = cmd_stack.copy()
            cmd_stack_fs.append('-rotate')
            cmd_stack_fs.append('270')
            cmd_stack_fs.append(os.path.join(OUTPUT_IMAGE_PATH,
                                             'fs', temp_image_name))
            _p = subprocess.Popen(cmd_stack_fs)
            _p.wait()
        else:
            shutil.copyfile(os.path.join(TMP_FOLDER, temp_image_name),
                        os.path.join(OUTPUT_IMAGE_PATH, 'fs',
                        temp_image_name), follow_symlinks=False)
        print('Full size file is copied...')

        # medium size image, resize to 50%


        cmd_stack_ms = cmd_stack.copy()
        cmd_stack_ms.append('-resize')
        cmd_stack_ms.append(IMAGE_CONVERSION_OPTS['ms']['size'])
        if rotation:
            cmd_stack_ms.append('-rotate')
            cmd_stack_ms.append('270')
        cmd_stack_ms.append(os.path.join(OUTPUT_IMAGE_PATH, 'ms', temp_image_name))
        _p = subprocess.Popen(cmd_stack_ms)
        _p.wait()
        print('Medium size file is copied...')

        # small size image
        cmd_stack_ss = cmd_stack.copy()
        cmd_stack_ss.append('-resize')
        cmd_stack_ss.append(IMAGE_CONVERSION_OPTS['ss']['size'])
        if rotation:
            cmd_stack_ss.append('-rotate')
            cmd_stack_ss.append('270')
        cmd_stack_ss.append(os.path.join(OUTPUT_IMAGE_PATH, 'ss', temp_image_name))
        _p = subprocess.Popen(cmd_stack_ss)
        _p.wait()
        print('Medium size file is copied...')
        # delete processed files

easy_process()

