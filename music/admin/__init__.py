"""
:Created: 24 July 2016
:Author: Lucas Connors

"""

from django.contrib import admin

from music.admin.model_admins import ActivityEstimateAdmin, AlbumAdmin
from music.models import ActivityEstimate, Album, Track

admin.site.register(Album, AlbumAdmin)
admin.site.register(Track)
admin.site.register(ActivityEstimate, ActivityEstimateAdmin)
