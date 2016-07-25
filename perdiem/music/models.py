"""
:Created: 24 July 2016
:Author: Lucas Connors

"""

from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models

from campaign.models import Project


class Album(models.Model):

    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=40, db_index=True, help_text='A short label for an album (used in URLs)')

    def __unicode__(self):
        return self.name

    def validate_unique(self):
        if Album.objects.exclude(id=self.id).filter(project__artist=self.project.artist, slug=self.slug).exists():
            raise ValidationError("Slug must be unique per artist")

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(Album, self).save(*args, **kwargs)


class Artwork(models.Model):

    album = models.OneToOneField(Album)
    img = models.ImageField(upload_to='artist/album')

    class Meta:
        verbose_name_plural = 'Artwork'

    def __unicode__(self):
        return unicode(self.album)


class MarketplaceURL(models.Model):

    MARKETPLACE_CHOICES = (
        ('spotify', 'Spotify',),
        ('itunes', 'iTunes',),
        ('apple', 'Apple Music',),
        ('google', 'Google Play',),
        ('amazon', 'Amazon',),
        ('tidal', 'Tidal',),
        ('youtube', 'YouTube',),
    )

    album = models.ForeignKey(Album)
    medium = models.CharField(choices=MARKETPLACE_CHOICES, max_length=10, help_text='The type of marketplace')
    url = models.URLField(unique=True, help_text='The URL to the album\'s page')

    class Meta:
        unique_together = (('album', 'medium',),)

    def __unicode__(self):
        return u'{album}: {medium}'.format(
            album=unicode(self.album),
            medium=self.get_medium_display()
        )
