"""
:Created: 25 May 2016
:Author: Lucas Connors

"""

from django import template

register = template.Library()


@register.filter
def notrail_floatformat(num, digits):
    if int(num) == num:
        return int(num)
    return round(num, digits)
