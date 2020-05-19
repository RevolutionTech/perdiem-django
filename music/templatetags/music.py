"""
:Created: 25 May 2016
:Author: Lucas Connors

"""

from django import template

register = template.Library()


@register.filter
def trackdurationformat(duration):
    if duration:
        minutes, seconds = divmod(duration.seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
