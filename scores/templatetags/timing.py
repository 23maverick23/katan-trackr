from __future__ import unicode_literals

from django import template
from django.utils.translation import ungettext

register = template.Library()

@register.filter
def naturaldelta_duration(timedelta):
    """ Format a duration field --> 2h and 30 min or only 45 min """
    if not timedelta:
        return '0m'

    total_seconds = int(timedelta.total_seconds())
    hours = total_seconds // 3600
    minutes = round((total_seconds % 3600) / 60)
    if minutes == 60:
        hours += 1
        minutes = 0
    if hours and minutes:
        # Display both
        return '{}h {}m'.format(hours, minutes)
    elif hours:
        # Display only hours
        return '{}h'.format(hours)
    # Display only minutes
    return '{}m'.format(minutes)

@register.filter
def naturaldelta_days(timedelta):
    """Same as humanizelib.naturaldelta, but express the timedelta in days whenever possible"""
    total_seconds = int(timedelta.total_seconds())
    days = abs(timedelta.days)
    if days < 1:
        if total_seconds == 0:
            return ""
        elif total_seconds < 60:
            return ungettext("%d second", "%d seconds", total_seconds) % total_seconds
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return ungettext("%d minute", "%d minutes", minutes) % minutes
        else:
            hours = total_seconds // 3600
            return ungettext("%d hour", "%d hours", hours) % hours
    else:
        return ungettext("%d day", "%d days", days) % days

@register.filter
def naturaldelta_days_short(timedelta):
    """Same as humanizelib.naturaldelta, but express the timedelta in days whenever possible"""
    total_seconds = int(timedelta.total_seconds())
    days = abs(timedelta.days)
    if days < 1:
        if total_seconds == 0:
            return ""
        elif total_seconds < 60:
            return ungettext("%ds", "%ds", total_seconds) % total_seconds
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return ungettext("%dm", "%dm", minutes) % minutes
        else:
            hours = total_seconds // 3600
            return ungettext("%dh", "%dh", hours) % hours
    else:
        return ungettext("%dd", "%dd", days) % days
