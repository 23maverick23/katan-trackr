"""
WSGI config for katan_trackr project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Determine if we are running on Heroku
if 'DYNO' in os.environ:
    SETTINGS = "katan_trackr.settings.prod"
else:
    SETTINGS = "katan_trackr.settings.dev"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS)

application = get_wsgi_application()
