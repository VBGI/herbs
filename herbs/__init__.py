import os

BASE_URL = os.path.dirname(os.path.abspath(__file__))


def init_herbs():
    if os.path.exists(os.path.join(BASE_URL, 'tmp')):
        pass
    else:
        try:
            os.mkdir(os.path.join(BASE_URL, 'tmp', mode=0o0644))
        except:
            pass

    for f in os.listdir(os.path.join(BASE_URL, 'fonts')):
        if f.endswith('.pkl'):
            try:
                os.remove(os.path.join(BASE_URL,'fonts', f))
            except:
                pass

