import hashlib
import urllib
from django import template

from libgravatar import Gravatar


register = template.Library()

# return only the URL of the gravatar
# TEMPLATE USE:  {{ email|gravatar_url:150 }}
@register.filter
def gravatar_url(email, size=150):
    default = "https://picsum.photos/{}.jpg".format(size)
    g = Gravatar(email)
    gravatar_url = g.get_image(size=size, default=default, filetype_extension=True)
    return gravatar_url
