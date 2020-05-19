"""
:Created: 12 March 2016
:Author: Lucas Connors

"""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from markdown_deux.templatetags.markdown_deux_tags import markdown_allowed

from artist.managers import ArtistQuerySet
from campaign.models import Campaign, Investment


class Genre(models.Model):

    name = models.CharField(max_length=40, db_index=True, unique=True)

    def __str__(self):
        return self.name


class Artist(models.Model):

    name = models.CharField(max_length=60, db_index=True)
    genres = models.ManyToManyField(Genre)
    slug = models.SlugField(
        max_length=40,
        unique=True,
        help_text="A short label for an artist (used in URLs)",
    )
    lat = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        db_index=True,
        help_text="Latitude of artist location",
    )
    lon = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        db_index=True,
        help_text="Longitude of artist location",
    )
    location = models.CharField(
        max_length=40,
        help_text="Description of artist location (usually city, state, country format)",
    )

    objects = ArtistQuerySet.as_manager()

    def __str__(self):
        return self.name

    def url(self):
        return reverse("artist", kwargs={"slug": self.slug})

    def social_twitter(self):
        twitter_socials = self.social_set.filter(medium=Social.SOCIAL_TWITTER)
        if twitter_socials.exists():
            return twitter_socials[0]

    def latest_campaign(self):
        campaigns = Campaign.objects.filter(
            project__artist=self, start_datetime__lt=timezone.now()
        ).order_by("-start_datetime")
        if campaigns:
            return campaigns[0]

    def active_campaign(self):
        active_campaigns = (
            Campaign.objects.filter(
                project__artist=self, start_datetime__lt=timezone.now()
            )
            .filter(
                models.Q(end_datetime__isnull=True)
                | models.Q(end_datetime__gte=timezone.now())
            )
            .order_by("-start_datetime")
        )
        if active_campaigns:
            return active_campaigns[0]

    def past_campaigns(self):
        return Campaign.objects.filter(
            project__artist=self, end_datetime__lt=timezone.now()
        ).order_by("-end_datetime")

    def all_campaigns_failed(self):
        # Artists that have an active campaign have not failed
        if self.active_campaign():
            return False

        # Artists that have no past campaigns have not failed
        past_campaigns = self.past_campaigns()
        if not past_campaigns:
            return False

        # Check all of the artist's past campaigns to see if any of them succeeded
        for campaign in past_campaigns:
            if campaign.percentage_funded() == 100:
                return False
        return True

    def has_permission_to_submit_update(self, user):
        return user.is_authenticated and (
            user.is_superuser or self.artistadmin_set.filter(user=user).exists()
        )

    def is_investor(self, user):
        return Investment.objects.filter(
            charge__customer__user=user, campaign__project__artist=self
        ).exists()

    def investors(self):
        investors = {}
        for project in self.project_set.all():
            investors = project.project_investors(investors=investors)
        return investors


class ArtistAdmin(models.Model):

    ROLE_MUSICIAN = "musician"
    ROLE_MANAGER = "manager"
    ROLE_PRODUCER = "producer"
    ROLE_SONGWRITER = "songwriter"
    ROLE_CHOICES = (
        (ROLE_MUSICIAN, "Musician"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_PRODUCER, "Producer"),
        (ROLE_SONGWRITER, "Songwriter"),
    )

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=12,
        help_text="The relationship of this user to the artist",
    )

    def __str__(self):
        return str(self.user)


class Bio(models.Model):

    artist = models.OneToOneField(Artist, on_delete=models.CASCADE)
    bio = models.TextField(help_text="Short biography of artist. " + markdown_allowed())

    def __str__(self):
        return str(self.artist)


class Photo(models.Model):

    artist = models.OneToOneField(Artist, on_delete=models.CASCADE)
    img = models.ImageField(
        upload_to="artist", help_text="Primary profile photo of artist"
    )

    def __str__(self):
        return str(self.artist)


