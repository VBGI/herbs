import os

BASE_URL = os.path.dirname(os.path.abspath(__file__))


def init_herbs():
    if os.path.exists(os.path.join(BASE_URL, 'labeling', 'tmp')):
        pass
    else:
        try:
            os.mkdir(os.path.join(BASE_URL, 'labeling', 'tmp', mode=0o0644))
        except:
            pass

    for f in os.listdir(os.path.join(BASE_URL, 'labeling', 'fonts')):
        if f.endswith('.pkl'):
            try:
                os.remove(os.path.join(BASE_URL, 'labeling', 'fonts', f))
            except:
                pass
