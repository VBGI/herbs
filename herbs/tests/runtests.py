import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
import django
# from django.conf import settings

# try:
    # Django <= 1.8
#     print 'Trying'
from django.test.simple import DjangoTestSuiteRunner
test_runner = DjangoTestSuiteRunner(verbosity=1)
# except ImportError:
#     # Django >= 1.8
#     django.setup()
#     from django.test.runner import DiscoverRunner
#     test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['herbs'])
 
if failures:
    sys.exit(failures)