class Playlist(models.Model):

    PLAYLIST_PROVIDER_SPOTIFY = "spotify"
    PLAYLIST_PROVIDER_SOUNDCLOUD = "soundcloud"
    PLAYLIST_PROVIDER_CHOICES = (
        (PLAYLIST_PROVIDER_SPOTIFY, "Spotify"),
        (PLAYLIST_PROVIDER_SOUNDCLOUD, "SoundCloud"),
    )

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    provider = models.CharField(
        choices=PLAYLIST_PROVIDER_CHOICES,
        max_length=10,
        help_text="Provider of the playlist",
    )
    uri = models.TextField(
        help_text="URI that with the provider uniquely identifies a playlist"
    )

    class Meta:
        unique_together = (("provider", "uri"),)

    def __str__(self):
        return self.uri

    def html(self):
        if self.provider == self.PLAYLIST_PROVIDER_SOUNDCLOUD:
            return """
                <iframe width="100%" height="166" scrolling="no" frameborder="no"
                    src="https://w.soundcloud.com/player/?url={url}&color=ff5500"
                >
                </iframe>
            """.format(
                url=self.uri
            )
        elif self.provider == self.PLAYLIST_PROVIDER_SPOTIFY:
            return """
                <iframe src="https://embed.spotify.com/?uri={uri}&theme=white" width="300" height="80" frameborder="0"
                    allowtransparency="true"
                >
                </iframe>
            """.format(
                uri=self.uri
            )


class Social(models.Model):

    SOCIAL_TWITTER = "twitter"
    SOCIAL_CHOICES = (
        ("facebook", "Facebook"),
        (SOCIAL_TWITTER, "Twitter"),
        ("instagram", "Instagram"),
        ("youtube", "YouTube"),
        ("soundcloud", "SoundCloud"),
    )

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    medium = models.CharField(
        choices=SOCIAL_CHOICES, max_length=10, help_text="The type of social network"
    )
    url = models.URLField(
        unique=True, help_text="The URL to the artist's social network page"
    )

    class Meta:
        unique_together = (("artist", "medium"),)

    def __str__(self):
        return "{artist}: {medium}".format(
            artist=str(self.artist), medium=self.get_medium_display()
        )

    def username_twitter(self):
        if self.medium == self.SOCIAL_TWITTER:
            return "@{username}".format(username=self.url.split("/")[-1])
        return self.url


class Update(models.Model):

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    created_datetime = models.DateTimeField(db_index=True, auto_now_add=True)
    title = models.CharField(max_length=75)
    text = models.TextField(
        help_text="The content of the update. " + markdown_allowed()
    )

    def __str__(self):
        return self.title


class UpdateImage(models.Model):

    update = models.ForeignKey(Update, on_delete=models.CASCADE)
    img = models.ImageField(upload_to="/".join(["artist", "updates"]))

    def __str__(self):
        return str(self.update)


class UpdateMediaURL(models.Model):

    MEDIA_YOUTUBE = "youtube"
    MEDIA_CHOICES = ((MEDIA_YOUTUBE, "YouTube"),)

    update = models.ForeignKey(Update, on_delete=models.CASCADE)
    media_type = models.CharField(choices=MEDIA_CHOICES, max_length=8)
    url = models.URLField()

    def __str__(self):
        return str(self.update)

    def clean_youtube_url(self):
        url = escape(self.url)

        # A hack to correct youtu.be links and normal watch links into embed links
        # TODO: Make more robust using regex and getting all query parameters
        if "youtu.be/" in url:
            url = url.replace("youtu.be/", "youtube.com/watch?v=")
        return url

    def thumbnail_html(self):
        if self.media_type == self.MEDIA_YOUTUBE:
            url = self.clean_youtube_url().replace("www.youtube.com", "youtube.com")
            thumbnail_url = "{base}/hqdefault.jpg".format(
                base=url.replace("youtube.com/watch?v=", "img.youtube.com/vi/")
            )
            return '<a href="{url}"><img src="{thumbnail_url}" /></a>'.format(
                url=url, thumbnail_url=thumbnail_url
            )

    def embed_html(self):
        if self.media_type == self.MEDIA_YOUTUBE:
            url = self.clean_youtube_url().replace("/watch?v=", "/embed/")
            return """
                <div class="videowrapper">
                    <iframe width="560" height="315" src="{url}" frameborder="0" allowfullscreen></iframe>
                </div>
            """.format(
                url=url
            )
