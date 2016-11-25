import os
import sys
import site

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir('/home/vitalii/venv/local/lib/python2.7/site-packages')

# Add the app's directory to the PYTHONPATH
sys.path.append('/var/www/prometrix-api')

os.environ['DJANGO_SETTINGS_MODULE'] = 'prometrix_cloud_security.settings.settings'

# Activate your virtual env
activate_env=os.path.expanduser("/home/vitalii/venv/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

