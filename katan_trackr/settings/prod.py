import os
from .base import *
import dj_database_url

DEBUG = bool(os.environ.get('DEBUG_OVERRIDE', False))

DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True)
